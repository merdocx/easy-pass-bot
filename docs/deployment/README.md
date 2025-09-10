# Руководство по развертыванию

## Обзор

Это руководство описывает процесс развертывания Easy Pass Bot в различных окружениях: от локальной разработки до продакшн сервера.

## Требования к системе

### Минимальные требования

- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python**: 3.8+
- **RAM**: 512 MB
- **Диск**: 1 GB свободного места
- **Сеть**: Доступ к интернету

### Рекомендуемые требования

- **ОС**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **RAM**: 2 GB
- **Диск**: 5 GB SSD
- **Сеть**: Стабильное соединение

### Дополнительные требования

- **SQLite**: 3.8+
- **Git**: 2.0+
- **Docker**: 20.10+ (опционально)
- **Nginx**: 1.18+ (для reverse proxy)

## Подготовка сервера

### 1. Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Установка Python

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv python3-dev -y

# CentOS/RHEL
sudo yum install python3 python3-pip python3-devel -y
```

### 3. Создание пользователя

```bash
# Создание пользователя для бота
sudo useradd -m -s /bin/bash easypass
sudo usermod -aG sudo easypass

# Переключение на пользователя
sudo su - easypass
```

## Установка

### Метод 1: Прямая установка

#### 1. Клонирование репозитория

```bash
cd /home/easypass
git clone https://github.com/merdocx/easy-pass-bot.git
cd easy-pass-bot
```

#### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r deploy/requirements.txt
```

#### 4. Настройка окружения

```bash
cp .env.example .env
nano .env
```

**Содержимое .env файла:**
```bash
# Telegram Bot Token
BOT_TOKEN=your_telegram_bot_token_here

# Database
DATABASE_PATH=database/easy_pass.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Security
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

#### 5. Создание директорий

```bash
mkdir -p logs database
chmod 755 logs database
```

#### 6. Инициализация базы данных

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from easy_pass_bot.database import db
import asyncio

async def init():
    await db.init_db()
    print('База данных инициализирована')

asyncio.run(init())
"
```

### Метод 2: Docker

#### 1. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN useradd -m -s /bin/bash easypass

# Установка рабочей директории
WORKDIR /app

# Копирование файлов
COPY deploy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создание директорий
RUN mkdir -p logs database && \
    chown -R easypass:easypass /app

# Переключение на пользователя
USER easypass

# Команда запуска
CMD ["python", "main.py"]
```

#### 2. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  easy-pass-bot:
    build: .
    container_name: easy-pass-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_PATH=database/easy_pass.db
      - LOG_LEVEL=INFO
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
    networks:
      - easy-pass-network

networks:
  easy-pass-network:
    driver: bridge
```

#### 3. Запуск с Docker

```bash
# Создание .env файла
echo "BOT_TOKEN=your_telegram_bot_token_here" > .env

# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## Настройка systemd

### 1. Создание сервиса

```bash
sudo nano /etc/systemd/system/easy-pass-bot.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Easy Pass Telegram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=easypass
Group=easypass
WorkingDirectory=/home/easypass/easy-pass-bot
Environment=PATH=/home/easypass/easy-pass-bot/venv/bin
ExecStart=/home/easypass/easy-pass-bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ограничения ресурсов
MemoryLimit=1G
CPUQuota=50%

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/easypass/easy-pass-bot/logs /home/easypass/easy-pass-bot/database

[Install]
WantedBy=multi-user.target
```

### 2. Активация сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable easy-pass-bot

# Запуск сервиса
sudo systemctl start easy-pass-bot

# Проверка статуса
sudo systemctl status easy-pass-bot
```

## Настройка Nginx (опционально)

### 1. Установка Nginx

```bash
sudo apt install nginx -y
```

### 2. Конфигурация

```bash
sudo nano /etc/nginx/sites-available/easy-pass-bot
```

