# API Документация

## Обзор

Easy Pass Bot предоставляет RESTful API для управления пропусками и пользователями. API построен на основе современных принципов и следует стандартам OpenAPI 3.0.

## Базовый URL

```
https://api.easypassbot.com/v1
```

## Аутентификация

API использует JWT токены для аутентификации. Получите токен через Telegram бота командой `/api_token`.

### Заголовки

```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 500 | Внутренняя ошибка сервера |

## Модели данных

### User (Пользователь)

```json
{
  "id": 1,
  "telegram_id": 123456789,
  "role": "resident",
  "full_name": "Иванов Иван Иванович",
  "phone_number": "+7 900 123 45 67",
  "apartment": "15",
  "status": "approved",
  "created_at": "2025-09-10T19:00:00Z",
  "updated_at": "2025-09-10T19:00:00Z"
}
```

### Pass (Пропуск)

```json
{
  "id": 1,
  "user_id": 1,
  "car_number": "А123БВ777",
  "status": "active",
  "created_at": "2025-09-10T19:00:00Z",
  "used_at": null,
  "used_by_id": null
}
```

## Endpoints

### Пользователи

#### GET /users

Получить список пользователей.

**Параметры запроса:**
- `role` (string, optional) - Фильтр по роли
- `status` (string, optional) - Фильтр по статусу
- `page` (integer, optional) - Номер страницы (по умолчанию 1)
- `limit` (integer, optional) - Количество записей на странице (по умолчанию 20)

**Пример запроса:**
```http
GET /users?role=resident&status=approved&page=1&limit=10
Authorization: Bearer <token>
```

**Пример ответа:**
```json
{
  "data": [
    {
      "id": 1,
      "telegram_id": 123456789,
      "role": "resident",
      "full_name": "Иванов Иван Иванович",
      "phone_number": "+7 900 123 45 67",
      "apartment": "15",
      "status": "approved",
      "created_at": "2025-09-10T19:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

#### GET /users/{id}

Получить пользователя по ID.

**Пример запроса:**
```http
GET /users/1
Authorization: Bearer <token>
```

**Пример ответа:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "role": "resident",
  "full_name": "Иванов Иван Иванович",
  "phone_number": "+7 900 123 45 67",
  "apartment": "15",
  "status": "approved",
  "created_at": "2025-09-10T19:00:00Z"
}
```

#### POST /users

Создать нового пользователя.

**Тело запроса:**
```json
{
  "telegram_id": 123456789,
  "role": "resident",
  "full_name": "Иванов Иван Иванович",
  "phone_number": "+7 900 123 45 67",
  "apartment": "15"
}
```

**Пример ответа:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "role": "resident",
  "full_name": "Иванов Иван Иванович",
  "phone_number": "+7 900 123 45 67",
  "apartment": "15",
  "status": "pending",
  "created_at": "2025-09-10T19:00:00Z"
}
```

#### PUT /users/{id}

Обновить пользователя.

**Тело запроса:**
```json
{
  "role": "security",
  "status": "approved"
}
```

#### DELETE /users/{id}

Удалить пользователя.

### Пропуски

#### GET /passes

Получить список пропусков.

**Параметры запроса:**
- `user_id` (integer, optional) - Фильтр по пользователю
- `status` (string, optional) - Фильтр по статусу
- `car_number` (string, optional) - Поиск по номеру автомобиля
- `page` (integer, optional) - Номер страницы
- `limit` (integer, optional) - Количество записей на странице

**Пример запроса:**
```http
GET /passes?status=active&car_number=А123
Authorization: Bearer <token>
```

#### GET /passes/{id}

Получить пропуск по ID.

#### POST /passes

Создать новый пропуск.

**Тело запроса:**
```json
{
  "user_id": 1,
  "car_number": "А123БВ777"
}
```

#### PUT /passes/{id}/use

Отметить пропуск как использованный.

**Тело запроса:**
```json
{
  "used_by_id": 2
}
```

#### DELETE /passes/{id}

Отменить пропуск.

### Статистика

#### GET /stats/users

Получить статистику пользователей.

**Пример ответа:**
```json
{
  "total": 100,
  "by_role": {
    "resident": 80,
    "security": 5,
    "admin": 2
  },
  "by_status": {
    "approved": 85,
    "pending": 10,
    "rejected": 5
  }
}
```

#### GET /stats/passes

Получить статистику пропусков.

**Пример ответа:**
```json
{
  "total": 500,
  "active": 50,
  "used": 400,
  "cancelled": 50,
  "by_status": {
    "active": 50,
    "used": 400,
    "cancelled": 50
  }
}
```

## Обработка ошибок

### Формат ошибки

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Неверные данные",
    "details": {
      "field": "phone_number",
      "reason": "Неверный формат номера телефона"
    }
  }
}
```

### Коды ошибок

| Код | Описание |
|-----|----------|
| `VALIDATION_ERROR` | Ошибка валидации данных |
| `USER_NOT_FOUND` | Пользователь не найден |
| `PASS_NOT_FOUND` | Пропуск не найден |
| `PERMISSION_DENIED` | Недостаточно прав |
| `RATE_LIMIT_EXCEEDED` | Превышен лимит запросов |
| `INTERNAL_ERROR` | Внутренняя ошибка сервера |

## Rate Limiting

API имеет ограничения на количество запросов:

- **Обычные пользователи**: 100 запросов в час
- **Охранники**: 500 запросов в час
- **Администраторы**: 1000 запросов в час

Заголовки ответа:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Настройка webhook

```http
POST /webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-domain.com/webhook",
  "events": ["user.created", "pass.used"],
  "secret": "your-webhook-secret"
}
```

### События

- `user.created` - Создан новый пользователь
- `user.approved` - Пользователь одобрен
- `user.rejected` - Пользователь отклонен
- `pass.created` - Создан новый пропуск
- `pass.used` - Пропуск использован
- `pass.cancelled` - Пропуск отменен

### Формат webhook

```json
{
  "event": "user.created",
  "timestamp": "2025-09-10T19:00:00Z",
  "data": {
    "user": {
      "id": 1,
      "telegram_id": 123456789,
      "full_name": "Иванов Иван Иванович"
    }
  }
}
```

## SDK

### Python

```python
from easy_pass_bot import EasyPassClient

