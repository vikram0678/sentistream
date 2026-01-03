import os
import asyncio
import random
import uuid
import logging
from datetime import datetime
import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import SocialMediaPost

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataIngester")

# --- DATABASE SETUP ---
DATABASE_URL = "postgresql://sentiment_user:your_secure_password@postgres:5432/sentiment_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class DataIngester:
    def __init__(self, redis_client, stream_name: str, posts_per_minute: int = 60):
        self.redis = redis_client
        self.stream_name = stream_name
        self.sleep_interval = 60.0 / posts_per_minute
        self.platforms = ["twitter", "reddit", "mastodon", "facebook"]
        self.products = ["iPhone 16", "Tesla Model 3", "ChatGPT", "Netflix", "Amazon Prime", "PlayStation 5"]
        self.authors = ["tech_enthusiast", "daily_driver", "critic_pro", "happy_buyer_22", "early_adopter"]
        self.templates = {
            "positive": ["I absolutely love {product}!", "This {product} is amazing!", "Highly recommend the new {product}."],
            "neutral": ["Just tried {product}.", "Received {product} today.", "Using {product} for the first time."],
            "negative": ["Very disappointed with {product}.", "Terrible experience with {product}.", "I hate the new {product} update."]
        }

    def generate_post(self) -> dict:
        rand = random.random()
        sentiment = "positive" if rand < 0.4 else "neutral" if rand < 0.7 else "negative"
        product = random.choice(self.products)
        return {
            'post_id': f'post_{uuid.uuid4().int}',
            'source': random.choice(self.platforms),
            'content': random.choice(self.templates[sentiment]).format(product=product),
            'author': random.choice(self.authors),
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

    async def save_to_db(self, post_data: dict):
        """Saves the post to Postgres so the Worker can find it"""
        db = SessionLocal()
        try:
            # SAFETY FIX: Ensure created_at is a valid datetime object
            raw_date = post_data.get('created_at')
            if raw_date:
                clean_date = raw_date.replace('Z', '')
                created_dt_obj = datetime.fromisoformat(clean_date)
            else:
                created_dt_obj = datetime.utcnow()

            new_post = SocialMediaPost(
                post_id=post_data['post_id'],
                source=post_data['source'],
                content=post_data['content'],
                author=post_data['author'],
                created_at=created_dt_obj
            )
            db.add(new_post)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"DB Error: {e}")
            return False
        finally:
            db.close()

    async def start(self):
        logger.info("🚀 Ingester started. Saving to DB and publishing to Redis...")
        while True:
            post = self.generate_post()
            
            # 1. Save to Postgres first
            db_success = await self.save_to_db(post)
            
            if db_success:
                # 2. Publish to Redis Stream
                try:
                    await self.redis.xadd(self.stream_name, post, id='*')
                    logger.info(f"✅ Success: {post['post_id']}")
                except Exception as e:
                    logger.error(f"Redis Error: {e}")

            await asyncio.sleep(self.sleep_interval)

async def main():
    client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), decode_responses=True)
    ingester = DataIngester(client, os.getenv("REDIS_STREAM_NAME", "social_posts_stream"))
    await ingester.start()

if __name__ == "__main__":
    asyncio.run(main())