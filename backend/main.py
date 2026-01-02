import os
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException, Depends
from sqlalchemy import create_engine, func, desc, text
from sqlalchemy.orm import sessionmaker, Session
from redis import Redis
from models import SocialMediaPost, SentimentAnalysis

app = FastAPI(title="SentiStream API")

# --- Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

redis_client = Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoint 1: Health Check (2 Points) ---
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
    
    if status == "unhealthy":
        raise HTTPException(status_code=503, detail=response)
    return response

# --- Endpoint 2: Get Posts (5 Points) ---
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

    if source:
        query = query.filter(SocialMediaPost.source == source)
    if sentiment:
        query = query.filter(SentimentAnalysis.sentiment_label == sentiment)

    total = query.count()
    results = query.order_by(desc(SocialMediaPost.created_at)).offset(offset).limit(limit).all()

    return {
        "posts": [{
            "post_id": p.post_id,
            "source": p.source,
            "content": p.content,
            "author": p.author,
            "created_at": p.created_at,
            "sentiment": {
                "label": s.sentiment_label,
                "confidence": s.confidence_score,
                "emotion": s.emotion,
                "model_name": s.model_name
            }
        } for p, s in results],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {"source": source, "sentiment": sentiment}
    }

# --- Endpoint 3: Aggregate Sentiment (5 Points) ---
@app.get("/api/sentiment/aggregate")
async def get_sentiment_aggregate(
    period: str = Query(..., regex="^(minute|hour|day)$"),
    db: Session = Depends(get_db)
):
    # PostgreSQL date_trunc logic
    trunc = func.date_trunc(period, SocialMediaPost.created_at)
    
    results = db.query(
        trunc.label("ts"),
        SentimentAnalysis.sentiment_label,
        func.count(SentimentAnalysis.id).label("count"),
        func.avg(SentimentAnalysis.confidence_score).label("avg_conf")
    ).join(SentimentAnalysis, SocialMediaPost.post_id == SentimentAnalysis.post_id)\
     .group_by("ts", SentimentAnalysis.sentiment_label)\
     .order_by("ts").all()

    # Process results into the required nested structure
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
            "timestamp": item["timestamp"],
            "positive_count": item["pos"],
            "negative_count": item["neg"],
            "neutral_count": item["neu"],
            "total_count": total,
            "positive_percentage": round((item["pos"]/total)*100, 2),
            "average_confidence": round(item["conf_sum"]/total, 2)
        })

    return {"period": period, "data": final_data}

# --- Endpoint 4: Sentiment Distribution (3 Points) ---
@app.get("/api/sentiment/distribution")
async def get_sentiment_distribution(hours: int = 24, db: Session = Depends(get_db)):
    cache_key = f"dist_{hours}"
    cached = redis_client.get(cache_key)
    if cached:
        return {**json.loads(cached), "cached": True}

    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Get Counts
    dist_query = db.query(
        SentimentAnalysis.sentiment_label, func.count(SentimentAnalysis.id)
    ).join(SocialMediaPost, SocialMediaPost.post_id == SentimentAnalysis.post_id)\
     .filter(SocialMediaPost.created_at >= threshold)\
     .group_by(SentimentAnalysis.sentiment_label).all()
    
    dist = {label: count for label, count in dist_query}
    total = sum(dist.values()) or 1
    
    # Get Top Emotions
    emotions = db.query(SentimentAnalysis.emotion, func.count(SentimentAnalysis.id))\
        .filter(SentimentAnalysis.post_id.in_(
            db.query(SocialMediaPost.post_id).filter(SocialMediaPost.created_at >= threshold)
        ))\
        .group_by(SentimentAnalysis.emotion).order_by(desc(func.count(SentimentAnalysis.id))).limit(5).all()

    result = {
        "timeframe_hours": hours,
        "distribution": dist,
        "total": total,
        "top_emotions": {e: c for e, c in emotions},
        "cached": False
    }
    
    redis_client.setex(cache_key, 60, json.dumps(result, default=str))
    return result
