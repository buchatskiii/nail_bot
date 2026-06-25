#!/bin/bash

# Скрипт для развёртывания бота на сервере
set -e

echo "=== Начинаем развёртывание nail_bot ==="

# 1. Обновление системы
echo ">>> Обновление пакетов..."
apt update && apt upgrade -y

# 2. Установка необходимых пакетов
echo ">>> Установка Python, Git, pip..."
apt install -y python3 python3-pip python3-venv git

# 3. Клонирование репозитория
echo ">>> Клонирование репозитория..."
cd /opt
if [ -d "nail_bot" ]; then
    echo "Репозиторий уже существует, обновляем..."
    cd nail_bot
    git pull origin main
else
    git clone https://github.com/buchatskiii/nail_bot.git
    cd nail_bot
fi

# 4. Создание виртуального окружения
echo ">>> Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# 5. Установка зависимостей
echo ">>> Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Создание .env файла, если его нет
if [ ! -f ".env" ]; then
    echo ">>> Создайте файл .env с настройками бота!"
    echo "Скопируйте .env.example в .env и заполните данные"
    exit 1
fi

# 7. Создание systemd сервиса
echo ">>> Настройка systemd сервиса..."
cat > /etc/systemd/system/nail_bot.service << 'EOF'
[Unit]
Description=Nail Bot - Telegram bot for nail master
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nail_bot
ExecStart=/opt/nail_bot/venv/bin/python /opt/nail_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. Перезагрузка systemd и запуск сервиса
echo ">>> Запуск сервиса..."
systemctl daemon-reload
systemctl enable nail_bot
systemctl restart nail_bot

echo "=== Развёртывание завершено! ==="
echo "Проверьте статус: systemctl status nail_bot"
echo "Логи: journalctl -u nail_bot -f"
