#!/usr/bin/env python3
"""
OpenClaw AI Agent - Telegram Bot for Web Crawling and Video Processing
Version 1.0
"""

import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
import requests
from bs4 import BeautifulSoup
import edge_tts
import moviepy.editor as mp
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/openclaw.log", rotation="10 MB", level="INFO")

# Initialize OpenAI client with OpenRouter
openai_client = openai.OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

class OpenClawAgent:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-pro")
        
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
        logger.info("OpenClaw Agent initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = """
🤖 OpenClaw AI Agent မှကြိုဆိုပါတယ်!

ကျွန်တော်သည် အောက်ပါလုပ်ငန်းများကို လုပ်ဆောင်ပေးနိုင်ပါသည်:
• Website လင့်ခ်များကို crawl လုပ်ခြင်း
• YouTube ဗီဒီယိုများကို အကျဉ်းချုပ်ပေးခြင်း
• မြန်မာဘာသာဖြင့် recap/script ရေးပေးခြင်း

အသုံးပြုရန်:
• Website လင့်ခ်ကို ပေးပို့ပါ
• YouTube လင့်ခ်ကို ပေးပို့ပါ
• /help ကို အသုံးပြုပြီး အကူအညီရယူပါ
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_text = """
📋 OpenClaw Agent အကူအညီ:

ကိန်းများ:
/start - စတင်ရန်
/help - အကူအညီရယူရန်

အသုံးပြုနည်း:
1. Website လင့်ခ်ကို ပေးပို့ပါ → အကျဉ်းချုပ်ရရှိပါမည်
2. YouTube လင့်ခ်ကို ပေးပို့ပါ → အကျဉ်းချုပ်ရရှိပါမည်

ဥပမာ:
https://example.com
https://youtube.com/watch?v=example
        """
        await update.message.reply_text(help_text)
    
    async def process_url(self, url: str) -> str:
        """Process URL (website or YouTube) and generate Myanmar recap"""
        try:
            # Check if it's a YouTube URL
            if "youtube.com" in url or "youtu.be" in url:
                return await self.process_youtube_url(url)
            else:
                return await self.process_website_url(url)
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return f"❌ အမှားဖြစ်ပါသည်: {str(e)}"
    
    async def process_website_url(self, url: str) -> str:
        """Crawl website and generate recap"""
        try:
            # Use requests to fetch the webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length
            content = text[:2000]
                
            # Generate recap using OpenRouter
            prompt = f"""
အောက်ပါ website အကြောင်းအရာကို မြန်မာဘာသာဖြင့် အကျဉ်းချုပ်ပေးပါ:

URL: {url}

အကြောင်းအရာ:
{content}

အကျဉ်းချုပ်တွင် အဓိကအချက်များကို မြန်မာဘာသာဖြင့် ရေးပေးပါ။
            """
                
            response = openai_client.chat.completions.create(
                model=self.openrouter_model,
                messages=[
                    {"role": "system", "content": "သင်သည် မြန်မာဘာသာဖြင့် အကျဉ်းချုပ်ရေးသားရန် ကျွမ်းကျင်သော AI ဖြစ်သည်။"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
                
            recap = response.choices[0].message.content
                
            return f"""
🌐 Website အကျဉ်းချုပ်

🔗 URL: {url}

📝 အကျဉ်းချုပ်:
{recap}
            """
                
        except Exception as e:
            logger.error(f"Error crawling website {url}: {str(e)}")
            return f"❌ Website ကို crawl လုပ်နိုင်ျခြင်း: {str(e)}"
    
    async def process_youtube_url(self, url: str) -> str:
        """Process YouTube URL and generate recap"""
        try:
            # For now, return a placeholder since YouTube processing requires additional setup
            prompt = f"""
YouTube ဗီဒီယို URL: {url}

ဤ YouTube ဗီဒီယိုအား မြန်မာဘာသာဖြင့် အကျဉ်းချုပ်ပေးရန် လိုအပ်ပါသည်။
ဗီဒီယို၏ အကြောင်းအရာကို ခန့်မှန်းပြီး မြန်မာဘာသာဖြင့် အကျဉ်းချုပ်တစ်ခု ရေးပေးပါ။
            """
            
            response = openai_client.chat.completions.create(
                model=self.openrouter_model,
                messages=[
                    {"role": "system", "content": "သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုအကျဉ်းချုပ်ရေးသားရန် ကျွမ်းကျင်သော AI ဖြစ်သည်။"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            
            recap = response.choices[0].message.content
            
            return f"""
🎥 YouTube ဗီဒီယို အကျဉ်းချုပ်

🔗 URL: {url}

📝 အကျဉ်းချုပ်:
{recap}

မှတ်ချက်: ဤအကျဉ်းချုပ်သည် URL အားဖြင့် ခန့်မှန်းထားခြင်း ဖြစ်ပါသည်။
            """
            
        except Exception as e:
            logger.error(f"Error processing YouTube URL {url}: {str(e)}")
            return f"❌ YouTube ဗီဒီယိုကို ဆောင်ရွက်နိုင်ခြင်း: {str(e)}"
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages"""
        message_text = update.message.text
        
        # Check if it's a URL
        if message_text.startswith(('http://', 'https://')):
            await update.message.reply_text("🔄 ဆောင်ရွက်နေသည်...")
            
            # Process the URL
            result = await self.process_url(message_text)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text(
                "❌ ကျေးဇူးပြုပြီး website သို့မဟုတ် YouTube URL ကိုသာ ပေးပို့ပါ။\n"
                "အကူအညီအတွက် /help ကိုအသုံးပြုပါ။"
            )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and hasattr(update, 'message'):
            await update.message.reply_text("❌ အမှားတစ်ခုဖြစ်ပါသည်။ ထပ်စမ်းကြည့်ပါ။")
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.telegram_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        logger.info("Starting OpenClaw Agent bot...")
        application.run_polling()

def main():
    """Main function"""
    try:
        agent = OpenClawAgent()
        agent.run()
    except Exception as e:
        logger.error(f"Failed to start agent: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
