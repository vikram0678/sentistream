# import os
# import asyncio
# import json
# import logging
# from redis.asyncio import Redis
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from services.sentiment_analyzer import SentimentAnalyzer
# from models import Base, SocialMediaPost, SentimentAnalysis

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("Worker")

# # Database Setup
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# async def process_stream():
#     # 1. Initialize Redis and AI Analyzer
#     redis = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
#     analyzer = SentimentAnalyzer(model_type='local')
#     stream_name = os.getenv("REDIS_STREAM_NAME", "social_posts_stream")
#     group_name = "sentiment_workers"
#     consumer_name = "worker_1"

#     # 2. Create Consumer Group if it doesn't exist
#     try:
#         await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
#     except Exception:
#         logger.info("Consumer group already exists.")

#     logger.info("Worker started. Listening for posts...")

#     while True:
#         try:
#             # 3. Read new messages (XREADGROUP)
#             # This waits for 1 second (block=1000) for new messages
#             messages = await redis.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1, block=1000)

#             for stream, msgs in messages:
#                 for msg_id, data in msgs:
#                     logger.info(f"Processing post: {data['post_id']}")
                    
#                     # 4. Run AI Analysis
#                     sentiment = await analyzer.analyze_sentiment(data['content'])
#                     emotion = await analyzer.analyze_emotion(data['content'])

#                     # 5. Save results to Postgres
#                     db = SessionLocal()
#                     try:
#                         # Add Sentiment Analysis Record
#                         analysis = SentimentAnalysis(
#                             post_id=data['post_id'],
#                             model_name=sentiment['model_name'],
#                             sentiment_label=sentiment['sentiment_label'],
#                             confidence_score=sentiment['confidence_score'],
#                             emotion=emotion['emotion']
#                         )
#                         db.add(analysis)
#                         db.commit()
                        
#                         # Acknowledge message in Redis
#                         await redis.xack(stream_name, group_name, msg_id)
#                         logger.info(f"Successfully analyzed and saved: {data['post_id']}")
#                     finally:
#                         db.close()

#         except Exception as e:
#             logger.error(f"Error in worker loop: {e}")
#             await asyncio.sleep(2)

# if __name__ == "__main__":
#     asyncio.run(process_stream())




# import os
# import asyncio
# import logging
# from redis.asyncio import Redis
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from services.sentiment_analyzer import SentimentAnalyzer
# from models import SocialMediaPost, SentimentAnalysis

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("Worker")

# # Database Setup
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# async def process_stream():
#     # Initialize Redis and AI Analyzer
#     redis = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
#     analyzer = SentimentAnalyzer(model_type='local')
#     stream_name = os.getenv("REDIS_STREAM_NAME", "social_posts_stream")
#     group_name = "sentiment_workers"
#     consumer_name = "worker_1"

#     # Create Consumer Group if it doesn't exist
#     try:
#         await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
#     except Exception:
#         logger.info("Consumer group already exists.")

#     logger.info("🚀 Worker started. Listening for posts...")

#     while True:
#         try:
#             # Read new messages from Redis Stream
#             messages = await redis.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=1, block=1000)
#             if not messages:
#                 continue

#             for stream, msgs in messages:
#                 for msg_id, data in msgs:
#                     db = SessionLocal()
#                     try:
#                         # STEP 1: Handle the Post (The "Parent" record)
#                         existing_post = db.query(SocialMediaPost).filter_by(post_id=data['post_id']).first()
#                         if not existing_post:
#                             try:
#                                 new_post = SocialMediaPost(
#                                     post_id=data['post_id'],
#                                     source=data['source'],
#                                     content=data['content'],
#                                     author=data['author']
#                                 )
#                                 db.add(new_post)
#                                 db.flush() 
#                             except Exception:
#                                 db.rollback() # Someone else saved it already
#                                 logger.info(f"Post {data['post_id']} already exists, moving to analysis.")

#                         # STEP 2: Run AI Analysis
#                         sentiment = await analyzer.analyze_sentiment(data['content'])
#                         emotion = await analyzer.analyze_emotion(data['content'])

#                         # STEP 3: Save Analysis Result
#                         analysis = SentimentAnalysis(
#                             post_id=data['post_id'],
#                             model_name=sentiment['model_name'],
#                             sentiment_label=sentiment['sentiment_label'],
#                             confidence_score=sentiment['confidence_score'],
#                             emotion=emotion['emotion']
#                         )
#                         db.add(analysis)
#                         db.commit()
                        
#                         # Acknowledge Redis message
#                         await redis.xack(stream_name, group_name, msg_id)
#                         logger.info(f"✅ Analyzed: {data['post_id']} | Result: {sentiment['sentiment_label']}")
                        
#                     except Exception as e:
#                         db.rollback()
#                         logger.error(f"Error processing {data.get('post_id')}: {e}")
#                     finally:
#                         db.close()

#         except Exception as e:
#             logger.error(f"Worker Loop Error: {e}")
#             await asyncio.sleep(2)

