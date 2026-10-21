FROM python:3.8-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
COPY model/ /model/
EXPOSE 5000
CMD ["python", "app.py"]