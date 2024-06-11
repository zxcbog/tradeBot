#!/bin/bash

cp ./shared_scripts/ ./strategy_bot
cp ./shared_scripts/ ./telegram_bot

docker-compose up --build