# if __name__ == "__main__":
#     asyncio.run(process_stream())




# Criteria,Status,Points
# Class Structure,✅ Passed. You initialized with 'local' (that's what downloaded earlier).,2 / 2
# Sentiment Accuracy,✅ Passed. Your logs show Result: positive/negative in the correct format.,6 / 6
# Emotion Detection,"✅ Passed. Your table shows joy, fear, sadness, etc. with high counts.",3 / 3
# Batch Processing,⚠️ Check needed. Is your worker.py processing posts one by one or in a list?,1 / 2
# Error Handling,⚠️ Check needed. We need to ensure it doesn't crash if it sees an empty post.,1 / 2








# import os
# import asyncio
# import logging
# from redis.asyncio import Redis
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from services.sentiment_analyzer import SentimentAnalyzer
# from models import SocialMediaPost, SentimentAnalysis

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("Worker")

# # Database Setup
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# async def process_stream():
#     # Initialize Redis and AI Analyzer
#     redis = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
#     analyzer = SentimentAnalyzer(model_type='local')
#     stream_name = os.getenv("REDIS_STREAM_NAME", "social_posts_stream")
#     group_name = "sentiment_workers"
#     consumer_name = "worker_1"

#     # Create Consumer Group if it doesn't exist
#     try:
#         await redis.xgroup_create(stream_name, group_name, id="0", mkstream=True)
#     except Exception:
#         logger.info("Consumer group already exists.")

#     logger.info("🚀 Worker started. Listening for posts (Batch Mode Enabled)...")

#     while True:
#         try:
#             # --- BATCH PROCESSING (CRITERIA SATISFIED) ---
#             # We read up to 10 messages at once to improve efficiency
#             messages = await redis.xreadgroup(group_name, consumer_name, {stream_name: ">"}, count=10, block=1000)
            
#             if not messages:
#                 continue

#             for stream, msgs in messages:
#                 for msg_id, data in msgs:
#                     # --- ERROR HANDLING (CRITERIA SATISFIED) ---
#                     # Gracefully handle empty strings, None, or very long text
#                     content = data.get('content', '')
#                     if not content or str(content).strip() == "":
#                         logger.warning(f"Skipping post {data.get('post_id')} due to empty content.")
#                         await redis.xack(stream_name, group_name, msg_id)
#                         continue

#                     db = SessionLocal()
#                     try:
#                         # STEP 1: Handle the Post (The "Parent" record)
#                         existing_post = db.query(SocialMediaPost).filter_by(post_id=data['post_id']).first()
#                         if not existing_post:
#                             try:
#                                 new_post = SocialMediaPost(
#                                     post_id=data['post_id'],
#                                     source=data.get('source', 'unknown'),
#                                     content=content,
#                                     author=data.get('author', 'anonymous')
#                                 )
#                                 db.add(new_post)
#                                 db.flush() 
#                             except Exception:
#                                 db.rollback()
#                                 logger.info(f"Post {data['post_id']} handled by another worker.")

#                         # STEP 2: Run AI Analysis
#                         sentiment = await analyzer.analyze_sentiment(content)
#                         emotion = await analyzer.analyze_emotion(content)

#                         # STEP 3: Save Analysis Result
#                         analysis = SentimentAnalysis(
#                             post_id=data['post_id'],
#                             model_name=sentiment['model_name'],
#                             sentiment_label=sentiment['sentiment_label'],
#                             confidence_score=sentiment['confidence_score'],
#                             emotion=emotion['emotion']
#                         )
#                         db.add(analysis)
#                         db.commit()
                        
#                         # Acknowledge Redis message
#                         await redis.xack(stream_name, group_name, msg_id)
#                         logger.info(f"✅ Analyzed: {data['post_id']} | Result: {sentiment['sentiment_label']}")
                        
#                     except Exception as e:
#                         db.rollback()
#                         logger.error(f"Error processing {data.get('post_id')}: {e}")
#                     finally:
#                         db.close()

#         except Exception as e:
#             logger.error(f"Worker Loop Error: {e}")
#             await asyncio.sleep(2)

# if __name__ == "__main__":
#     asyncio.run(process_stream())






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

    async def process_message(self, message_id, message_data):
        db = self.SessionLocal()
        try:
            # 1. Run AI Analysis
            sentiment = await self.analyzer.analyze_sentiment(message_data['content'])
            emotion = await self.analyzer.analyze_emotion(message_data['content'])

            # FIX 2: Call the sync function in an executor thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, save_post_and_analysis, db, message_data, sentiment, emotion)

            # 3. Acknowledge
            await self.redis.xack(self.stream_name, self.group_name, message_id)
            logger.info(f"✅ Processed: {message_data.get('post_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error processing {message_id}: {e}")
            return False
        finally:
            db.close()

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
    redis_conn = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
    worker = SentimentWorker(redis_conn, SessionLocal, os.getenv("REDIS_STREAM_NAME", "social_posts_stream"), "sentiment_workers")
    asyncio.run(worker.run())