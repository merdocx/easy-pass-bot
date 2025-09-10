"""
Тесты для сервиса архивации
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.easy_pass_bot.services.archive_service import ArchiveService
from src.easy_pass_bot.database.models import Pass
from src.easy_pass_bot.core.interfaces import IPassRepository


class MockPassRepository(IPassRepository):
    """Мок репозитория пропусков для тестирования"""
    
    def __init__(self):
        self.passes = []
        self.next_id = 1
    
    async def create(self, entity: Pass) -> int:
        entity.id = self.next_id
        self.next_id += 1
        self.passes.append(entity)
        return entity.id
    
    async def get_by_id(self, entity_id: int) -> Pass:
        for pass_obj in self.passes:
            if pass_obj.id == entity_id:
                return pass_obj
        return None
    
    async def update(self, entity: Pass) -> bool:
        for i, pass_obj in enumerate(self.passes):
            if pass_obj.id == entity.id:
                self.passes[i] = entity
                return True
        return False
    
    async def delete(self, entity_id: int) -> bool:
        for i, pass_obj in enumerate(self.passes):
            if pass_obj.id == entity_id:
                del self.passes[i]
                return True
        return False
    
    async def get_by_car_number(self, car_number: str) -> list:
        return [p for p in self.passes if p.car_number == car_number]
    
    async def get_user_passes(self, user_id: int) -> list:
        return [p for p in self.passes if p.user_id == user_id and not p.is_archived]
    
    async def mark_as_used(self, pass_id: int, used_by_id: int) -> bool:
        for pass_obj in self.passes:
            if pass_obj.id == pass_id:
                pass_obj.status = 'used'
                pass_obj.used_at = datetime.now()
                pass_obj.used_by_id = used_by_id
                return True
        return False
    
    async def get_all(self) -> list:
        return self.passes.copy()
    
    async def archive_pass(self, pass_id: int) -> bool:
        for pass_obj in self.passes:
            if pass_obj.id == pass_id:
                pass_obj.is_archived = True
                return True
        return False
    
    async def get_passes_for_archiving(self) -> list:
        now = datetime.now()
        passes_to_archive = []
        
        for pass_obj in self.passes:
            if pass_obj.is_archived:
                continue
                
            # Использованные пропуски старше 24 часов
            if (pass_obj.status == 'used' and 
                pass_obj.used_at and 
                pass_obj.used_at < now - timedelta(hours=24)):
                passes_to_archive.append(pass_obj)
            
            # Неиспользованные пропуски старше 7 дней
            elif (pass_obj.status == 'active' and 
                  pass_obj.created_at and 
                  pass_obj.created_at < now - timedelta(days=7)):
                passes_to_archive.append(pass_obj)
        
        return passes_to_archive


@pytest.fixture
def mock_repository():
    """Фикстура для мок-репозитория"""
    return MockPassRepository()


@pytest.fixture
def archive_service(mock_repository):
    """Фикстура для сервиса архивации"""
    logger = MagicMock()
    error_handler = MagicMock()
    return ArchiveService(
        pass_repository=mock_repository,
        logger=logger,
        error_handler=error_handler
    )


@pytest.fixture
def sample_passes():
    """Фикстура с тестовыми пропусками"""
    now = datetime.now()
    
    # Активный пропуск (недавно созданный)
    recent_pass = Pass(
        id=1,
        user_id=1,
        car_number="A123BC",
        status="active",
        created_at=now - timedelta(hours=1),
        is_archived=False
    )
    
    # Использованный пропуск (старше 24 часов)
    old_used_pass = Pass(
        id=2,
        user_id=2,
        car_number="B456DE",
        status="used",
        created_at=now - timedelta(days=2),
        used_at=now - timedelta(hours=25),
        used_by_id=3,
        is_archived=False
    )
    
    # Активный пропуск (старше 7 дней)
    old_active_pass = Pass(
        id=3,
        user_id=3,
        car_number="C789FG",
        status="active",
        created_at=now - timedelta(days=8),
        is_archived=False
    )
    
    # Уже архивный пропуск
    archived_pass = Pass(
        id=4,
        user_id=4,
        car_number="D012HI",
        status="used",
        created_at=now - timedelta(days=10),
        used_at=now - timedelta(days=5),
        used_by_id=3,
        is_archived=True
    )
    
    return [recent_pass, old_used_pass, old_active_pass, archived_pass]


@pytest.mark.asyncio
async def test_archive_old_passes(archive_service, mock_repository, sample_passes):
    """Тест архивации старых пропусков"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Выполняем архивацию
    archived_count = await archive_service.archive_old_passes()
    
    # Проверяем, что архивировались правильные пропуски
    assert archived_count == 2  # old_used_pass и old_active_pass
    
    # Проверяем, что пропуски действительно архивированы
    old_used_pass = next(p for p in mock_repository.passes if p.id == 2)
    old_active_pass = next(p for p in mock_repository.passes if p.id == 3)
    
    assert old_used_pass.is_archived == True
    assert old_active_pass.is_archived == True
    
    # Проверяем, что недавний пропуск не архивирован
    recent_pass = next(p for p in mock_repository.passes if p.id == 1)
    assert recent_pass.is_archived == False


