# Use the official Python 3.9 image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Create a non-root user (Hugging Face Spaces requirement for security)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy requirements file to the working directory
COPY --chown=user ./requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# COPY THE MODEL FOLDER
# This assumes your 'my_email_classifier' folder is in the same directory as this Dockerfile
COPY --chown=user ./my_email_classifier /app/my_email_classifier

# Copy the app code
COPY --chown=user ./app.py /app/app.py

# Expose the port used by Spaces
EXPOSE 7860

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]