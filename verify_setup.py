#!/usr/bin/env python3
"""
Quick verification script to check if Loglify is set up correctly.
"""
import sys
import os

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking imports...")
    try:
        import fastapi
        import uvicorn
        import telegram
        import sqlalchemy
        import openai
        import click
        import httpx
        import pydantic
        print("✅ All core dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration can be loaded"""
    print("\n🔍 Checking configuration...")
    try:
        from config import settings
        print(f"✅ Configuration loaded")
        print(f"   Database URL: {settings.database_url[:50]}...")
        print(f"   Telegram Token: {'Set' if settings.telegram_token != 'your_telegram_bot_token_here' else 'Not set'}")
        print(f"   OpenAI API Key: {'Set' if settings.openai_api_key != 'your_openai_api_key_here' else 'Not set'}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_database():
    """Check if database can be initialized"""
    print("\n🔍 Checking database...")
    try:
        from database import init_db, engine
        print("✅ Database engine created")
        # Don't actually create tables in verification
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    print("🚀 Loglify Setup Verification\n")
    
    all_ok = True
    all_ok &= check_imports()
    all_ok &= check_config()
    all_ok &= check_database()
    
    print("\n" + "="*50)
    if all_ok:
        print("✅ All checks passed! Loglify is ready to use.")
        print("\nNext steps:")
        print("1. Edit .env and add your API keys")
        print("2. Run: python3 run.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

