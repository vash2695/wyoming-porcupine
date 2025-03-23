FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source code
COPY setup.py ./
COPY wyoming_porcupine3/ ./wyoming_porcupine3/

# Install package
RUN pip3 install --no-cache-dir -e .

ENTRYPOINT ["wyoming-porcupine3"] 