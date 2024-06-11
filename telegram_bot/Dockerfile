FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY ../shared_scripts .

EXPOSE 80

CMD ["python", "tg.py"]
