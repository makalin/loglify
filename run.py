#!/usr/bin/env python3
"""
Main entry point for running Loglify.
Starts both the FastAPI server and Telegram bot.
"""
import asyncio
import threading
import uvicorn
from telegram_bot import TelegramBot
from config import settings


def run_api():
    """Run FastAPI server"""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


def run_bot():
    """Run Telegram bot"""
    bot = TelegramBot()
    bot.run()


if __name__ == "__main__":
    print("🚀 Starting Loglify...")
    print(f"   API: http://{settings.host}:{settings.port}")
    print(f"   Telegram Bot: {'Enabled' if settings.telegram_token else 'Disabled'}")
    
    # Start API in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Wait a bit for API to start
    import time
    time.sleep(2)
    
    # Run bot in main thread (blocking)
    if settings.telegram_token:
        run_bot()
    else:
        print("⚠️  Telegram bot disabled. API is running.")
        print("   Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")

