# 🏗 System Architecture: SentiStream

## 🖼 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SENTISTREAM ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Ingester   │
                              │   (Python)   │
                              └──────┬───────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Redis Streams Broker       │
                    │  (social_posts_stream)          │
                    │  (processed_posts_stream)       │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Worker (AI Engine)         │
                    │  • Transformer Pipeline         │
                    │  • DistilBERT Model             │
                    │  • Sentiment Classification     │
                    └────────────────┬────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
    ┌────▼─────┐              ┌──────▼──────┐         ┌─────────▼─────┐
    │PostgreSQL│              │   Redis     │         │    Backend    │
    │ Database │              │   Streams   │         │   (FastAPI)   │
    │  (posts  │              │ (output)    │         │               │
    │  table)  │              └─────────────┘         └────────┬──────┘
    └──────────┘                                               │
                                                    ┌──────────▼──────────┐
                                                    │  WebSocket Gateway  │
                                                    │  (Live Broadcast)   │
                                                    └──────────┬──────────┘
                                                               │
                                                    ┌──────────▼──────────┐
                                                    │ Frontend (React)    │
                                                    │ • Recharts (Pie)    │
                                                    │ • Recharts (Line)   │
                                                    │ • Real-Time Updates │
                                                    └─────────────────────┘
```

## 🧩 Component Descriptions

**Ingester (Python)**
Acts as the data producer, simulating a high-frequency stream of social media posts. Pushes raw text payloads to Redis Streams at configurable intervals. Designed to handle real-world scaling by distributing multiple ingester instances.

**Redis (Message Broker)**
Uses Redis Streams to decouple data ingestion from processing, ensuring high availability and preventing system crashes during traffic spikes. Maintains two streams: `social_posts_stream` (raw input) and `processed_posts_stream` (enriched output).

**Worker (AI Sentiment Engine)**
The consumer service that pulls batches of posts from Redis Streams, runs NLP sentiment analysis using the DistilBERT transformer model, and classifies sentiment as Positive, Negative, or Neutral. Pushes processed results downstream and persists to PostgreSQL.

**PostgreSQL (Relational Database)**
Stores processed posts, sentiment aggregates, and historical metrics for reporting and analytics. Serves as the source of truth for historical sentiment data.

**Backend (FastAPI)**
The central orchestration hub. Handles HTTP REST requests for stats and recent posts, manages the WebSocket gateway for live updates, and reads from both PostgreSQL and Redis to serve the frontend.

**Frontend (React)**
The presentation layer displaying real-time sentiment charts using Recharts. Maintains WebSocket connections for live updates without page refreshes, providing sub-second latency visualization.

## 🌊 Data Flow

1. **Ingestion**: Raw social media text is generated by the Ingester service and sent to the `social_posts_stream` in Redis
2. **Processing**: The Worker continuously pulls batches from `social_posts_stream`, runs the sentiment model, and classifies each post
3. **Storage**: Processed posts with sentiment labels are stored in PostgreSQL and pushed to `processed_posts_stream` in Redis
4. **Serving**: The Backend listens to `processed_posts_stream`, aggregates metrics, and broadcasts updates via WebSocket to the Frontend dashboard
5. **Visualization**: The React Frontend receives real-time updates and renders dynamic charts showing sentiment distribution and trends

## ⚖️ Technology Justification

**FastAPI**
Chosen for its native asynchronous support (`async`/`await`), making it ideal for high-concurrency WebSocket connections and non-blocking I/O operations. Built-in automatic API documentation (Swagger UI) reduces overhead.

**Redis Streams**
Provides a persistent, append-only log that acts as a buffer between producers and consumers. Prevents system crashes during traffic spikes and enables horizontal scaling of Worker instances without data loss.

**DistilBERT**
A lightweight, distilled version of BERT that achieves 97% of BERT's performance with 40% fewer parameters and 60% faster inference. Critical for real-time analysis with constrained resources (4GB RAM).

**PostgreSQL**
Relational structure ensures data integrity with ACID compliance. Query flexibility supports complex aggregation and historical analysis. Better for structured sentiment data than NoSQL alternatives.

**WebSockets**
Enables full-duplex communication for true real-time updates without HTTP polling overhead. Essential for sub-second latency requirements.

## 📊 Database Schema

### Table: `posts`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `content` | TEXT | NOT NULL | Original post text |
| `sentiment_label` | VARCHAR(10) | NOT NULL | Classification: 'positive', 'negative', 'neutral' |
| `sentiment_score` | FLOAT | NOT NULL | Confidence score [0.0, 1.0] |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Processing timestamp |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

### Indexes

- `idx_timestamp` on `timestamp` (for time-range queries)
- `idx_sentiment_label` on `sentiment_label` (for aggregation queries)

## 📡 API Design

**Pattern**: RESTful for historical data retrieval; Pub/Sub via WebSockets for live event streaming

**Response Format**: All endpoints return JSON for consistency and frontend compatibility

**Key Endpoints**:
- `GET /api/stats` → Returns aggregated sentiment counts
- `GET /api/posts/recent` → Returns 10 most recent posts with sentiment
- `WS /ws/sentiment` → WebSocket for real-time sentiment broadcasts

**Error Handling**: Standard HTTP status codes (200, 400, 404, 500) with descriptive error messages

## 📈 Scalability & Security

**Scalability**
- **Horizontal Scaling**: The Worker service can be scaled to multiple instances consuming from the same Redis Stream, enabling linear throughput increases
- **Load Balancing**: Frontend requests can be distributed across multiple Backend instances using a reverse proxy (nginx, HAProxy)
- **Database Optimization**: PostgreSQL replication and read replicas support increased query load
- **Caching Layer**: Redis can cache frequently-accessed stats to reduce database hits

**Security**
- **CORS Protection**: Backend enforces CORS policies to prevent unauthorized cross-origin requests
- **Rate Limiting**: API endpoints include rate-limiting middleware to prevent abuse
- **Authentication**: Ready for Bearer token / JWT integration on protected endpoints
- **Data Validation**: FastAPI's Pydantic models validate all incoming data
- **Network Isolation**: Services communicate over Docker network; Redis and PostgreSQL are not exposed to host network by default