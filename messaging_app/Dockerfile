# messaging_app/Dockerfile

# 1. Base Image
FROM python:3.10

# 2. Set working directory in the container
WORKDIR /app

# 3. Copy the requirements file
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. Copy the entire project code into the container
COPY . .

# 6. Use -p 8000:8000 to map ports when running the container
EXPOSE 8000

# 7. Default command to run the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
