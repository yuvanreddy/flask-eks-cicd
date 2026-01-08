FROM python:3.9-slim

WORKDIR /app

# Install Flask
RUN pip install flask

# Copy application code
COPY app.py .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]