@pytest.mark.asyncio
async def test_get_archived_passes(archive_service, mock_repository, sample_passes):
    """Тест получения архивных пропусков"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Получаем архивные пропуски
    archived_passes = await archive_service.get_archived_passes()
    
    # Проверяем, что возвращаются только архивные пропуски
    assert len(archived_passes) == 1
    assert archived_passes[0].id == 4
    assert archived_passes[0].is_archived == True


@pytest.mark.asyncio
async def test_get_archive_statistics(archive_service, mock_repository, sample_passes):
    """Тест получения статистики архива"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Получаем статистику
    stats = await archive_service.get_archive_statistics()
    
    # Проверяем статистику
    assert stats['total_passes'] == 4
    assert stats['archived_count'] == 1
    assert stats['active_count'] == 3
    assert 'archived_by_status' in stats
    assert 'archived_by_month' in stats


@pytest.mark.asyncio
async def test_restore_pass(archive_service, mock_repository, sample_passes):
    """Тест восстановления пропуска из архива"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Восстанавливаем архивный пропуск
    success = await archive_service.restore_pass(4)
    
    # Проверяем успешность операции
    assert success == True
    
    # Проверяем, что пропуск больше не архивирован
    restored_pass = next(p for p in mock_repository.passes if p.id == 4)
    assert restored_pass.is_archived == False


@pytest.mark.asyncio
async def test_restore_non_archived_pass(archive_service, mock_repository, sample_passes):
    """Тест попытки восстановить неархивный пропуск"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Пытаемся восстановить неархивный пропуск
    with pytest.raises(Exception, match="Pass is not archived"):
        await archive_service.restore_pass(1)


@pytest.mark.asyncio
async def test_restore_nonexistent_pass(archive_service, mock_repository):
    """Тест попытки восстановить несуществующий пропуск"""
    # Пытаемся восстановить несуществующий пропуск
    with pytest.raises(Exception, match="Pass with ID 999 not found"):
        await archive_service.restore_pass(999)


@pytest.mark.asyncio
async def test_permanently_delete_archived_passes(archive_service, mock_repository, sample_passes):
    """Тест постоянного удаления старых архивных пропусков"""
    # Добавляем тестовые пропуски в репозиторий
    for pass_obj in sample_passes:
        mock_repository.passes.append(pass_obj)
    
    # Удаляем архивные пропуски старше 1 дня
    deleted_count = await archive_service.permanently_delete_archived_passes(older_than_days=1)
    
    # Проверяем, что удалился только один архивный пропуск
    assert deleted_count == 1
    
    # Проверяем, что архивный пропуск действительно удален
    remaining_passes = [p for p in mock_repository.passes if p.id == 4]
    assert len(remaining_passes) == 0
