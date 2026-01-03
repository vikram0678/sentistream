# 📊 SentiStream: Real-Time Sentiment Analysis Platform

SentiStream is a high-performance, distributed data pipeline designed to ingest, analyze, and visualize social media sentiment in real-time. By leveraging a microservices architecture, the platform processes streams of text through an AI sentiment engine, stores metrics in a relational database, and broadcasts updates to a responsive React dashboard via WebSockets. It is designed to provide immediate feedback on public mood and brand perception with sub-second latency.

## 🚀 Features

- **Real-Time Data Ingestion**: High-speed ingestion using Redis Streams
- **AI Sentiment Analysis**: Automated classification (Positive, Negative, Neutral) using DistilBERT transformers
- **Live Dashboard**: Instant UI updates without page refreshes using WebSockets
- **Dynamic Visualizations**: Interactive Pie and Line charts for distribution and trend analysis
- **Containerized Orchestration**: Fully Dockerized services for consistent deployment

## 🏗 Architecture Overview

This project uses a 6-service microservice architecture. For a detailed breakdown of service interactions and design decisions, please refer to the `ARCHITECTURE.md` file.

## 🛠 Prerequisites

- **Docker**: 20.10+ and Docker Compose: 2.0+
- **Memory**: 4GB RAM minimum (required for AI model loading and React builds)
- **Network**: Ports 3000 (Frontend) and 8000 (Backend) must be available
- **API Keys**: This project uses local HuggingFace models; no external API keys are required for the default setup

## ⚡ Quick Start

```bash
# Clone repository
git clone https://github.com/vikram0678/sentistream.git
cd sentistream

# Copy environment template
cp .env.example .env

# Edit .env file (Optional: Defaults are pre-configured)
nano .env

# Start all services
docker compose up -d

# Wait for services to be healthy (30-60 seconds)
docker compose ps

# Access dashboard
# Open http://localhost:3000 in browser

# Stop services
docker compose down
```

## ⚙️ Configuration

The system is configured via the `.env` file:

- **DATABASE_URL**: Connection string for PostgreSQL (e.g., `postgresql://user:password@postgres:5432/sentistream`)
- **REDIS_URL**: Connection string for Redis broker (e.g., `redis://redis:6379`)
- **FRONTEND_URL**: URL for CORS policy (default: `http://localhost:3000`)
- **WORKER_BATCH_SIZE**: Number of posts to process in each batch (default: `32`)
- **MODEL_NAME**: HuggingFace model identifier (default: `distilbert-base-uncased-finetuned-sst-2-english`)

## 📡 API Documentation

- **GET /api/stats**: Returns total counts for all sentiment categories
- **GET /api/posts/recent**: Fetches the 10 most recent processed posts
- **WS /ws/sentiment**: WebSocket endpoint for live sentiment broadcasts

Full interactive documentation available at `http://localhost:8000/docs`

## 🧪 Testing Instructions

To run the backend test suite with coverage reporting:

```bash
docker compose exec backend pytest --cov=app --cov-report=term
```

Expected output should show coverage ≥70% for critical functions.

## 🆘 Troubleshooting

- **Frontend memory error**: Ensure Docker Desktop has 4GB RAM allocated. Run `docker system prune -f` to clear build cache
- **Worker Timeout**: The first run downloads a 184MB DistilBERT model. Check progress with `docker compose logs -f worker`
- **Empty Charts**: Send a test post via Redis: `docker compose exec redis redis-cli xadd social_posts_stream "*" content "Test post"`
- **Port Already in Use**: Change ports in `.env` or stop conflicting services with `lsof -i :3000` or `lsof -i :8000`

## 🔧 Manual Dependency Recovery

If the automatic Docker build gets stuck during installation of heavy AI libraries (torch, transformers), or if the dashboard fails to load, you can manually install dependencies inside the running containers:

**Fix Backend & AI Worker Dependencies**

```bash
# Install missing backend dependencies
docker compose exec backend pip install httpx transformers torch pytest-cov

# Install missing worker dependencies
docker compose exec worker pip install transformers torch
```

**Fix Frontend Dependencies**

```bash
# Force reinstall frontend npm packages
docker compose exec frontend npm install
```

**Run Tests After Recovery**

```bash
# Run full test suite with coverage
docker compose exec backend pytest --cov=. --cov-report=term
```

## 🚀 How the Dashboard Starts (Automated Flow)

Once all dependencies are installed, the system initializes automatically in this sequence:

