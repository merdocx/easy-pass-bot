-- 🗄️ Примеры SQL запросов для работы с пропусками

-- 📊 1. Основные запросы для анализа данных

-- Общее количество пропусков
SELECT COUNT(*) as total_passes FROM passes;

-- Количество пропусков по статусам
SELECT status, COUNT(*) as count 
FROM passes 
GROUP BY status 
ORDER BY count DESC;

-- Топ-10 пользователей по количеству пропусков
SELECT u.full_name, u.apartment, COUNT(p.id) as pass_count
FROM users u 
JOIN passes p ON u.id = p.user_id 
GROUP BY u.id, u.full_name, u.apartment
ORDER BY pass_count DESC 
LIMIT 10;

-- 📅 2. Запросы по датам

-- Пропуски за последние 30 дней
SELECT COUNT(*) as recent_passes
FROM passes 
WHERE created_at >= datetime('now', '-30 days');

-- Использованные пропуски за последнюю неделю
SELECT COUNT(*) as used_this_week
FROM passes 
WHERE status = 'used' 
AND used_at >= datetime('now', '-7 days');

-- Среднее время между созданием и использованием пропуска
SELECT AVG(
    (julianday(used_at) - julianday(created_at)) * 24
) as avg_hours_to_use
FROM passes 
WHERE status = 'used' AND used_at IS NOT NULL;

-- 🚗 3. Анализ автомобилей

-- Самые популярные номера автомобилей
SELECT car_number, COUNT(*) as usage_count
FROM passes 
GROUP BY car_number 
ORDER BY usage_count DESC 
LIMIT 10;

-- Пропуски по номерам автомобилей (формат)
SELECT 
    CASE 
        WHEN car_number LIKE 'А%' THEN 'А-серия'
        WHEN car_number LIKE 'В%' THEN 'В-серия'
        WHEN car_number LIKE 'Е%' THEN 'Е-серия'
        WHEN car_number LIKE 'К%' THEN 'К-серия'
        WHEN car_number LIKE 'Н%' THEN 'Н-серия'
        WHEN car_number LIKE 'Р%' THEN 'Р-серия'
        WHEN car_number LIKE 'У%' THEN 'У-серия'
        WHEN car_number LIKE 'Ц%' THEN 'Ц-серия'
        WHEN car_number LIKE 'Ю%' THEN 'Ю-серия'
        WHEN car_number LIKE 'Я%' THEN 'Я-серия'
        ELSE 'Другие'
    END as series,
    COUNT(*) as count
FROM passes 
GROUP BY series 
ORDER BY count DESC;

-- 👥 4. Анализ пользователей

-- Активность пользователей по ролям
SELECT u.role, COUNT(p.id) as total_passes,
       COUNT(CASE WHEN p.status = 'active' THEN 1 END) as active_passes,
       COUNT(CASE WHEN p.status = 'used' THEN 1 END) as used_passes,
       COUNT(CASE WHEN p.status = 'cancelled' THEN 1 END) as cancelled_passes
FROM users u 
LEFT JOIN passes p ON u.id = p.user_id 
GROUP BY u.role;

-- Пользователи без пропусков
SELECT u.full_name, u.phone_number, u.apartment
FROM users u 
LEFT JOIN passes p ON u.id = p.user_id 
WHERE p.id IS NULL 
AND u.status = 'approved';

-- 🔍 5. Поисковые запросы

-- Поиск пропусков по номеру автомобиля
SELECT p.*, u.full_name, u.phone_number
FROM passes p 
JOIN users u ON p.user_id = u.id 
WHERE p.car_number LIKE '%123%';

-- Поиск пропусков по владельцу
SELECT p.*, u.full_name, u.phone_number
FROM passes p 
JOIN users u ON p.user_id = u.id 
WHERE u.full_name LIKE '%Иван%';

-- Поиск пропусков по дате создания
SELECT p.*, u.full_name
FROM passes p 
JOIN users u ON p.user_id = u.id 
WHERE DATE(p.created_at) = '2025-09-12';

-- 📈 6. Статистические запросы

-- Статистика по дням недели
SELECT 
    CASE CAST(strftime('%w', created_at) AS INTEGER)
        WHEN 0 THEN 'Воскресенье'
        WHEN 1 THEN 'Понедельник'
        WHEN 2 THEN 'Вторник'
        WHEN 3 THEN 'Среда'
        WHEN 4 THEN 'Четверг'
        WHEN 5 THEN 'Пятница'
        WHEN 6 THEN 'Суббота'
    END as day_of_week,
    COUNT(*) as pass_count
FROM passes 
GROUP BY strftime('%w', created_at)
ORDER BY strftime('%w', created_at);

-- Статистика по часам дня
SELECT 
    strftime('%H', created_at) as hour,
    COUNT(*) as pass_count
FROM passes 
GROUP BY strftime('%H', created_at)
ORDER BY hour;

-- 📋 7. Административные запросы

-- Архивирование старых использованных пропусков
UPDATE passes 
SET is_archived = 1 
WHERE status = 'used' 
AND used_at < datetime('now', '-90 days');

-- Поиск дублирующихся номеров автомобилей
SELECT car_number, COUNT(*) as count
FROM passes 
GROUP BY car_number 
HAVING COUNT(*) > 1;

-- Очистка отмененных пропусков старше 30 дней
DELETE FROM passes 
WHERE status = 'cancelled' 
AND created_at < datetime('now', '-30 days');

-- 🔧 8. Примеры создания пропусков

-- Создание нового пропуска
INSERT INTO passes (user_id, car_number, status, created_at, is_archived)
VALUES (1, 'А123БВ777', 'active', datetime('now'), 0);

-- Отметка пропуска как использованного
UPDATE passes 
SET status = 'used', 
    used_at = datetime('now'),
    used_by_id = 2
WHERE id = 1;

-- Отмена пропуска
UPDATE passes 
SET status = 'cancelled' 
WHERE id = 1;

-- 📊 9. Отчеты для админки

-- Ежедневный отчет по пропускам
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_created,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
    COUNT(CASE WHEN status = 'used' THEN 1 END) as used,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled
FROM passes 
WHERE created_at >= datetime('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Отчет по использованию пропусков
SELECT 
    DATE(used_at) as date,
    COUNT(*) as used_count,
    COUNT(DISTINCT used_by_id) as unique_users
FROM passes 
WHERE status = 'used' 
AND used_at >= datetime('now', '-30 days')
GROUP BY DATE(used_at)
ORDER BY date DESC;
