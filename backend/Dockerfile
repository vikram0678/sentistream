# FROM python:3.9-slim

# # Install system dependencies ONCE during build
# RUN apt-get update && apt-get install -y \
#     curl \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# # Install Python requirements ONCE during build
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the rest of the code
# COPY . .

# # Start the app
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



FROM python:3.9-slim

# Install system dependencies once
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]