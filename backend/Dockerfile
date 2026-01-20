FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
# We assume requirements files are moved to backend/requirements/ or similar, 
# but for now we'll copy them if they exist, or just use a basic setup.
# IMPORTANT: Adjusting to the new structure where requirements might be in root or moved.
# Since we moved 'pipeline' and 'common' into 'backend', we need a requirements.txt here.
# For now, we'll create a requirements.txt in the next step.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Command is set in docker-compose, but safe default:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
