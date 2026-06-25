# Команды для деплоя (копировать и вставлять в PuTTY по порядку)

---

**1. Обновление системы:**
```
apt update && apt upgrade -y
```

**2. Установка Python, Git, pip:**
```
apt install -y python3 python3-pip python3-venv git
```

**3. Клонирование репозитория:**
```
cd /opt && git clone https://github.com/buchatskiii/nail_bot.git && cd nail_bot
```

**4. Виртуальное окружение и зависимости:**
```
python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
```

**5. Создать .env файл (открой .env на компьютере и скопируй содержимое):**
```
nano /opt/nail_bot/.env
```
(Вставь текст → Ctrl+X → Y → Enter)

**6. Создать systemd сервис:**
```
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
```

**7. Запустить сервис:**
```
systemctl daemon-reload && systemctl enable nail_bot && systemctl restart nail_bot
```

**8. Проверить статус:**
```
systemctl status nail_bot
```
