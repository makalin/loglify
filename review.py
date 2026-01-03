import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db, LogEntry
from llm_parser import LLMParser
from config import settings
import httpx
from telegram import Bot


class DailyReview:
    def __init__(self):
        self.parser = LLMParser()
        self.bot = None
        if settings.telegram_token:
            self.bot = Bot(token=settings.telegram_token)
    
    async def generate_review(self, db: Session) -> str:
        """Generate daily review using AI"""
        # Get today's logs
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.utcnow()
        
        logs = db.query(LogEntry).filter(
            LogEntry.timestamp >= today_start,
            LogEntry.timestamp <= today_end
        ).order_by(LogEntry.timestamp).all()
        
        if not logs:
            return "📝 No activities logged today."
        
        # Format logs for AI
        logs_summary = []
        total_duration = 0
        
        for log in logs:
            entry = {
                "time": log.timestamp.strftime("%H:%M"),
                "action": log.action,
                "project": log.project,
                "duration": log.duration,
                "tags": log.tags
            }
            logs_summary.append(entry)
            if log.duration:
                total_duration += log.duration
        
        # Create prompt for AI review
        logs_text = "\n".join([
            f"{log['time']}: {log['action']}"
            + (f" ({log['duration']} min)" if log.get('duration') else "")
            + (f" - {log['project']}" if log.get('project') else "")
            for log in logs_summary
        ])
        
        prompt = f"""Analyze the following daily activity log and provide:
1. A brief summary of the day
2. Key highlights or achievements
3. Patterns or insights
4. Suggestions for tomorrow

Today's Activities:
{logs_text}

Total logged time: {round(total_duration / 60, 1)} hours

Provide a friendly, concise review (2-3 paragraphs)."""
        
        review = self.parser.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides daily life log reviews. Be encouraging and insightful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return review.choices[0].message.content.strip()
    
    async def send_review(self, review_text: str):
        """Send review to Telegram"""
        if not self.bot or not settings.telegram_chat_id:
            print("Telegram bot or chat ID not configured. Review:")
            print(review_text)
            return
        
        try:
            await self.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=f"📊 Daily Review - {datetime.utcnow().strftime('%Y-%m-%d')}\n\n{review_text}"
            )
            print("✅ Daily review sent to Telegram")
        except Exception as e:
            print(f"Error sending review: {str(e)}")
    
    async def run(self):
        """Run daily review"""
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            review_text = await self.generate_review(db)
            await self.send_review(review_text)
        finally:
            db.close()


async def main():
    review = DailyReview()
    await review.run()


if __name__ == "__main__":
    asyncio.run(main())

