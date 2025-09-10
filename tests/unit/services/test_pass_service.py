"""
Unit тесты для PassService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.easy_pass_bot.services.pass_service import PassService
from src.easy_pass_bot.core.exceptions import ValidationError, DatabaseError, AuthorizationError
from src.easy_pass_bot.config import PASS_STATUSES, ROLES, USER_STATUSES
from tests.fixtures.pass_fixtures import sample_pass_data, used_pass_data
from tests.fixtures.user_fixtures import sample_user_data, admin_user_data, security_user_data


class TestPassService:
    """Тесты для PassService"""
    
    @pytest.fixture
    def mock_pass_repository(self):
        """Мок репозитория пропусков"""
        from tests.mocks.repository_mocks import MockPassRepository
        return MockPassRepository()
    
    @pytest.fixture
    def mock_user_repository(self):
        """Мок репозитория пользователей"""
        from tests.mocks.repository_mocks import MockUserRepository
        return MockUserRepository()
    
    @pytest.fixture
    def mock_notification_service(self):
        """Мок сервиса уведомлений"""
        from tests.mocks.repository_mocks import MockNotificationService
        return MockNotificationService()
    
    @pytest.fixture
    def pass_service(self, mock_pass_repository, mock_user_repository, mock_notification_service):
        """Фикстура сервиса пропусков"""
        return PassService(
            pass_repository=mock_pass_repository,
            user_repository=mock_user_repository,
            notification_service=mock_notification_service
        )
    
    @pytest.fixture
    async def approved_user(self, mock_user_repository, sample_user_data):
        """Создает одобренного пользователя"""
        from src.easy_pass_bot.database.models import User
        user = User(
            id=1,
            telegram_id=sample_user_data['telegram_id'],
            role=sample_user_data['role'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment'],
            status=USER_STATUSES['APPROVED']
        )
        await mock_user_repository.create(user)
        return user
    
    @pytest.fixture
    async def security_user(self, mock_user_repository, security_user_data):
        """Создает охранника"""
        from src.easy_pass_bot.database.models import User
        user = User(
            id=2,
            telegram_id=security_user_data['telegram_id'],
            role=security_user_data['role'],
            full_name=security_user_data['full_name'],
            phone_number=security_user_data['phone_number'],
            apartment=security_user_data['apartment'],
            status=USER_STATUSES['APPROVED']
        )
        await mock_user_repository.create(user)
        return user
    
    @pytest.mark.asyncio
    async def test_create_pass_success(self, pass_service, approved_user):
        """Тест успешного создания пропуска"""
        car_number = 'А123БВ777'
        
        pass_obj = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number=car_number
        )
        
        assert pass_obj.user_id == approved_user.id
        assert pass_obj.car_number == car_number.upper()
        assert pass_obj.status == PASS_STATUSES['ACTIVE']
        assert pass_obj.id is not None
    
    @pytest.mark.asyncio
    async def test_create_pass_user_not_found(self, pass_service):
        """Тест создания пропуска для несуществующего пользователя"""
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.create_pass(
                user_id=999999,
                car_number='А123БВ777'
            )
        
        assert 'не найден' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_pass_user_not_approved(self, mock_user_repository, pass_service):
        """Тест создания пропуска для неодобренного пользователя"""
        from src.easy_pass_bot.database.models import User
        # Создаем неодобренного пользователя
        user = User(
            id=1,
            telegram_id=123456789,
            role=ROLES['RESIDENT'],
            full_name='Неодобренный Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='1',
            status=USER_STATUSES['PENDING']
        )
        await mock_user_repository.create(user)
        
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.create_pass(
                user_id=user.id,
                car_number='А123БВ777'
            )
        
        assert 'должен быть одобрен' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_pass_by_id_success(self, pass_service, approved_user):
        """Тест успешного получения пропуска по ID"""
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Получаем пропуск
        pass_obj = await pass_service.get_pass_by_id(created_pass.id)
        
        assert pass_obj is not None
        assert pass_obj.id == created_pass.id
        assert pass_obj.car_number == 'А123БВ777'
    
    @pytest.mark.asyncio
    async def test_get_pass_by_id_not_found(self, pass_service):
        """Тест получения несуществующего пропуска"""
        pass_obj = await pass_service.get_pass_by_id(999999)
        
        assert pass_obj is None
    
    @pytest.mark.asyncio
    async def test_get_user_passes(self, pass_service, approved_user):
        """Тест получения пропусков пользователя"""
        # Создаем несколько пропусков
        pass1 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        pass2 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='В456ГД888'
        )
        
        # Получаем пропуски пользователя
        passes = await pass_service.get_user_passes(approved_user.id)
        
        assert len(passes) == 2
        pass_ids = [p.id for p in passes]
        assert pass1.id in pass_ids
        assert pass2.id in pass_ids
    
    @pytest.mark.asyncio
    async def test_get_active_user_passes(self, pass_service, approved_user):
        """Тест получения активных пропусков пользователя"""
        # Создаем активный пропуск
        active_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Создаем использованный пропуск
        used_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='В456ГД888'
        )
        await pass_service.mark_pass_as_used(used_pass.id, 2)
        
        # Получаем активные пропуски
        active_passes = await pass_service.get_active_user_passes(approved_user.id)
        
        assert len(active_passes) == 1
        assert active_passes[0].id == active_pass.id
        assert active_passes[0].status == PASS_STATUSES['ACTIVE']
    
    @pytest.mark.asyncio
    async def test_search_passes_by_car_number_exact(self, pass_service, approved_user):
        """Тест точного поиска пропусков по номеру автомобиля"""
        car_number = 'А123БВ777'
        
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number=car_number
        )
        
        # Ищем пропуск
        found_passes = await pass_service.search_passes_by_car_number(car_number)
        
        assert len(found_passes) == 1
        assert found_passes[0].id == created_pass.id
        assert found_passes[0].car_number == car_number
    
    @pytest.mark.asyncio
    async def test_search_passes_by_car_number_partial(self, pass_service, approved_user):
        """Тест частичного поиска пропусков по номеру автомобиля"""
        # Создаем пропуски с похожими номерами
        pass1 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        pass2 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ888'
        )
        pass3 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='В456ГД777'
        )
        
        # Ищем частично
        found_passes = await pass_service.search_passes_by_car_number('А123', partial=True)
        
        assert len(found_passes) == 2
        pass_ids = [p.id for p in found_passes]
        assert pass1.id in pass_ids
        assert pass2.id in pass_ids
        assert pass3.id not in pass_ids
    
    @pytest.mark.asyncio
    async def test_mark_pass_as_used_success(self, pass_service, approved_user, security_user):
        """Тест успешной отметки пропуска как использованного"""
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Отмечаем как использованный
        result = await pass_service.mark_pass_as_used(
            created_pass.id, 
            security_user.id
        )
        
        assert result is True
        
        # Проверяем статус
        updated_pass = await pass_service.get_pass_by_id(created_pass.id)
        assert updated_pass.status == PASS_STATUSES['USED']
        assert updated_pass.used_by_id == security_user.id
        assert updated_pass.used_at is not None
    
    @pytest.mark.asyncio
    async def test_mark_pass_as_used_not_found(self, pass_service, security_user):
        """Тест отметки несуществующего пропуска как использованного"""
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.mark_pass_as_used(999999, security_user.id)
        
        assert 'не найден' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mark_pass_as_used_not_active(self, pass_service, approved_user, security_user):
        """Тест отметки неактивного пропуска как использованного"""
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Отмечаем как использованный первый раз
        await pass_service.mark_pass_as_used(created_pass.id, security_user.id)
        
        # Пытаемся отметить снова
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.mark_pass_as_used(created_pass.id, security_user.id)
        
        assert 'не активен' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mark_pass_as_used_unauthorized(self, pass_service, approved_user):
        """Тест отметки пропуска пользователем без прав"""
        # Создаем обычного пользователя (не охранника)
        from src.easy_pass_bot.database.models import User
        regular_user = User(
            id=3,
            telegram_id=333333333,
            role=ROLES['RESIDENT'],
            full_name='Обычный Пользователь',
            phone_number='+7 900 333 33 33',
            apartment='3',
            status=USER_STATUSES['APPROVED']
        )
        await pass_service.user_repository.create(regular_user)
        
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Пытаемся отметить пропуск обычным пользователем
        with pytest.raises(AuthorizationError) as exc_info:
            await pass_service.mark_pass_as_used(created_pass.id, regular_user.id)
        
        assert 'охранник или админ' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_pass_success(self, pass_service, approved_user):
        """Тест успешной отмены пропуска"""
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Отменяем пропуск
        result = await pass_service.cancel_pass(created_pass.id, approved_user.id)
        
        assert result is True
        
        # Проверяем статус
        updated_pass = await pass_service.get_pass_by_id(created_pass.id)
        assert updated_pass.status == PASS_STATUSES['CANCELLED']
        assert updated_pass.used_by_id == approved_user.id
    
    @pytest.mark.asyncio
    async def test_cancel_pass_not_found(self, pass_service, approved_user):
        """Тест отмены несуществующего пропуска"""
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.cancel_pass(999999, approved_user.id)
        
        assert 'не найден' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_pass_not_active(self, pass_service, approved_user):
        """Тест отмены неактивного пропуска"""
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Отменяем пропуск первый раз
        await pass_service.cancel_pass(created_pass.id, approved_user.id)
        
        # Пытаемся отменить снова
        with pytest.raises(ValidationError) as exc_info:
            await pass_service.cancel_pass(created_pass.id, approved_user.id)
        
        assert 'только активные' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_pass_unauthorized(self, pass_service, approved_user):
        """Тест отмены пропуска неавторизованным пользователем"""
        # Создаем другого пользователя
        from src.easy_pass_bot.database.models import User
        other_user = User(
            id=3,
            telegram_id=333333333,
            role=ROLES['RESIDENT'],
            full_name='Другой Пользователь',
            phone_number='+7 900 333 33 33',
            apartment='3',
            status=USER_STATUSES['APPROVED']
        )
        await pass_service.user_repository.create(other_user)
        
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Пытаемся отменить чужой пропуск
        with pytest.raises(AuthorizationError) as exc_info:
            await pass_service.cancel_pass(created_pass.id, other_user.id)
        
        assert 'только свои' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_pass_by_admin(self, pass_service, approved_user, security_user):
        """Тест отмены пропуска администратором"""
        # Создаем администратора
        from src.easy_pass_bot.database.models import User
        admin_user = User(
            id=3,
            telegram_id=333333333,
            role=ROLES['ADMIN'],
            full_name='Администратор',
            phone_number='+7 900 333 33 33',
            apartment=None,
            status=USER_STATUSES['APPROVED']
        )
        await pass_service.user_repository.create(admin_user)
        
        # Создаем пропуск
        created_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Администратор отменяет пропуск
        result = await pass_service.cancel_pass(created_pass.id, admin_user.id)
        
        assert result is True
        
        # Проверяем статус
        updated_pass = await pass_service.get_pass_by_id(created_pass.id)
        assert updated_pass.status == PASS_STATUSES['CANCELLED']
    
    @pytest.mark.asyncio
    async def test_get_pass_statistics(self, pass_service, approved_user, security_user):
        """Тест получения статистики пропусков"""
        # Создаем активный пропуск
        active_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        
        # Создаем использованный пропуск
        used_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='В456ГД888'
        )
        await pass_service.mark_pass_as_used(used_pass.id, security_user.id)
        
        # Создаем отмененный пропуск
        cancelled_pass = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='Е789ЖЗ999'
        )
        await pass_service.cancel_pass(cancelled_pass.id, approved_user.id)
        
        # Получаем статистику
        stats = await pass_service.get_pass_statistics()
        
        assert stats['total'] == 3
        assert stats['active_count'] == 1
        assert stats['used_count'] == 1
        assert stats['cancelled_count'] == 1
        assert PASS_STATUSES['ACTIVE'] in stats['by_status']
        assert PASS_STATUSES['USED'] in stats['by_status']
        assert PASS_STATUSES['CANCELLED'] in stats['by_status']
    
    @pytest.mark.asyncio
    async def test_get_recent_passes(self, pass_service, approved_user):
        """Тест получения последних пропусков"""
        # Создаем несколько пропусков
        pass1 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='А123БВ777'
        )
        pass2 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='В456ГД888'
        )
        pass3 = await pass_service.create_pass(
            user_id=approved_user.id,
            car_number='Е789ЖЗ999'
        )
        
        # Получаем последние пропуски
        recent_passes = await pass_service.get_recent_passes(limit=2)
        
        assert len(recent_passes) == 2
        # Должны быть отсортированы по дате создания (новые сначала)
        assert recent_passes[0].id == pass3.id
        assert recent_passes[1].id == pass2.id
