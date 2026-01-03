import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models import SocialMediaPost, SentimentAnalysis, SentimentAlert

logger = logging.getLogger("AlertService")

class AlertService:
    def __init__(self, db_session_maker):
        self.SessionLocal = db_session_maker
        # Load configs from Env
        self.threshold = float(os.getenv("ALERT_NEGATIVE_RATIO_THRESHOLD", 2.0))
        self.window = int(os.getenv("ALERT_WINDOW_MINUTES", 5))
        self.min_posts = int(os.getenv("ALERT_MIN_POSTS", 10))

    async def check_thresholds(self) -> Optional[dict]:
        with self.SessionLocal() as db:
            now = datetime.utcnow()
            start_time = now - timedelta(minutes=self.window)

            # 1. Fetch metrics in the window
            results = db.query(SentimentAnalysis.sentiment_label).join(
                SocialMediaPost, SocialMediaPost.post_id == SentimentAnalysis.post_id
            ).filter(SocialMediaPost.created_at >= start_time).all()

            if len(results) < self.min_posts:
                return None # Not enough data

            counts = {"positive": 0, "negative": 0, "neutral": 0}
            for res in results:
                label = res[0].lower()
                if "pos" in label: counts["positive"] += 1
                elif "neg" in label: counts["negative"] += 1
                else: counts["neutral"] += 1

            total = len(results)
            # Avoid division by zero
            pos_count = counts["positive"] if counts["positive"] > 0 else 0.1
            ratio = counts["negative"] / pos_count

            # 2. Trigger Logic
            if ratio > self.threshold:
                return {
                    "alert_triggered": True,
                    "alert_type": "high_negative_ratio",
                    "threshold": self.threshold,
                    "actual_ratio": round(ratio, 2),
                    "window_minutes": self.window,
                    "metrics": {
                        "positive_count": counts["positive"],
                        "negative_count": counts["negative"],
                        "neutral_count": counts["neutral"],
                        "total_count": total
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None

    async def save_alert(self, alert_data: dict) -> int:
        with self.SessionLocal() as db:
            try:
                now = datetime.utcnow()
                new_alert = SentimentAlert(
                    alert_type=alert_data["alert_type"],
                    threshold_value=float(alert_data["threshold"]),
                    actual_value=float(alert_data["actual_ratio"]),
                    window_minutes=int(alert_data["window_minutes"]),
                    window_start=now - timedelta(minutes=alert_data["window_minutes"]),
                    window_end=now,
                    post_count=int(alert_data["metrics"]["total_count"]),
                    triggered_at=now,
                    details=alert_data["metrics"] # This goes into your JSONB column
                )
                db.add(new_alert)
                db.commit()
                db.refresh(new_alert)
                logger.info(f"✅ Alert saved to database. ID: {new_alert.id}")
                return new_alert.id
            except Exception as e:
                db.rollback()
                logger.error(f"❌ Failed to save alert: {e}")
                raise e

    async def run_monitoring_loop(self):
        logger.info("📢 Alert Monitoring Loop Started")
        while True:
            try:
                alert_data = await self.check_thresholds()
                if alert_data:
                    alert_id = await self.save_alert(alert_data)
                    logger.warning(f"🚨 ALERT TRIGGERED! ID: {alert_id} | Ratio: {alert_data['actual_ratio']}")
            except Exception as e:
                logger.error(f"Alert Loop Error: {e}")
            
            await asyncio.sleep(60) # Check every minute