1. **System Initialization**: Docker Compose starts PostgreSQL and Redis services first, establishing the data layer
2. **Backend Startup**: FastAPI backend launches and opens port 8000, initializing the REST API and WebSocket gateway
3. **Frontend Mounting**: React frontend starts on port 3000 and automatically establishes a persistent WebSocket connection to `ws://localhost:8000/ws/sentiment`
4. **Ingester & Worker**: Data ingester begins streaming mock social posts to Redis, while the worker processes sentiment analysis
5. **Real-Time Sync**: Backend receives processed sentiment data from the worker and pushes updates to all connected WebSocket clients
6. **Dashboard Updates**: Frontend receives live updates and renders charts without page refreshes, showing sentiment distribution and trends with sub-second latency

**Status Check Command**

```bash
# Verify all services are running and healthy
docker compose ps
```

Expected output should show all 6 services with status `healthy` or `running`.

## 📂 Project Structure

```
sentistream/
│
├── 🐳 docker-compose.yml          # Orchestration configuration for all 6 services
│
├── 📁 backend/                     # FastAPI Server & WebSocket Gateway
│   ├── 🚀 main.py                 # FastAPI application, routes, WebSocket handler
│   ├── 🗄️ models.py               # SQLAlchemy ORM models for database
│   ├── 📦 requirements.txt         # Python dependencies (fastapi, sqlalchemy, etc.)
│   ├── 🐳 Dockerfile              # Container image for backend service
│   ├── 🔍 inspect_db.py           # Database inspection utility
│   ├── ✅ test_analyzer.py        # Unit tests for sentiment analyzer
│   ├── ✅ test_ingester.py        # Unit tests for ingester integration
│   │
│   ├── 📁 services/               # Business logic modules
│   │   ├── 🧠 sentiment_analyzer.py  # Transformer-based sentiment classification
│   │   └── 🔔 alerting.py           # Alert and notification logic
│   │
│   └── 📁 tests/                  # Test suite directory
│       └── ✅ test_sentiment.py   # Sentiment analysis unit tests
│
├── 📁 worker/                      # AI Sentiment Analysis Engine
│   ├── ⚙️ worker.py               # Main worker consumer loop
│   ├── 🗄️ models.py               # Data models for sentiment processing
│   ├── 📦 requirements.txt         # Python dependencies (torch, transformers, etc.)
│   │
│   └── 📁 services/               # Worker business logic
│       └── 🧠 sentiment_analyzer.py  # DistilBERT sentiment classification
│
├── 📁 ingester/                    # Data Stream Simulator & Producer
│   ├── 📤 ingester.py             # Social post stream generator
│   ├── 🗄️ models.py               # Data models for raw posts
│   └── 📦 requirements.txt         # Python dependencies (redis, faker, etc.)
│
└── 📁 frontend/                    # React Dashboard & Visualization Layer
    ├── 📦 package.json            # npm dependencies and scripts
    ├── 🔒 package-lock.json       # npm lock file for reproducible installs
    ├── 🔒 yarn.lock               # Yarn lock file (alternative to npm)
    ├── 🎨 tailwind.config.js      # Tailwind CSS configuration
    ├── 🎨 postcss.config.js       # PostCSS configuration
    ├── 📖 README.md               # Frontend-specific documentation
    │
    ├── 📁 public/                 # Static assets served to browser
    │   ├── 📄 index.html          # Main HTML entry point
    │   ├── 🎯 favicon.ico         # Browser tab icon
    │   ├── 📄 manifest.json       # PWA manifest
    │   ├── 🤖 robots.txt          # SEO robots directive
    │   ├── 🖼️ logo192.png         # App logo (192px)
    │   └── 🖼️ logo512.png         # App logo (512px)
    │
    └── 📁 src/                    # React source code
        ├── ⚛️ index.js            # React DOM render entry point
        ├── 🎨 index.css           # Global styles
        ├── ⚛️ App.js              # Main App component
        ├── 🎨 App.css             # App-level styles
        ├── ✅ App.test.js         # App component tests
        ├── ⚙️ setupTests.js       # Jest test configuration
        ├── 📊 reportWebVitals.js  # Performance monitoring
        ├── 🎨 logo.svg            # React logo asset
        │
        ├── 📁 components/         # Reusable React components
        │   ├── 📊 Dashboard.js    # Main dashboard layout
        │   ├── 📈 SentimentChart.js  # Pie chart for sentiment distribution
        │   ├── 📉 TrendChart.js   # Line chart for sentiment trends
        │   └── 📊 Stats.js        # Real-time statistics panel
        │
        └── 📁 services/           # Frontend API & WebSocket services
            ├── 🌐 api.js          # REST API client (axios/fetch)
            └── 🔌 websocket.js    # WebSocket connection handler
```

## 📄 License

MIT License - Copyright (c) 2026 Vikram Nandimandalam