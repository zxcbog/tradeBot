FROM python:3.9-slim

WORKDIR /app

COPY strategy_bot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY strategy_bot/ /app
COPY shared_scripts/ /app/shared_scripts

EXPOSE 80

CMD ["python", "StrategyBot.py"]
