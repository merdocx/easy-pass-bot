# 🗄️ Структура базы данных Easy Pass Bot

## 📊 Общая схема базы данных

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      USERS      │    │      PASSES     │    │      ADMINS     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ telegram_id     │◄───┤ user_id (FK)    │    │ username        │
│ role            │    │ car_number      │    │ email           │
│ full_name       │    │ status          │    │ full_name       │
│ phone_number    │    │ created_at      │    │ password_hash   │
│ apartment       │    │ used_at         │    │ role            │
│ status          │    │ used_by_id (FK) │    │ is_active       │
│ created_at      │    │ is_archived     │    │ created_at      │
│ updated_at      │    └─────────────────┘    │ updated_at      │
│ blocked_until   │                           │ last_login      │
│ block_reason    │                           └─────────────────┘
└─────────────────┘
```

## 🔗 Связи между таблицами

### PASSES → USERS
- `user_id` → `users.id` (владелец пропуска)
- `used_by_id` → `users.id` (кто использовал пропуск)

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
