FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files except venv
COPY . .

# Run Streamlit app (change this line if you want to run main2.py or main3.py)
CMD ["streamlit", "run", "main.py", "--server.port=80", "--server.address=0.0.0.0"]

EXPOSE 80
