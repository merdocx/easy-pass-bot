import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from .models import User, Pass
from ..config import DATABASE_PATH, PASS_STATUSES
from ..services.cache_service import cache_service
from ..services.retry_service import retry_service
from ..core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Создание таблицы пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (
                        role IN ('resident', 'security', 'admin')
                    ),
                    full_name VARCHAR(255) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    apartment VARCHAR(10) NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
                        status IN ('pending', 'approved', 'rejected')
                    ),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Создание таблицы пропусков
            await db.execute("""
                CREATE TABLE IF NOT EXISTS passes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    car_number VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
                        status IN ('active', 'used', 'cancelled')
                    ),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    used_at TIMESTAMP NULL,
                    used_by_id INTEGER NULL,
                    is_archived BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (used_by_id) REFERENCES users(id)
                )
            """)
            # Создание индексов
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id "
                "ON users(telegram_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_role "
                "ON users(role)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_status "
                "ON users(status)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_passes_user_id "
                "ON passes(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_passes_status "
                "ON passes(status)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_passes_car_number "
                "ON passes(car_number)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_passes_created_at "
                "ON passes(created_at)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_passes_is_archived "
                "ON passes(is_archived)"
            )
            await db.commit()
            logger.info("Database initialized successfully")

    async def create_user(self, user: User) -> int:
        """Создание пользователя с инвалидацией кэша"""
        try:
            user_id = await retry_service.execute_with_retry(
                self._create_user_internal, user
            )
            # Инвалидируем кэш пользователей
            await cache_service.invalidate_pattern("user_.*")
            return user_id
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {e}")

    async def _create_user_internal(self, user: User) -> int:
        """Внутренний метод создания пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO users (
                    telegram_id, role, full_name, phone_number,
                    apartment, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.telegram_id, user.role, user.full_name,
                user.phone_number, user.apartment, user.status,
                datetime.now(), datetime.now()
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_user_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[User]:
        """Получение пользователя по Telegram ID с кэшированием"""
        cache_key = f"user_telegram_id:{telegram_id}"
        # Пытаемся получить из кэша
        cached_user = await cache_service.get(cache_key)
        if cached_user is not None:
            return cached_user
        # Если не в кэше, получаем из базы данных
        try:
            user = await retry_service.execute_with_retry(
                self._get_user_by_telegram_id_internal, telegram_id
            )
            # Сохраняем в кэш на 5 минут
            if user:
                await cache_service.set(cache_key, user, ttl=300)
            return user
        except Exception as e:
            raise DatabaseError(f"Failed to get user by telegram_id {telegram_id}: {e}")
    async def _get_user_by_telegram_id_internal(self, telegram_id: int) -> Optional[User]:
        """Внутренний метод получения пользователя по Telegram ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users WHERE telegram_id = ?
            """, (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    )
                return None
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users WHERE id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    )
                return None
    async def update_user_status(self, user_id: int, status: str):
        """Обновление статуса пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET status = ?, updated_at = ? WHERE id = ?
            """, (status, datetime.now(), user_id))
            await db.commit()
    
    async def block_user(self, user_id: int, blocked_until: str, block_reason: str):
        """Блокировка пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET status = 'blocked', blocked_until = ?, block_reason = ?, updated_at = ? WHERE id = ?
            """, (blocked_until, block_reason, datetime.now(), user_id))
            await db.commit()
    
    async def unblock_user(self, user_id: int):
        """Разблокировка пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET status = 'approved', blocked_until = NULL, block_reason = NULL, updated_at = ? WHERE id = ?
            """, (datetime.now(), user_id))
            await db.commit()
    
    async def delete_user(self, user_id: int):
        """Удаление пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала удаляем все пропуски пользователя
            await db.execute("DELETE FROM passes WHERE user_id = ?", (user_id,))
            # Затем удаляем самого пользователя
            await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await db.commit()
    async def get_admin_users(self) -> List[User]:
        """Получение всех администраторов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users WHERE role = 'admin' AND status = 'approved'
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    ) for row in rows
                ]
    async def get_pending_users(self) -> List[User]:
        """Получение пользователей на модерации"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users WHERE role = 'resident' AND status = 'pending'
                ORDER BY created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    ) for row in rows
                ]
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    ) for row in rows
                ]
    async def create_pass(self, pass_obj: Pass) -> int:
        """Создание пропуска"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO passes (user_id, car_number, status, created_at, is_archived)
                VALUES (?, ?, ?, ?, ?)
            """, (pass_obj.user_id, pass_obj.car_number, pass_obj.status, datetime.now(), pass_obj.is_archived))
            await db.commit()
            return cursor.lastrowid
    async def get_pass_by_id(self, pass_id: int) -> Optional[Pass]:
        """Получение пропуска по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes WHERE id = ?
            """, (pass_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=row[4], used_at=row[5], used_by_id=row[6], is_archived=bool(row[7])
                    )
                return None
    async def update_pass_status(self, pass_id: int, status: str, used_by_id: int = None) -> bool:
        """Обновление статуса пропуска"""
        async with aiosqlite.connect(self.db_path) as db:
            if status == PASS_STATUSES['USED']:
                await db.execute("""
                    UPDATE passes
                    SET status = ?, used_at = datetime('now'), used_by_id = ?
                    WHERE id = ?
                """, (status, used_by_id, pass_id))
            else:
                await db.execute("""
                    UPDATE passes
                    SET status = ?
                    WHERE id = ?
                """, (status, pass_id))
            await db.commit()
            return True
    async def find_pass_by_car_number(self, car_number: str) -> Optional[Pass]:
        """Поиск пропуска по номеру автомобиля (возвращает первый найденный)"""
        from datetime import datetime
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes WHERE car_number LIKE ? AND status = 'active' AND is_archived = 0
                ORDER BY created_at DESC LIMIT 1
            """, (f"%{car_number}%",)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Преобразуем строки дат в объекты datetime
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    return Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    )
                return None
    async def find_all_passes_by_car_number(self, car_number: str) -> List[Pass]:
        """Поиск всех пропусков по номеру автомобиля"""
        from datetime import datetime
        passes = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes WHERE car_number LIKE ? AND status = 'active' AND is_archived = 0
                ORDER BY created_at DESC
            """, (f"%{car_number}%",)) as cursor:
                async for row in cursor:
                    # Преобразуем строки дат в объекты datetime
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    ))
        return passes
    async def get_user_passes(self, user_id: int) -> List[Pass]:
        """Получение пропусков пользователя (исключая архивные)"""
        from datetime import datetime
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes WHERE user_id = ? AND is_archived = 0
                ORDER BY created_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                passes = []
                for row in rows:
                    # Преобразуем строки дат в объекты datetime
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    ))
                return passes
    async def count_active_passes(self, user_id: int) -> int:
        """Подсчет активных пропусков пользователя (исключая архивные)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM passes WHERE user_id = ? AND status = 'active' AND is_archived = 0
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    async def check_duplicate_pass(self, user_id: int, car_number: str) -> bool:
        """Проверка дублирования пропуска (исключая архивные)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM passes WHERE user_id = ? AND car_number = ? AND status = 'active' AND is_archived = 0
            """, (user_id, car_number)) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False
    async def mark_pass_as_used(self, pass_id: int, used_by_id: int):
        """Отметка пропуска как использованного"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE passes SET status = 'used', used_at = ?, used_by_id = ? WHERE id = ?
            """, (datetime.now(), used_by_id, pass_id))
            await db.commit()
    
    async def archive_pass(self, pass_id: int) -> bool:
        """Переместить пропуск в архив"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE passes SET is_archived = 1 WHERE id = ?
            """, (pass_id,))
            await db.commit()
            return True
    
    async def get_passes_for_archiving(self) -> List[Pass]:
        """Получить пропуски для архивации"""
        from datetime import datetime, timedelta
        passes = []
        now = datetime.now()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Использованные пропуски старше 24 часов
            used_cutoff = now - timedelta(hours=24)
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes 
                WHERE status = 'used' AND used_at < ? AND is_archived = 0
            """, (used_cutoff,)) as cursor:
                async for row in cursor:
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    ))
            
            # Неиспользованные пропуски старше 7 дней
            unused_cutoff = now - timedelta(days=7)
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes 
                WHERE status = 'active' AND created_at < ? AND is_archived = 0
            """, (unused_cutoff,)) as cursor:
                async for row in cursor:
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    ))
        
        return passes
    
    async def get_all_passes(self) -> List[Pass]:
        """Получить все пропуски (включая архивные) - для административных целей"""
        from datetime import datetime
        passes = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id, is_archived
                FROM passes
                ORDER BY created_at DESC
            """) as cursor:
                async for row in cursor:
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6], is_archived=bool(row[7])
                    ))
        return passes

    async def get_users_paginated(
        self, 
        page: int = 1, 
        per_page: int = 20,
        search: str = None,
        status_filter: str = None,
        role_filter: str = None,
        id_filter: str = None,
        telegram_id_filter: str = None,
        full_name_filter: str = None,
        phone_filter: str = None,
        apartment_filter: str = None,
        created_date_filter: str = None
    ) -> Tuple[List[User], int]:
        """Получение пользователей с пагинацией и фильтрацией по столбцам"""
        offset = (page - 1) * per_page
        
        # Строим WHERE условия
        where_conditions = []
        params = []
        
        # Общий поиск (совместимость)
        if search:
            where_conditions.append("(full_name LIKE ? OR telegram_id LIKE ? OR phone_number LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Фильтры по конкретным столбцам
        if id_filter:
            where_conditions.append("id LIKE ?")
            params.append(f"%{id_filter}%")
        
        if telegram_id_filter:
            where_conditions.append("telegram_id LIKE ?")
            params.append(f"%{telegram_id_filter}%")
        
        if full_name_filter:
            where_conditions.append("full_name LIKE ?")
            params.append(f"%{full_name_filter}%")
        
        if phone_filter:
            where_conditions.append("phone_number LIKE ?")
            params.append(f"%{phone_filter}%")
        
        if apartment_filter:
            where_conditions.append("apartment LIKE ?")
            params.append(f"%{apartment_filter}%")
        
        if status_filter:
            where_conditions.append("status = ?")
            params.append(status_filter)
        
        if role_filter:
            where_conditions.append("role = ?")
            params.append(role_filter)
        
        if created_date_filter:
            where_conditions.append("DATE(created_at) = ?")
            params.append(created_date_filter)
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем общее количество записей
            count_query = f"SELECT COUNT(*) FROM users{where_clause}"
            async with db.execute(count_query, params) as cursor:
                total_count = (await cursor.fetchone())[0]
            
            # Получаем данные с пагинацией
            query = f"""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, blocked_until, block_reason, created_at, updated_at
                FROM users{where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                users = [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        blocked_until=row[7], block_reason=row[8],
                        created_at=row[9], updated_at=row[10]
                    ) for row in rows
                ]
                
                return users, total_count

    async def get_passes_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str = None,
        status_filter: str = None,
        id_filter: str = None,
        car_number_filter: str = None,
        owner_filter: str = None,
        phone_filter: str = None,
        apartment_filter: str = None,
        created_date_filter: str = None,
        used_date_filter: str = None
    ) -> Tuple[List[Pass], int]:
        """Получение пропусков с пагинацией и фильтрацией по столбцам"""
        offset = (page - 1) * per_page
        
        # Строим WHERE условия
        where_conditions = []
        params = []
        
        # Общий поиск (совместимость)
        if search:
            where_conditions.append("car_number LIKE ?")
            params.append(f"%{search}%")
        
        # Фильтры по конкретным столбцам
        if id_filter:
            where_conditions.append("p.id LIKE ?")
            params.append(f"%{id_filter}%")
        
        if car_number_filter:
            where_conditions.append("p.car_number LIKE ?")
            params.append(f"%{car_number_filter}%")
        
        if owner_filter:
            where_conditions.append("u.full_name LIKE ?")
            params.append(f"%{owner_filter}%")
        
        if phone_filter:
            where_conditions.append("u.phone_number LIKE ?")
            params.append(f"%{phone_filter}%")
        
        if apartment_filter:
            where_conditions.append("u.apartment LIKE ?")
            params.append(f"%{apartment_filter}%")
        
        if status_filter:
            where_conditions.append("p.status = ?")
            params.append(status_filter)
        
        if created_date_filter:
            where_conditions.append("DATE(p.created_at) = ?")
            params.append(created_date_filter)
        
        if used_date_filter:
            where_conditions.append("DATE(p.used_at) = ?")
            params.append(used_date_filter)
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем общее количество записей
            # Используем JOIN если есть фильтры по пользователям
            if owner_filter or phone_filter or apartment_filter:
                count_query = f"""
                    SELECT COUNT(*) 
                    FROM passes p 
                    JOIN users u ON p.user_id = u.id{where_clause}
                """
            else:
                count_query = f"SELECT COUNT(*) FROM passes p{where_clause}"
            
            async with db.execute(count_query, params) as cursor:
                total_count = (await cursor.fetchone())[0]
            
            # Получаем данные с пагинацией
            # Используем JOIN если есть фильтры по пользователям
            if owner_filter or phone_filter or apartment_filter:
                query = f"""
                    SELECT p.id, p.user_id, p.car_number, p.status, p.created_at, p.used_at, p.used_by_id, p.is_archived
                    FROM passes p 
                    JOIN users u ON p.user_id = u.id{where_clause}
                    ORDER BY p.created_at DESC
                    LIMIT ? OFFSET ?
                """
            else:
                query = f"""
                    SELECT p.id, p.user_id, p.car_number, p.status, p.created_at, p.used_at, p.used_by_id, p.is_archived
                    FROM passes p{where_clause}
                    ORDER BY p.created_at DESC
                    LIMIT ? OFFSET ?
                """
            
            params.extend([per_page, offset])
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                passes = [
                    Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=row[4], used_at=row[5], used_by_id=row[6], is_archived=bool(row[7])
                    ) for row in rows
                ]
                
                return passes, total_count

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username (для админки)"""
        try:
            # Для админки username = "admin", ищем пользователя с ролью admin
            if username == "admin":
                async with aiosqlite.connect(self.db_path) as db:
                    async with db.execute(
                        "SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at FROM users WHERE role = 'admin' LIMIT 1",
                        ()
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            return User(
                                id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                                phone_number=row[4], apartment=row[5], status=row[6],
                                created_at=row[7], updated_at=row[8]
                            )
            else:
                # Для других пользователей ищем по full_name
                async with aiosqlite.connect(self.db_path) as db:
                    async with db.execute(
                        "SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at FROM users WHERE full_name = ?",
                        (username,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            return User(
                                id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                                phone_number=row[4], apartment=row[5], status=row[6],
                                created_at=row[7], updated_at=row[8]
                            )
            return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    async def change_user_role(self, user_id: int, new_role: str) -> bool:
        """Изменить роль пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_role, user_id)
                )
                await db.commit()
                
                # Инвалидируем кэш
                cache_service.invalidate_user_cache(user_id)
                
                logger.info(f"User {user_id} role changed to {new_role}")
                return True
        except Exception as e:
            logger.error(f"Error changing user {user_id} role to {new_role}: {e}")
            return False

    async def cleanup(self):
        """Очистка ресурсов базы данных"""
        # Закрываем все соединения
        pass

# Глобальный экземпляр базы данных
db = Database()
