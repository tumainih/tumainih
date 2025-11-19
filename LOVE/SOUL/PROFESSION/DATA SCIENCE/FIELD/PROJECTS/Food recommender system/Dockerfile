FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port used by Streamlit
EXPOSE 8501
ENV PORT=8501

# Run the app
CMD ["streamlit", "run", "a.py", "--server.port=8501", "--server.address=0.0.0.0"]
