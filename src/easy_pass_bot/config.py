import os
from dotenv import load_dotenv
load_dotenv()
# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/easy_pass.db')
# Роли пользователей
ROLES = {
    'RESIDENT': 'resident',
    'SECURITY': 'security',
    'ADMIN': 'admin'
}
# Статусы пользователей
USER_STATUSES = {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'REJECTED': 'rejected',
    'BLOCKED': 'blocked'
}
# Статусы пропусков
PASS_STATUSES = {
    'ACTIVE': 'active',
    'USED': 'used',
    'CANCELLED': 'cancelled'
}
# Лимиты
MAX_ACTIVE_PASSES = 3
# Настройки кэширования
CACHE_DEFAULT_TTL = 300  # 5 минут
CACHE_MAX_SIZE = 1000
# Настройки повторных попыток
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 60.0
# Настройки Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 30
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2
# Настройки аналитики
ANALYTICS_RETENTION_DAYS = 30
ANALYTICS_BATCH_SIZE = 100
# Настройки подтверждений
CONFIRMATION_TIMEOUT = 300  # 5 минут
CONFIRMATION_CLEANUP_INTERVAL = 60  # 1 минута
# Сообщения
MESSAGES = {
    'WELCOME': """🏠 Добро пожаловать в Easy Pass!
Заполните форму регистрации:
Отправьте сообщение в формате:
ФИО, Телефон, Квартира
Например: Иванов Иван Иванович, +7 900 123 45 67, 15""",
    'REGISTRATION_SENT': "✅ Заявка отправлена на модерацию!",
    'REGISTRATION_APPROVED': "✅ Регистрация одобрена!",
    'REGISTRATION_REJECTED': (
        "❌ Заявка отклонена. Обратитесь к администратору."
    ),
    'PASS_CREATION_REQUEST': """🚗 Подача заявки на пропуск
Введите номер автомобиля:
Например: А123БВ777""",
    'PASS_CREATED': "✅ Заявка создана! Номер: {car_number}",
    'PASS_NOT_FOUND': (
        "❌ Пропуск с номером {car_number} не найден.\n\n"
        "Проверьте правильность номера."
    ),
    'PASS_USED': "✅ Пропуск отмечен как использованный!",
    'INVALID_FORMAT': """❌ Неверный формат.
Отправьте: ФИО, Телефон, Квартира
Например: Иванов Иван Иванович, +7 900 123 45 67, 15""",
    'ALL_FIELDS_REQUIRED': "❌ Все поля обязательны",
    'ENTER_CAR_NUMBER': "❌ Введите номер автомобиля",
    'MAX_PASSES_REACHED': "❌ У вас уже 3 активные заявки",
    'DUPLICATE_PASS': "❌ У вас уже есть заявка с таким номером",
    'NO_RIGHTS': "❌ Нет прав",
    'PASS_ALREADY_USED': "❌ Пропуск уже использован",
    'REQUEST_ALREADY_PROCESSED': "❌ Заявка уже обработана"
}
