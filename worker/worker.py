import os
import asyncio
import logging
from datetime import datetime
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.sentiment_analyzer import SentimentAnalyzer
from models import SocialMediaPost, SentimentAnalysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Worker")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# FIX 1: Remove 'async' from this function
def save_post_and_analysis(db_session, post_data, sentiment_result, emotion_result):
    try:
        existing_post = db_session.query(SocialMediaPost).filter_by(post_id=post_data['post_id']).first()
        
        if existing_post:
            existing_post.ingested_at = datetime.utcnow()
            post_record = existing_post
        else:
            # FIX: Ensure created_at is NEVER None
            created_at = post_data.get('created_at')
            if created_at is None:
                created_at = datetime.utcnow()

            post_record = SocialMediaPost(
                post_id=post_data['post_id'],
                source=post_data.get('source', 'unknown'),
                content=post_data['content'],
                author=post_data.get('author', 'anonymous'),
                created_at=created_at # Now it's guaranteed to have a value!
            )
            db_session.add(post_record)
        
        db_session.flush()

        analysis_record = SentimentAnalysis(
            post_id=post_data['post_id'],
            model_name=sentiment_result['model_name'],
            sentiment_label=sentiment_result['sentiment_label'],
            confidence_score=sentiment_result['confidence_score'],
            emotion=emotion_result['emotion']
        )
        db_session.add(analysis_record)
        db_session.commit()
        return post_record.id, analysis_record.id
    except Exception as e:
        db_session.rollback()
        logger.error(f"Database Save Error: {e}")
        raise e

class SentimentWorker:
    def __init__(self, redis_client, db_session_maker, stream_name, consumer_group):
        self.redis = redis_client
        self.SessionLocal = db_session_maker
        self.stream_name = stream_name
        self.group_name = consumer_group
        self.consumer_name = f"worker_{os.getpid()}"
        self.analyzer = SentimentAnalyzer(model_type='local')

    async def setup(self):
        try:
            await self.redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except Exception:
            logger.info("Consumer group ready.")

# Inside worker/worker.py

    async def process_message(self, message_id, message_data):
        # This is where we add the "with" block to create a private DB session
        # for THIS specific message. This prevents the "Different Loop" error.
        with self.SessionLocal() as db: 
            try:
                # 1. Run your AI analysis
                sentiment = await self.analyzer.analyze_sentiment(message_data['content'])
                emotion = await self.analyzer.analyze_emotion(message_data['content'])

                # 2. Use the 'db' session we just created to save the data
                # We use the executor to keep the database work from blocking the loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, 
                    self.save_to_db,  # This is a helper function we define below
                    db, 
                    message_data, 
                    sentiment, 
                    emotion
                )

                # 3. Tell Redis we are done
                await self.redis.xack(self.stream_name, self.group_name, message_id)
                logger.info(f"✅ Processed: {message_data.get('post_id')}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {message_id}: {e}")
                db.rollback() # Rollback if something fails
    # --- ADD IT HERE ---
    def save_to_db(self, db, data, sentiment, emotion):
        """Safe database save that handles different AI return formats"""
        from models import SocialMediaPost, SentimentAnalysis
        from datetime import datetime
        
        # 1. Save or Update the Post
        post = SocialMediaPost(
            post_id=data['post_id'],
            source=data.get('source', 'unknown'),
            content=data['content'],
            author=data.get('author', 'unknown'),
            created_at=datetime.utcnow()
        )
        db.merge(post) 
        
        # 2. Extract AI results safely (The fix for the 'label' error)
        # We try all possible keys used by HuggingFace pipelines
        label = sentiment.get('label') or sentiment.get('sentiment_label') or 'neutral'
        score = sentiment.get('score') or sentiment.get('confidence_score') or 0.0
        emo = emotion.get('label') or emotion.get('emotion') or 'neutral'

        # 3. Save the Analysis
        analysis = SentimentAnalysis(
            post_id=data['post_id'],
            model_name="distilbert-sst2",
            sentiment_label=label,
            confidence_score=score,
            emotion=emo
        )
        db.add(analysis)
        db.commit()

    async def run(self, batch_size=10, block_ms=5000):
        await self.setup()
        logger.info(f"🚀 {self.consumer_name} ready.")
        while True:
            try:
                messages = await self.redis.xreadgroup(
                    self.group_name, self.consumer_name, {self.stream_name: ">"}, 
                    count=batch_size, block=block_ms
                )
                if not messages: continue
                for _, msgs in messages:
                    tasks = [self.process_message(m_id, m_data) for m_id, m_data in msgs]
                    await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Loop error: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    from models import Base
    Base.metadata.create_all(bind=engine)

    redis_conn = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
    worker = SentimentWorker(redis_conn, SessionLocal, os.getenv("REDIS_STREAM_NAME", "social_posts_stream"), "sentiment_workers")
    asyncio.run(worker.run())