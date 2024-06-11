FROM python:3.9-slim

WORKDIR /app

COPY telegram_bot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_bot/ /app
COPY shared_scripts/ /app/shared_scripts

EXPOSE 80

CMD ["python", "TelegramBot.py"]
