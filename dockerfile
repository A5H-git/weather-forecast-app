# Use the base python 3.12 image
FROM python:3.12-slim

# Set WD
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project container
COPY . /app/

# Run migration scripts
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Run server script
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]