client = EasyPassClient(api_key="your-api-key")

# Получить пользователей
users = client.users.list(role="resident")

# Создать пропуск
pass_obj = client.passes.create(
    user_id=1,
    car_number="А123БВ777"
)
```

### JavaScript

```javascript
import EasyPassClient from 'easy-pass-bot-js';

const client = new EasyPassClient('your-api-key');

// Получить пользователей
const users = await client.users.list({ role: 'resident' });

// Создать пропуск
const passObj = await client.passes.create({
  user_id: 1,
  car_number: 'А123БВ777'
});
```

## Примеры использования

### Полный цикл работы с пропуском

```python
# 1. Создать пользователя
user = client.users.create({
    "telegram_id": 123456789,
    "role": "resident",
    "full_name": "Иванов Иван Иванович",
    "phone_number": "+7 900 123 45 67",
    "apartment": "15"
})

# 2. Одобрить пользователя
client.users.update(user.id, {"status": "approved"})

# 3. Создать пропуск
pass_obj = client.passes.create({
    "user_id": user.id,
    "car_number": "А123БВ777"
})

# 4. Найти пропуск
passes = client.passes.list(car_number="А123")

# 5. Отметить как использованный
client.passes.use(pass_obj.id, {"used_by_id": 2})
```

## Changelog

### v1.0.0 (2025-09-10)
- Первый релиз API
- Базовые CRUD операции для пользователей и пропусков
- JWT аутентификация
- Rate limiting
- Webhooks

## Поддержка

- **Документация**: [docs.easypassbot.com](https://docs.easypassbot.com)
- **Поддержка**: support@easypassbot.com
- **GitHub**: [github.com/merdocx/easy-pass-bot](https://github.com/merdocx/easy-pass-bot)




