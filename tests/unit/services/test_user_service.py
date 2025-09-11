"""
Unit тесты для UserService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.easy_pass_bot.services.user_service import UserService
from src.easy_pass_bot.core.exceptions import ValidationError, DatabaseError, AuthorizationError
from src.easy_pass_bot.config import ROLES, USER_STATUSES
from tests.fixtures.user_fixtures import sample_user_data, admin_user_data, security_user_data


class TestUserService:
    """Тесты для UserService"""
    
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
    def user_service(self, mock_user_repository, mock_notification_service):
        """Фикстура сервиса пользователей"""
        return UserService(
            user_repository=mock_user_repository,
            notification_service=mock_notification_service
        )
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, sample_user_data):
        """Тест успешного создания пользователя"""
        user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        assert user.telegram_id == sample_user_data['telegram_id']
        assert user.full_name == sample_user_data['full_name']
        assert user.phone_number == sample_user_data['phone_number']
        assert user.apartment == sample_user_data['apartment']
        assert user.role == ROLES['RESIDENT']
        assert user.status == USER_STATUSES['PENDING']
        assert user.id is not None
    
    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, user_service, sample_user_data):
        """Тест создания пользователя, который уже существует"""
        # Создаем пользователя первый раз
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Пытаемся создать того же пользователя
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(
                telegram_id=sample_user_data['telegram_id'],
                full_name='Другой Пользователь',
                phone_number='+7 900 999 99 99',
                apartment='99'
            )
        
        assert 'уже существует' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_success(self, user_service, sample_user_data):
        """Тест успешного получения пользователя по Telegram ID"""
        # Создаем пользователя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Получаем пользователя
        user = await user_service.get_user_by_telegram_id(sample_user_data['telegram_id'])
        
        assert user is not None
        assert user.id == created_user.id
        assert user.telegram_id == sample_user_data['telegram_id']
    
    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, user_service):
        """Тест получения несуществующего пользователя"""
        user = await user_service.get_user_by_telegram_id(999999999)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, sample_user_data):
        """Тест успешного получения пользователя по ID"""
        # Создаем пользователя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Получаем пользователя
        user = await user_service.get_user_by_id(created_user.id)
        
        assert user is not None
        assert user.id == created_user.id
        assert user.telegram_id == sample_user_data['telegram_id']
    
    @pytest.mark.asyncio
    async def test_update_user_status_success(self, user_service, sample_user_data):
        """Тест успешного обновления статуса пользователя"""
        # Создаем пользователя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Обновляем статус
        result = await user_service.update_user_status(
            created_user.id, 
            USER_STATUSES['APPROVED']
        )
        
        assert result is True
        
        # Проверяем, что статус обновился
        updated_user = await user_service.get_user_by_id(created_user.id)
        assert updated_user.status == USER_STATUSES['APPROVED']
    
    @pytest.mark.asyncio
    async def test_update_user_status_not_found(self, user_service):
        """Тест обновления статуса несуществующего пользователя"""
        with pytest.raises(ValidationError) as exc_info:
            await user_service.update_user_status(999999, USER_STATUSES['APPROVED'])
        
        assert 'не найден' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_approve_user(self, user_service, sample_user_data):
        """Тест одобрения пользователя"""
        # Создаем пользователя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Одобряем пользователя
        result = await user_service.approve_user(created_user.id, 1)
        
        assert result is True
        
        # Проверяем статус
        updated_user = await user_service.get_user_by_id(created_user.id)
        assert updated_user.status == USER_STATUSES['APPROVED']
    
    @pytest.mark.asyncio
    async def test_reject_user(self, user_service, sample_user_data):
        """Тест отклонения пользователя"""
        # Создаем пользователя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Отклоняем пользователя
        result = await user_service.reject_user(created_user.id, 1)
        
        assert result is True
        
        # Проверяем статус
        updated_user = await user_service.get_user_by_id(created_user.id)
        assert updated_user.status == USER_STATUSES['REJECTED']
    
    @pytest.mark.asyncio
    async def test_get_pending_users(self, user_service, sample_user_data):
        """Тест получения пользователей на модерации"""
        # Создаем пользователя (по умолчанию PENDING)
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Создаем одобренного пользователя
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'] + 1,
            full_name='Одобренный Пользователь',
            phone_number='+7 900 111 11 11',
            apartment='1'
        )
        # Одобряем его
        users = await user_service.user_repository.get_all()
        approved_user = next(u for u in users if u.telegram_id == sample_user_data['telegram_id'] + 1)
        await user_service.approve_user(approved_user.id, 1)
        
        # Получаем пользователей на модерации
        pending_users = await user_service.get_pending_users()
        
        assert len(pending_users) == 1
        assert pending_users[0].status == USER_STATUSES['PENDING']
    
    @pytest.mark.asyncio
    async def test_get_users_by_role(self, user_service, sample_user_data, admin_user_data):
        """Тест получения пользователей по роли"""
        # Создаем жителя
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Создаем администратора
        await user_service.create_user(
            telegram_id=admin_user_data['telegram_id'],
            full_name=admin_user_data['full_name'],
            phone_number=admin_user_data['phone_number'],
            apartment=admin_user_data['apartment'],
            role=admin_user_data['role']
        )
        
        # Получаем жителей
        residents = await user_service.get_users_by_role(ROLES['RESIDENT'])
        assert len(residents) == 1
        assert residents[0].role == ROLES['RESIDENT']
        
        # Получаем администраторов
        admins = await user_service.get_users_by_role(ROLES['ADMIN'])
        assert len(admins) == 1
        assert admins[0].role == ROLES['ADMIN']
    
    @pytest.mark.asyncio
    async def test_is_admin_true(self, user_service, admin_user_data):
        """Тест проверки администратора - да"""
        # Создаем администратора
        created_user = await user_service.create_user(
            telegram_id=admin_user_data['telegram_id'],
            full_name=admin_user_data['full_name'],
            phone_number=admin_user_data['phone_number'],
            apartment=admin_user_data['apartment'],
            role=admin_user_data['role']
        )
        
        # Одобряем его
        await user_service.approve_user(created_user.id, 1)
        
        # Проверяем, что он администратор
        is_admin = await user_service.is_admin(admin_user_data['telegram_id'])
        assert is_admin is True
    
    @pytest.mark.asyncio
    async def test_is_admin_false(self, user_service, sample_user_data):
        """Тест проверки администратора - нет"""
        # Создаем обычного пользователя
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Проверяем, что он не администратор
        is_admin = await user_service.is_admin(sample_user_data['telegram_id'])
        assert is_admin is False
    
    @pytest.mark.asyncio
    async def test_is_security_true(self, user_service, security_user_data):
        """Тест проверки охранника - да"""
        # Создаем охранника
        created_user = await user_service.create_user(
            telegram_id=security_user_data['telegram_id'],
            full_name=security_user_data['full_name'],
            phone_number=security_user_data['phone_number'],
            apartment=security_user_data['apartment'],
            role=security_user_data['role']
        )
        
        # Одобряем его
        await user_service.approve_user(created_user.id, 1)
        
        # Проверяем, что он охранник
        is_security = await user_service.is_security(security_user_data['telegram_id'])
        assert is_security is True
    
    @pytest.mark.asyncio
    async def test_is_resident_true(self, user_service, sample_user_data):
        """Тест проверки жителя - да"""
        # Создаем жителя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Одобряем его
        await user_service.approve_user(created_user.id, 1)
        
        # Проверяем, что он житель
        is_resident = await user_service.is_resident(sample_user_data['telegram_id'])
        assert is_resident is True
    
    @pytest.mark.asyncio
    async def test_require_role_success(self, user_service, admin_user_data):
        """Тест успешной проверки роли"""
        # Создаем администратора
        created_user = await user_service.create_user(
            telegram_id=admin_user_data['telegram_id'],
            full_name=admin_user_data['full_name'],
            phone_number=admin_user_data['phone_number'],
            apartment=admin_user_data['apartment'],
            role=admin_user_data['role']
        )
        
        # Одобряем его
        await user_service.approve_user(created_user.id, 1)
        
        # Проверяем роль
        user = await user_service.require_role(
            admin_user_data['telegram_id'], 
            ROLES['ADMIN']
        )
        
        assert user is not None
        assert user.role == ROLES['ADMIN']
    
    @pytest.mark.asyncio
    async def test_require_role_wrong_role(self, user_service, sample_user_data):
        """Тест проверки роли с неверной ролью"""
        # Создаем жителя
        created_user = await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Одобряем его
        await user_service.approve_user(created_user.id, 1)
        
        # Пытаемся проверить роль администратора
        with pytest.raises(AuthorizationError) as exc_info:
            await user_service.require_role(
                sample_user_data['telegram_id'], 
                ROLES['ADMIN']
            )
        
        assert 'Требуется роль' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_require_role_not_approved(self, user_service, sample_user_data):
        """Тест проверки роли неодобренного пользователя"""
        # Создаем жителя (не одобряем)
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Пытаемся проверить роль
        with pytest.raises(AuthorizationError) as exc_info:
            await user_service.require_role(
                sample_user_data['telegram_id'], 
                ROLES['RESIDENT']
            )
        
        assert 'не одобрен' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_statistics(self, user_service, sample_user_data, admin_user_data):
        """Тест получения статистики пользователей"""
        # Создаем жителя
        await user_service.create_user(
            telegram_id=sample_user_data['telegram_id'],
            full_name=sample_user_data['full_name'],
            phone_number=sample_user_data['phone_number'],
            apartment=sample_user_data['apartment']
        )
        
        # Создаем администратора
        created_admin = await user_service.create_user(
            telegram_id=admin_user_data['telegram_id'],
            full_name=admin_user_data['full_name'],
            phone_number=admin_user_data['phone_number'],
            apartment=admin_user_data['apartment'],
            role=admin_user_data['role']
        )
        
        # Одобряем администратора
        await user_service.approve_user(created_admin.id, 1)
        
        # Получаем статистику
        stats = await user_service.get_user_statistics()
        
        assert stats['total'] == 2
        assert stats['pending_count'] == 1
        assert stats['approved_count'] == 1
        assert stats['rejected_count'] == 0
        assert ROLES['RESIDENT'] in stats['by_role']
        assert ROLES['ADMIN'] in stats['by_role']
        assert USER_STATUSES['PENDING'] in stats['by_status']
        assert USER_STATUSES['APPROVED'] in stats['by_status']





