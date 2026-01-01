import os
import asyncio
import random
import uuid
import logging
from datetime import datetime
import redis.asyncio as redis
from redis.exceptions import RedisError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataIngester")

class DataIngester:
    """
    Publishes simulated social media posts to Redis Stream
    """
    def __init__(self, redis_client, stream_name: str, posts_per_minute: int = 60):
        self.redis = redis_client
        self.stream_name = stream_name
        self.posts_per_minute = posts_per_minute
        self.sleep_interval = 60.0 / posts_per_minute

        # Realistic post generation assets
        self.platforms = ["twitter", "reddit", "mastodon", "facebook"]
        self.products = ["iPhone 16", "Tesla Model 3", "ChatGPT", "Netflix", "Amazon Prime", "PlayStation 5"]
        self.authors = ["tech_enthusiast", "daily_driver", "critic_pro", "happy_buyer_22", "early_adopter"]
        
        self.templates = {
            "positive": [
                "I absolutely love {product}!", "This {product} is amazing!", 
                "{product} exceeded my expectations!", "Highly recommend the new {product}."
            ],
            "neutral": [
                "Just tried {product}.", "Received {product} today.", 
                "Using {product} for the first time.", "Fact: {product} was released recently."
            ],
            "negative": [
                "Very disappointed with {product}.", "Terrible experience with {product}.", 
                "Would not recommend {product}.", "I hate the new {product} update."
            ]
        }

    def generate_post(self) -> dict:
        """Generates a realistic post with ~40% pos, 30% neu, 30% neg sentiment"""
        # Determine sentiment based on probability
        rand = random.random()
        if rand < 0.4:
            sentiment = "positive"
        elif rand < 0.7:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        product = random.choice(self.products)
        content = random.choice(self.templates[sentiment]).format(product=product)
        
        return {
            'post_id': f'post_{uuid.uuid4().int}',
            'source': random.choice(self.platforms),
            'content': content,
            'author': random.choice(self.authors),
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

    async def publish_post(self, post_data: dict) -> bool:
        """Publishes to Redis Stream using XADD"""
        try:
            # XADD key ID field string [field string ...]
            # '*' lets Redis generate the auto-incrementing message ID
            await self.redis.xadd(self.stream_name, post_data, id='*')
            return True
        except RedisError as e:
            logger.error(f"Redis connection failure: {e}")
            return False

    async def start(self, duration_seconds: int = None):
        """Main loop for generating and publishing posts"""
        logger.info(f"Starting ingester at {self.posts_per_minute} posts/min...")
        start_time = datetime.utcnow()
        
        try:
            while True:
                # Check duration constraint
                if duration_seconds:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed >= duration_seconds:
                        logger.info("Target duration reached. Stopping ingester.")
                        break

                # Process post
                post = self.generate_post()
                success = await self.publish_post(post)
                
                if success:
                    logger.info(f"Published: {post['post_id']} - {post['content'][:30]}...")
                
                # Rate limiting sleep
                await asyncio.sleep(self.sleep_interval)
                
        except asyncio.CancelledError:
            logger.info("Ingester service cancelled.")
        except KeyboardInterrupt:
            logger.info("Ingester stopped by user.")

async def main():
    # Configuration from environment variables
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    stream_name = os.getenv("REDIS_STREAM_NAME", "social_posts_stream")
    ppm = int(os.getenv("POSTS_PER_MINUTE", 60))

    # Initialize async Redis client
    client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    
    ingester = DataIngester(client, stream_name, ppm)
    await ingester.start()

if __name__ == "__main__":
    asyncio.run(main())