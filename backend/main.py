import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional


from websockets.exceptions import ConnectionClosedError
from fastapi import FastAPI, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, func, desc, text
from sqlalchemy.orm import sessionmaker, Session
from redis import Redis

from services.alerting import AlertService
from models import Base, SocialMediaPost, SentimentAnalysis, SentimentAlert

from fastapi.middleware.cors import CORSMiddleware




# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BackendAPI")

# 2. Initialize Database Engine FIRST
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. NOW Create Tables (This must come AFTER engine is defined)
Base.metadata.create_all(bind=engine)

# 4. Initialize FastAPI and Redis
app = FastAPI(title="SentiStream API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Add your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


redis_client = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

# ... (rest of your code: ConnectionManager, get_db, endpoints, etc.) ...
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4.2 WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # 1. Accept the connection FIRST
        await websocket.accept()
        
        # 2. Add to list
        self.active_connections.append(websocket)
        
        # 3. Try to send the welcome message, but catch errors if they disconnect immediately
        try:
            await websocket.send_json({
                "type": "connected",
                "message": "Connected to sentiment stream",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()

# --- 4.2 Periodic Metrics Task (FIXED NEATLY) ---
async def metrics_broadcaster():
    """Background loop to calculate and broadcast metrics every 30 seconds."""
    while True:
        await asyncio.sleep(30)
        # Using 'with' ensures the session is closed even if the loop crashes
        with SessionLocal() as db:
            try:
                now = datetime.utcnow()
                timeframes = {
                    "last_minute": now - timedelta(minutes=1),
                    "last_hour": now - timedelta(hours=1),
                    "last_24_hours": now - timedelta(hours=24)
                }
                
                metrics = {}
                for timeframe_key, threshold in timeframes.items():
                    counts = db.query(
                        SentimentAnalysis.sentiment_label, 
                        func.count(SentimentAnalysis.id)
                    ).join(SocialMediaPost, SocialMediaPost.post_id == SentimentAnalysis.post_id)\
                    .filter(SocialMediaPost.created_at >= threshold)\
                    .group_by(SentimentAnalysis.sentiment_label).all()
                    
                    mapping = {row[0]: row[1] for row in counts}
                    metrics[timeframe_key] = {
                        "positive": mapping.get("positive", 0),
                        "negative": mapping.get("negative", 0),
                        "neutral": mapping.get("neutral", 0),
                        "total": sum(mapping.values())
                    }

                await manager.broadcast({
                    "type": "metrics_update",
                    "data": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Metrics broadcast error: {e}")

@app.on_event("startup")
async def startup_event():
    # # Run the broadcaster in the current event loop
    # asyncio.create_task(metrics_broadcaster())
    # 1. Initialize the Alert Service using the DB session maker
    alert_service = AlertService(SessionLocal)
    
    # 2. Start the background tasks
    asyncio.create_task(metrics_broadcaster())
    # This is the new part:
    asyncio.create_task(alert_service.run_monitoring_loop())

# --- Endpoint 1: Health Check ---
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    status = "healthy"
    services = {"database": "connected", "redis": "connected"}
    try:
        db.execute(text("SELECT 1"))
    except:
        services["database"] = "disconnected"
        status = "unhealthy"
    try:
        redis_client.ping()
    except:
        services["redis"] = "disconnected"
        status = "unhealthy"

    total_posts = db.query(SocialMediaPost).count()
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_posts = db.query(SocialMediaPost).filter(SocialMediaPost.created_at >= one_hour_ago).count()

    response = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
        "stats": {
            "total_posts": total_posts,
            "total_analyses": db.query(SentimentAnalysis).count(),
            "recent_posts_1h": recent_posts
        }
    }
    if status == "unhealthy": raise HTTPException(status_code=503, detail=response)
    return response

# --- Endpoint 2: Get Posts ---
@app.get("/api/posts")
async def get_posts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SocialMediaPost, SentimentAnalysis).join(
        SentimentAnalysis, SocialMediaPost.post_id == SentimentAnalysis.post_id
    )
    if source: query = query.filter(SocialMediaPost.source == source)
    if sentiment: query = query.filter(SentimentAnalysis.sentiment_label == sentiment)
    total = query.count()
    results = query.order_by(desc(SocialMediaPost.created_at)).offset(offset).limit(limit).all()

    return {
        "posts": [{
            "post_id": p.post_id, "source": p.source, "content": p.content,
            "author": p.author, "created_at": p.created_at,
            "sentiment": {
                "label": s.sentiment_label, "confidence": s.confidence_score,
                "emotion": s.emotion, "model_name": s.model_name
            }
        } for p, s in results],
        "total": total, "limit": limit, "offset": offset,
        "filters": {"source": source, "sentiment": sentiment}
    }

# --- Endpoint 3: Aggregate Sentiment ---
@app.get("/api/sentiment/aggregate")
async def get_sentiment_aggregate(
    period: str = Query(..., regex="^(minute|hour|day)$"),
    db: Session = Depends(get_db)
):
    trunc = func.date_trunc(period, SocialMediaPost.created_at)
    results = db.query(
        trunc.label("ts"), SentimentAnalysis.sentiment_label,
        func.count(SentimentAnalysis.id).label("count"),
        func.avg(SentimentAnalysis.confidence_score).label("avg_conf")
    ).join(SentimentAnalysis, SocialMediaPost.post_id == SentimentAnalysis.post_id)\
     .group_by("ts", SentimentAnalysis.sentiment_label).order_by("ts").all()

    data_map = {}
    for ts, label, count, avg_conf in results:
        ts_iso = ts.isoformat()
        if ts_iso not in data_map:
            data_map[ts_iso] = {"timestamp": ts_iso, "pos": 0, "neg": 0, "neu": 0, "conf_sum": 0, "count": 0}
        if "pos" in label: data_map[ts_iso]["pos"] += count
        elif "neg" in label: data_map[ts_iso]["neg"] += count
        else: data_map[ts_iso]["neu"] += count
        data_map[ts_iso]["count"] += count
        data_map[ts_iso]["conf_sum"] += (avg_conf * count)

    final_data = []
    for item in data_map.values():
        total = item["count"]
        final_data.append({
            "timestamp": item["timestamp"], "positive_count": item["pos"],
            "negative_count": item["neg"], "neutral_count": item["neu"],
            "total_count": total, "positive_percentage": round((item["pos"]/total)*100, 2),
            "average_confidence": round(item["conf_sum"]/total, 2)
        })
    # return {"period": period, "data": final_data}
    # Find the return line at the end of @app.get("/api/sentiment/aggregate")
    return {
        "period": period, 
        "data": final_data,
        "summary": {
            "total_posts": sum(item["total_count"] for item in final_data),
            "positive_total": sum(item["positive_count"] for item in final_data),
            "negative_total": sum(item["negative_count"] for item in final_data),
            "neutral_total": sum(item["neutral_count"] for item in final_data)
        }
    }

# --- Endpoint 4: Sentiment Distribution ---
@app.get("/api/sentiment/distribution")
async def get_sentiment_distribution(hours: int = 24, db: Session = Depends(get_db)):
    cache_key = f"dist_{hours}"
    cached = redis_client.get(cache_key)
    if cached: return {**json.loads(cached), "cached": True}

    threshold = datetime.utcnow() - timedelta(hours=hours)
    dist_query = db.query(
        SentimentAnalysis.sentiment_label, func.count(SentimentAnalysis.id)
    ).join(SocialMediaPost, SocialMediaPost.post_id == SentimentAnalysis.post_id)\
     .filter(SocialMediaPost.created_at >= threshold)\
     .group_by(SentimentAnalysis.sentiment_label).all()
    
    dist = {label: count for label, count in dist_query}
    total = sum(dist.values()) or 1
    
    emotions = db.query(SentimentAnalysis.emotion, func.count(SentimentAnalysis.id))\
        .filter(SentimentAnalysis.post_id.in_(
            db.query(SocialMediaPost.post_id).filter(SocialMediaPost.created_at >= threshold)
        ))\
        .group_by(SentimentAnalysis.emotion).order_by(desc(func.count(SentimentAnalysis.id))).limit(5).all()

    result = {
        "timeframe_hours": hours, "distribution": dist, "total": total,
        "top_emotions": {e: c for e, c in emotions}, "cached": False
    }
    redis_client.setex(cache_key, 60, json.dumps(result, default=str))
    return result



# --- WebSocket Endpoint ---
@app.websocket("/ws/sentiment")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket) # This now handles accept()
    
    pubsub = redis_client.pubsub()
    pubsub.subscribe("sentiment_events")
    
    try:
        while True:
            # Check for messages from Redis
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                raw_data = json.loads(message['data'])
                await websocket.send_json({
                    "type": "new_post",
                    "data": {
                        "post_id": raw_data['post_id'],
                        "content": raw_data['content'][:100],
                        "source": raw_data.get('source', 'unknown'),
                        "sentiment_label": raw_data['sentiment'],
                        "confidence_score": raw_data.get('confidence', 0.99),
                        "emotion": raw_data['emotion'],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            # Check if the client is still there by receiving (non-blocking-ish)
            # This prevents the "ConnectionClosedError" by reacting to client drops
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except asyncio.TimeoutError:
                pass # This is normal, just means no message from client
                
            await asyncio.sleep(0.01) 
    except (WebSocketDisconnect, ConnectionClosedError):
        manager.disconnect(websocket)
    finally:
        pubsub.unsubscribe("sentiment_events")