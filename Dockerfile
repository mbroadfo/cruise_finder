# Use official Python image
FROM python:3.11-slim


# Set working directory
WORKDIR /app

# Install OS-level dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries
RUN python -m playwright install --with-deps

# Copy application source code
COPY . .

# Set Python Path
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Default command
CMD ["python", "-m", "src.main"]
