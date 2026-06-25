# PowerShell скрипт для деплоя бота на сервер
$server = "139.100.234.22"
$password = "NfEB4KQm9l2m"
$keyPath = "$env:USERPROFILE\.ssh\id_rsa_deploy"

Write-Host "=== Деплой nail_bot на сервер $server ===" -ForegroundColor Green

# 1. Копируем SSH ключ на сервер
Write-Host "`n>>> Копируем SSH ключ на сервер..." -ForegroundColor Yellow
$pubKey = Get-Content "$keyPath.pub" -Raw

$sshCommand = @"
mkdir -p ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh && echo 'SSH key added successfully'
"@

# Используем ssh с передачей пароля через переменную
$env:SSHPASS = $password
sshpass -e ssh -o StrictHostKeyChecking=no root@$server $sshCommand 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "sshpass не работает, пробуем через ssh с ключом..." -ForegroundColor Yellow
    # Если ключ уже добавлен, пробуем подключиться
    ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "echo 'SSH key works!'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n⚠️  Не удалось подключиться по SSH." -ForegroundColor Red
        Write-Host "Пожалуйста, выполните следующие шаги вручную:" -ForegroundColor Yellow
        Write-Host "1. Откройте PuTTY и подключитесь к $server" -ForegroundColor White
        Write-Host "2. Войдите как root с паролем" -ForegroundColor White
        Write-Host "3. Выполните команды из файла deploy.sh" -ForegroundColor White
        exit 1
    }
}

# 2. Обновление системы и установка пакетов
Write-Host "`n>>> Обновление системы..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "apt update && apt upgrade -y && apt install -y python3 python3-pip python3-venv git" 2>&1

# 3. Клонирование репозитория
Write-Host "`n>>> Клонирование репозитория..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "cd /opt && if [ -d nail_bot ]; then cd nail_bot && git pull origin main; else git clone https://github.com/buchatskiii/nail_bot.git && cd nail_bot; fi" 2>&1

# 4. Создание виртуального окружения и установка зависимостей
Write-Host "`n>>> Установка зависимостей Python..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "cd /opt/nail_bot && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt" 2>&1

# 5. Создаём .env файл
Write-Host "`n>>> Настройка .env файла..." -ForegroundColor Yellow
Write-Host "⚠️  ВАЖНО: Файл .env будет создан из локального .env файла!" -ForegroundColor Red

# Читаем локальный .env
$envContent = Get-Content "C:\Users\dlyav\Desktop\nail_bot\.env" -Raw

# Создаём .env на сервере через heredoc
$createEnvCommand = @"
cat > /opt/nail_bot/.env << 'ENVEOF'
$envContent
ENVEOF
echo '.env file created'
"@

ssh -o StrictHostKeyChecking=no -i $keyPath root@$server $createEnvCommand 2>&1

# 6. Создание systemd сервиса
Write-Host "`n>>> Настройка systemd сервиса..." -ForegroundColor Yellow
$serviceContent = @'
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
'@

$createServiceCommand = @"
cat > /etc/systemd/system/nail_bot.service << 'SERVICEEOF'
$serviceContent
SERVICEEOF
echo 'Service file created'
"@

ssh -o StrictHostKeyChecking=no -i $keyPath root@$server $createServiceCommand 2>&1

# 7. Запуск сервиса
Write-Host "`n>>> Запуск сервиса..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "systemctl daemon-reload && systemctl enable nail_bot && systemctl restart nail_bot" 2>&1

# 8. Проверка статуса
Write-Host "`n>>> Проверка статуса..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $keyPath root@$server "systemctl status nail_bot --no-pager" 2>&1

Write-Host "`n=== Деплой завершён! ===" -ForegroundColor Green
Write-Host "Проверьте логи: journalctl -u nail_bot -f" -ForegroundColor Cyan