**Содержимое файла:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Логи
    access_log /var/log/nginx/easy-pass-bot.access.log;
    error_log /var/log/nginx/easy-pass-bot.error.log;

    # Статические файлы
    location /static/ {
        alias /home/easypass/easy-pass-bot/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API (если используется)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### 3. Активация сайта

```bash
sudo ln -s /etc/nginx/sites-available/easy-pass-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Настройка мониторинга

### 1. Prometheus (опционально)

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'easy-pass-bot'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Grafana (опционально)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Настройка бэкапов

### 1. Скрипт бэкапа

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/easypass/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BOT_DIR="/home/easypass/easy-pass-bot"

# Создание директории бэкапа
mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp $BOT_DIR/database/easy_pass.db $BACKUP_DIR/easy_pass_$DATE.db

# Бэкап логов
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz $BOT_DIR/logs/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Бэкап завершен: $DATE"
```

### 2. Настройка cron

```bash
# Добавление в crontab
crontab -e

# Бэкап каждый день в 2:00
0 2 * * * /home/easypass/easy-pass-bot/backup.sh
```

## Настройка SSL (опционально)

### 1. Установка Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Получение сертификата

```bash
sudo certbot --nginx -d your-domain.com
```

### 3. Автообновление

```bash
sudo crontab -e

# Проверка обновления сертификата каждый день
0 12 * * * /usr/bin/certbot renew --quiet
```

## Проверка развертывания

### 1. Проверка сервиса

```bash
# Статус сервиса
sudo systemctl status easy-pass-bot

# Логи
sudo journalctl -u easy-pass-bot -f

# Проверка портов
sudo netstat -tlnp | grep python
```

### 2. Проверка бота

```bash
# Тест подключения к Telegram
curl -X GET "https://api.telegram.org/bot$BOT_TOKEN/getMe"

# Проверка базы данных
sqlite3 database/easy_pass.db ".tables"
```

### 3. Мониторинг производительности

```bash
# Использование памяти
ps aux | grep python

# Использование диска
df -h

# Логи ошибок
tail -f logs/bot.log | grep ERROR
```

## Обновление

### 1. Остановка сервиса

```bash
sudo systemctl stop easy-pass-bot
```

### 2. Обновление кода

```bash
cd /home/easypass/easy-pass-bot
git pull origin main
```

### 3. Обновление зависимостей

```bash
source venv/bin/activate
pip install -r deploy/requirements.txt
```

### 4. Миграция базы данных

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from easy_pass_bot.database import db
import asyncio

async def migrate():
    await db.init_db()
    print('Миграция завершена')

asyncio.run(migrate())
"
```

### 5. Запуск сервиса

```bash
sudo systemctl start easy-pass-bot
```

## Откат

### 1. Остановка сервиса

```bash
sudo systemctl stop easy-pass-bot
```

### 2. Восстановление из бэкапа

```bash
# Восстановление базы данных
cp /home/easypass/backups/easy_pass_YYYYMMDD_HHMMSS.db database/easy_pass.db

# Откат кода
cd /home/easypass/easy-pass-bot
git checkout <previous-commit>
```

### 3. Запуск сервиса

```bash
sudo systemctl start easy-pass-bot
```

## Устранение неполадок

### Частые проблемы

#### 1. Бот не запускается

```bash
# Проверка логов
sudo journalctl -u easy-pass-bot -n 50

# Проверка прав доступа
ls -la /home/easypass/easy-pass-bot/

# Проверка токена
echo $BOT_TOKEN
```

#### 2. Ошибки базы данных

```bash
# Проверка файла базы данных
ls -la database/easy_pass.db

# Проверка целостности
sqlite3 database/easy_pass.db "PRAGMA integrity_check;"
```

#### 3. Проблемы с памятью

```bash
# Мониторинг памяти
free -h
ps aux --sort=-%mem | head

# Увеличение лимита памяти в systemd
sudo systemctl edit easy-pass-bot
```

### Логи и отладка

```bash
# Просмотр логов в реальном времени
sudo journalctl -u easy-pass-bot -f

# Логи приложения
tail -f logs/bot.log

# Логи Nginx
sudo tail -f /var/log/nginx/easy-pass-bot.error.log
```

## Безопасность

### 1. Настройка файрвола

```bash
# UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 2. Настройка SSH

```bash
# Отключение root логина
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Перезапуск SSH
sudo systemctl restart ssh
```

### 3. Регулярные обновления

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Производительность

### 1. Оптимизация Python

```bash
# Установка оптимизированной версии
pip install --upgrade pip setuptools wheel

# Компиляция с оптимизацией
export PYTHONOPTIMIZE=1
```

### 2. Оптимизация базы данных

```sql
-- Создание индексов
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_passes_car_number ON passes(car_number);
CREATE INDEX idx_passes_status ON passes(status);

-- Анализ производительности
ANALYZE;
```

### 3. Мониторинг ресурсов

```bash
# Установка htop
sudo apt install htop -y

# Мониторинг в реальном времени
htop
```

## Заключение

Это руководство покрывает основные аспекты развертывания Easy Pass Bot. Для получения дополнительной помощи обратитесь к документации разработчика или создайте issue в GitHub репозитории.
