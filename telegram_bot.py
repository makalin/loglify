import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from database import get_db, LogEntry
from llm_parser import LLMParser
from models import LogEntryCreate
from config import settings
from datetime import datetime
import httpx


class TelegramBot:
    def __init__(self):
        self.parser = LLMParser()
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Welcome to Loglify!\n\n"
            "Just send me messages about what you're doing, and I'll log them.\n\n"
            "Examples:\n"
            "• 'I just spent 2 hours fixing a bug in the backend'\n"
            "• 'Meeting with Client X regarding the new design'\n"
            "• 'Ate a chicken salad and a soda'\n\n"
            "Commands:\n"
            "/stats - Get your statistics\n"
            "/query <question> - Ask questions about your logs"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"http://localhost:{settings.port}/api/logs/stats?days=7"
                )
                stats = response.json()
                
                message = f"📊 Your Stats (Last 7 Days)\n\n"
                message += f"Total Logs: {stats['total_logs']}\n"
                message += f"Total Time: {stats['total_duration_hours']} hours\n\n"
                message += "By Source:\n"
                for source, count in stats['logs_by_source'].items():
                    message += f"  • {source}: {count}\n"
                message += "\nTop Actions:\n"
                for action, count in list(stats['top_actions'].items())[:5]:
                    message += f"  • {action}: {count}\n"
                
                await update.message.reply_text(message)
            except Exception as e:
                await update.message.reply_text(f"Error fetching stats: {str(e)}")
    
    async def query_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /query command"""
        query_text = " ".join(context.args) if context.args else None
        
        if not query_text:
            await update.message.reply_text("Usage: /query <your question>")
            return
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"http://localhost:{settings.port}/api/query",
                    json={"query": query_text}
                )
                result = response.json()
                await update.message.reply_text(f"💡 {result['answer']}")
            except Exception as e:
                await update.message.reply_text(f"Error processing query: {str(e)}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages - parse and log them"""
        text = update.message.text
        
        if not text:
            return
        
        # Parse the message using LLM
        parsed = self.parser.parse_natural_language(text)
        
        # Create log entry
        log_entry = LogEntryCreate(
            source="telegram",
            raw_text=text,
            action=parsed["action"],
            project=parsed.get("project"),
            duration=parsed.get("duration"),
            tags=parsed.get("tags", [])
        )
        
        # Send to API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"http://localhost:{settings.port}/api/logs",
                    json=log_entry.dict()
                )
                
                if response.status_code == 200:
                    entry = response.json()
                    confirmation = f"✅ Logged: {entry['action']}"
                    if entry.get('duration'):
                        confirmation += f" ({entry['duration']} min)"
                    if entry.get('project'):
                        confirmation += f" - {entry['project']}"
                    await update.message.reply_text(confirmation)
                else:
                    await update.message.reply_text("❌ Error logging entry")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
    
    def run(self):
        """Start the Telegram bot"""
        if not settings.telegram_token:
            print("Warning: TELEGRAM_TOKEN not set. Telegram bot will not start.")
            return
        
        self.application = Application.builder().token(settings.telegram_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("query", self.query_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print("🤖 Telegram bot starting...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()

