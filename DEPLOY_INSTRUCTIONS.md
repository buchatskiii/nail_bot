# Инструкция по деплою бота на сервер

## Шаг 1: Подключитесь к серверу через PuTTY

- **IP адрес:** 139.100.234.22
- **Порт:** 22
- **Логин:** root
- **Пароль:** NfEB4KQm9l2m

## Шаг 2: Выполните команды по порядку

### 1. Обновление системы
```bash
apt update && apt upgrade -y
```

### 2. Установка Python, Git, pip
```bash
apt install -y python3 python3-pip python3-venv git
```

### 3. Клонирование репозитория
```bash
cd /opt
git clone https://github.com/buchatskiii/nail_bot.git
cd nail_bot
```

### 4. Создание виртуального окружения и установка зависимостей
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Создание .env файла
Скопируйте содержимое файла `.env` с вашего компьютера и выполните:
```bash
nano /opt/nail_bot/.env
```
Вставьте содержимое .env, сохраните (Ctrl+X, Y, Enter).

### 6. Создание systemd сервиса
```bash
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

### 7. Запуск сервиса
```bash
systemctl daemon-reload
systemctl enable nail_bot
systemctl restart nail_bot
```

### 8. Проверка статуса
```bash
systemctl status nail_bot
```

### 9. Просмотр логов (если нужно)
```bash
journalctl -u nail_bot -f
```

## Шаг 3: Проверка работы

Откройте Telegram и отправьте боту команду `/start`. Если бот отвечает — всё работает!

## Полезные команды

- **Перезапуск бота:** `systemctl restart nail_bot`
- **Остановка бота:** `systemctl stop nail_bot`
- **Логи в реальном времени:** `journalctl -u nail_bot -f`
- **Обновление бота:** 
  ```bash
  cd /opt/nail_bot
  git pull origin main
  systemctl restart nail_bot
  ```
