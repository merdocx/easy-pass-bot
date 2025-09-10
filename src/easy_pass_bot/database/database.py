import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional
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
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users WHERE telegram_id = ?
            """, (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    )
                return None
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users WHERE id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    )
                return None
    async def update_user_status(self, user_id: int, status: str):
        """Обновление статуса пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET status = ?, updated_at = ? WHERE id = ?
            """, (status, datetime.now(), user_id))
            await db.commit()
    async def get_admin_users(self) -> List[User]:
        """Получение всех администраторов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users WHERE role = 'admin' AND status = 'approved'
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    ) for row in rows
                ]
    async def get_pending_users(self) -> List[User]:
        """Получение пользователей на модерации"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users WHERE role = 'resident' AND status = 'pending'
                ORDER BY created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    ) for row in rows
                ]
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    ) for row in rows
                ]
    async def create_pass(self, pass_obj: Pass) -> int:
        """Создание пропуска"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO passes (user_id, car_number, status, created_at)
                VALUES (?, ?, ?, ?)
            """, (pass_obj.user_id, pass_obj.car_number, pass_obj.status, datetime.now()))
            await db.commit()
            return cursor.lastrowid
    async def get_pass_by_id(self, pass_id: int) -> Optional[Pass]:
        """Получение пропуска по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id
                FROM passes WHERE id = ?
            """, (pass_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=row[4], used_at=row[5], used_by_id=row[6]
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
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id
                FROM passes WHERE car_number LIKE ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (f"%{car_number}%",)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Преобразуем строки дат в объекты datetime
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    return Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6]
                    )
                return None
    async def find_all_passes_by_car_number(self, car_number: str) -> List[Pass]:
        """Поиск всех пропусков по номеру автомобиля"""
        from datetime import datetime
        passes = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id
                FROM passes WHERE car_number LIKE ? AND status = 'active'
                ORDER BY created_at DESC
            """, (f"%{car_number}%",)) as cursor:
                async for row in cursor:
                    # Преобразуем строки дат в объекты datetime
                    created_at = datetime.fromisoformat(row[4]) if row[4] else None
                    used_at = datetime.fromisoformat(row[5]) if row[5] else None
                    passes.append(Pass(
                        id=row[0], user_id=row[1], car_number=row[2], status=row[3],
                        created_at=created_at, used_at=used_at, used_by_id=row[6]
                    ))
        return passes
    async def get_user_passes(self, user_id: int) -> List[Pass]:
        """Получение пропусков пользователя"""
        from datetime import datetime
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id
                FROM passes WHERE user_id = ?
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
                        created_at=created_at, used_at=used_at, used_by_id=row[6]
                    ))
                return passes
    async def count_active_passes(self, user_id: int) -> int:
        """Подсчет активных пропусков пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM passes WHERE user_id = ? AND status = 'active'
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    async def check_duplicate_pass(self, user_id: int, car_number: str) -> bool:
        """Проверка дублирования пропуска"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM passes WHERE user_id = ? AND car_number = ? AND status = 'active'
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
# Глобальный экземпляр базы данных
db = Database()
