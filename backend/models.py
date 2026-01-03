from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

# Define Base here to avoid relative import issues in your environment
Base = declarative_base()



class SocialMediaPost(Base):
    """
    Table 1: social_media_posts
    Purpose: Store raw social media posts
    """
    __tablename__ = 'social_media_posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Required: String (255), unique, indexed
    post_id = Column(String(255), unique=True, nullable=False, index=True)
    # Required: String (50), indexed
    source = Column(String(50), nullable=False, index=True)
    # Required: Text (no length limit)
    content = Column(Text, nullable=False)
    # Required: String (255)
    author = Column(String(255), nullable=False)
    # Required: DateTime, indexed (Manual index added for dashboard performance)
    created_at = Column(DateTime, nullable=False, index=True)
    # Required: DateTime, default to current timestamp
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to analyses
    analyses = relationship("SentimentAnalysis", back_populates="post", cascade="all, delete-orphan")


class SentimentAnalysis(Base):
    """
    Table 2: sentiment_analysis
    Purpose: Store sentiment analysis results
    """
    __tablename__ = 'sentiment_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Required: Foreign key referencing social_media_posts.post_id
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'), nullable=False)
    # Required: String (100)
    model_name = Column(String(100), nullable=False)
    # Required: String (20)
    sentiment_label = Column(String(20), nullable=False)
    # Required: Float (0.0 to 1.0)
    confidence_score = Column(Float, nullable=False)
    # Required: String (50), nullable
    emotion = Column(String(50), nullable=True)
    # Required: DateTime, default to current timestamp, indexed
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship back to post
    post = relationship("SocialMediaPost", back_populates="analyses")


class SentimentAlert(Base):
    """
    Table 3: sentiment_alerts
    Purpose: Store triggered alerts
    """
    __tablename__ = 'sentiment_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Required: String (50)
    alert_type = Column(String(50), nullable=False)
    # Required: Float
    threshold_value = Column(Float, nullable=False)
    # Required: Float
    actual_value = Column(Float, nullable=False)
    # Required: DateTime

    window_minutes = Column(Integer, nullable=False, default=5)

    window_start = Column(DateTime, nullable=False)
    # Required: DateTime
    window_end = Column(DateTime, nullable=False)
    # Required: Integer
    post_count = Column(Integer, nullable=False)
    # Required: DateTime, default to current timestamp, indexed
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # Required: JSON (Using JSONB for PostgreSQL efficiency)
    details = Column(JSONB, nullable=False)

# Explicitly defining indexes as per requirements
Index('idx_post_id', SocialMediaPost.post_id)
Index('idx_source', SocialMediaPost.source)
Index('idx_created_at', SocialMediaPost.created_at)
Index('idx_analyzed_at', SentimentAnalysis.analyzed_at)
Index('idx_triggered_at', SentimentAlert.triggered_at)