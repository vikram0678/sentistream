# import os  # <-- This was missing!
# import logging
# from datetime import datetime
# from fastapi import FastAPI, status
# from fastapi.responses import JSONResponse
# from sqlalchemy import create_engine, text
# from sqlalchemy.exc import SQLAlchemyError
# import redis
# from redis.exceptions import RedisError

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Import models (ensure models.py exists with Base)
# try:
#     from models import Base
#     logger.info("Models imported successfully.")
# except ImportError as e:
#     logger.error(f"models.py import failed: {e}. Skipping schema creation.")
#     Base = None

# app = FastAPI(title="SentiStream API")

# # Auto-create schema on startup (with error handling)
# try:
#     engine = create_engine(os.getenv("DATABASE_URL"))
#     if Base:
#         Base.metadata.create_all(bind=engine)
#         logger.info("Database schema created successfully.")
#     else:
#         logger.warning("Skipping schema creation (no models).")
# except Exception as e:
#     logger.error(f"Database startup error: {e}")

# @app.get("/api/health")
# async def health_check():
#     db_status = "disconnected"
#     redis_status = "disconnected"
#     stats = {"total_posts": 0, "total_analyses": 0, "recent_posts_1h": 0}
#     error_msg = None

#     try:
#         # Test DB
#         with engine.connect() as conn:
#             conn.execute(text("SELECT 1"))
#             conn.commit()
#             db_status = "connected"
#             logger.info("Health: DB connected.")
#     except SQLAlchemyError as e:
#         error_msg = f"DB error: {e}"
#         logger.error(error_msg)
#     except Exception as e:
#         error_msg = f"Unexpected DB error: {e}"
#         logger.error(error_msg)

#     try:
#         # Test Redis
#         r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
#         r.ping()
#         redis_status = "connected"
#         logger.info("Health: Redis connected.")
#     except RedisError as e:
#         error_msg = f"Redis error: {e}"
#         logger.error(error_msg)
#     except Exception as e:
#         error_msg = f"Unexpected Redis error: {e}"
#         logger.error(error_msg)

#     # Determine overall status
#     overall_status = "healthy" if db_status == "connected" and redis_status == "connected" else "unhealthy"
#     http_status = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

#     response = {
#         "status": overall_status,
#         "timestamp": datetime.utcnow().isoformat() + "Z",
#         "services": {"database": db_status, "redis": redis_status},
#         "stats": stats
#     }
#     if error_msg:
#         response["error"] = error_msg

#     logger.info(f"Health response: {response}")
#     return JSONResponse(status_code=http_status, content=response)

# if __name__ == "__main__":
#     import uvicorn
#     host = os.getenv("API_HOST", "0.0.0.0")
#     port = int(os.getenv("API_PORT", 8000))
#     logger.info(f"Starting server on {host}:{port}")
#     uvicorn.run(app, host=host, port=port, log_level="info")






import os
import logging
import redis
from datetime import datetime
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SentiStream API")

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_engine(DATABASE_URL)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")

@app.get("/api/health")
async def health_check():
    health = {"database": "disconnected", "redis": "disconnected"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            health["database"] = "connected"
        
        r = redis.from_url(REDIS_URL)
        if r.ping():
            health["redis"] = "connected"
            
        is_healthy = all(v == "connected" for v in health.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "services": health,
                "stats": {"total_posts": 0} 
            }
        )
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})