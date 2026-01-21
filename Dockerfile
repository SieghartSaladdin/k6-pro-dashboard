# Base Image Python 3.10 Slim
FROM python:3.10-slim

# Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set Work Directory
WORKDIR /app

# Install dependencies (curl for k6 download)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install k6 (Load Testing Tool)
# Using generic linux-amd64 binary
RUN curl -L https://github.com/grafana/k6/releases/download/v0.56.0/k6-v0.56.0-linux-amd64.tar.gz -o k6.tar.gz \
    && tar -xzf k6.tar.gz \
    && mv k6-*-linux-amd64/k6 /usr/local/bin/k6 \
    && rm -rf k6.tar.gz k6-*-linux-amd64

# Verify k6 installation
RUN k6 version

# Install Python Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Project Files
COPY . .

# Ensure results directory exists
RUN mkdir -p results

# Expose Streamlit Default Port
EXPOSE 8501

# Run the Application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
