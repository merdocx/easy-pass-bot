# 🗄️ Структура базы данных PM Desk

## 📊 Общая схема базы данных

```
┌─────────────────┐    ┌─────────────────┐
│      USERS      │    │      PASSES     │
├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │
│ telegram_id     │◄───┤ user_id (FK)    │
│ role            │    │ car_number      │
│ full_name       │    │ status          │
│ phone_number    │    │ created_at      │
│ apartment       │    │ used_at         │
│ status          │    │ used_by_id (FK) │
│ is_admin        │    │ is_archived     │
│ password_hash   │    └─────────────────┘
│ created_at      │
│ updated_at      │
│ blocked_until   │
│ block_reason    │
└─────────────────┘
```

## 🔗 Связи между таблицами

### PASSES → USERS
- `user_id` → `users.id` (владелец пропуска)
- `used_by_id` → `users.id` (кто использовал пропуск)

## 📋 Детальная структура таблицы USERS

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор пользователя |
| `telegram_id` | BIGINT | UNIQUE NOT NULL | Telegram ID пользователя |
| `role` | VARCHAR(20) | NOT NULL | Роль: 'resident', 'security', 'admin' |
| `full_name` | VARCHAR(255) | NOT NULL | Полное имя пользователя |
| `phone_number` | VARCHAR(20) | NOT NULL | Номер телефона (нормализованный) |
| `apartment` | VARCHAR(10) | NULL | Номер квартиры |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Статус: 'pending', 'approved', 'rejected', 'blocked' |
| `is_admin` | BOOLEAN | NOT NULL, DEFAULT 0 | Флаг администратора |
| `password_hash` | VARCHAR(255) | NULL | Хеш пароля для веб-админки |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Дата создания |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Дата обновления |
| `blocked_until` | TEXT | NULL | Дата окончания блокировки |
| `block_reason` | TEXT | NULL | Причина блокировки |

## 📋 Детальная структура таблицы PASSES

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор пропуска |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY | ID владельца пропуска (ссылка на users.id) |
| `car_number` | VARCHAR(20) | NOT NULL | Номер автомобиля |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Статус пропуска: 'active', 'used', 'cancelled' |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Дата создания пропуска |
| `used_at` | TIMESTAMP | NULL | Дата использования пропуска |
| `used_by_id` | INTEGER | NULL, FOREIGN KEY | ID пользователя, который использовал пропуск |
| `is_archived` | BOOLEAN | NOT NULL, DEFAULT 0 | Флаг архивирования пропуска |

## 🎯 Индексы для оптимизации

```sql
CREATE INDEX idx_passes_user_id ON passes(user_id);
CREATE INDEX idx_passes_status ON passes(status);
CREATE INDEX idx_passes_car_number ON passes(car_number);
CREATE INDEX idx_passes_created_at ON passes(created_at);
CREATE INDEX idx_passes_is_archived ON passes(is_archived);
```

## 📊 Возможные статусы пропусков

| Статус | Описание | Когда устанавливается |
|--------|----------|----------------------|
| `active` | Активный | При создании пропуска |
| `used` | Использован | Когда пропуск был использован для проезда |
| `cancelled` | Отменен | Когда пропуск был отменен администратором |

## 🔄 Жизненный цикл пропуска

```
Создание → active → used (при использовании)
    ↓
cancelled (при отмене)
    ↓
archived (при архивировании)
```

## 📈 Варианты наполнения базы данных

### 1. Тестовые данные для разработки
- Создать пропуски для всех существующих пользователей
- Разнообразные статусы (active, used, cancelled)
- Различные даты создания и использования

### 2. Демонстрационные данные
- Реалистичные номера автомобилей
- Логичная временная последовательность
- Различные сценарии использования

### 3. Стресс-тестирование
- Большое количество пропусков
- Множественные пропуски для одного пользователя
- Пропуски с различными статусами

### 4. Продакшн данные
- Реальные данные пользователей
- Актуальные номера автомобилей
- Корректные временные метки
