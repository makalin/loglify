"""
Scheduler for running periodic tasks (daily review, GitHub sync, etc.)
"""
import schedule
import time
import asyncio
from datetime import datetime
from config import settings
from review import DailyReview
from aggregators.github import GitHubAggregator


def run_daily_review():
    """Run daily review"""
    print(f"[{datetime.now()}] Running daily review...")
    review = DailyReview()
    asyncio.run(review.run())


def run_github_sync():
    """Run GitHub sync"""
    print(f"[{datetime.now()}] Running GitHub sync...")
    aggregator = GitHubAggregator()
    asyncio.run(aggregator.sync(days=1))


def start_scheduler():
    """Start the scheduler"""
    if settings.enable_daily_review:
        # Schedule daily review
        review_time = settings.review_time
        schedule.every().day.at(review_time).do(run_daily_review)
        print(f"📅 Daily review scheduled for {review_time}")
    
    # Schedule GitHub sync (every 6 hours)
    if settings.github_token:
        schedule.every(6).hours.do(run_github_sync)
        print("🔄 GitHub sync scheduled (every 6 hours)")
    
    print("⏰ Scheduler started")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    start_scheduler()

