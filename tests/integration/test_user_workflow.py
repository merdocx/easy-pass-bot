"""
Интеграционные тесты для пользовательского workflow
"""
import pytest
import pytest_asyncio
from src.easy_pass_bot.services.user_service import UserService
from src.easy_pass_bot.services.pass_service import PassService
from src.easy_pass_bot.services.validation_service import ValidationService
from src.easy_pass_bot.services.notification_service import NotificationService
from tests.mocks.repository_mocks import MockUserRepository, MockPassRepository, MockNotificationService
from src.easy_pass_bot.config import ROLES, USER_STATUSES, PASS_STATUSES


class TestUserWorkflow:
    """Интеграционные тесты пользовательского workflow"""
    
    @pytest_asyncio.fixture
    async def services(self):
        """Настройка сервисов для интеграционных тестов"""
        # Создаем репозитории
        user_repo = MockUserRepository()
        pass_repo = MockPassRepository()
        notification_service = MockNotificationService()
        
        # Создаем сервисы
        validation_service = ValidationService()
        user_service = UserService(
            user_repository=user_repo,
            notification_service=notification_service
        )
        pass_service = PassService(
            pass_repository=pass_repo,
            user_repository=user_repo,
            notification_service=notification_service
        )
        
        # Инициализируем сервисы
        await validation_service.initialize()
        await user_service.initialize()
        await pass_service.initialize()
        
        return {
            'user_service': user_service,
            'pass_service': pass_service,
            'validation_service': validation_service,
            'notification_service': notification_service,
            'user_repo': user_repo,
            'pass_repo': pass_repo
        }
    
    @pytest.mark.asyncio
    async def test_complete_user_registration_workflow(self, services):
        """Тест полного workflow регистрации пользователя"""
        user_service = services['user_service']
        validation_service = services['validation_service']
        notification_service = services['notification_service']
        
        # 1. Валидация данных регистрации
        registration_data = {
            'full_name': 'Иванов Иван Иванович',
            'phone_number': '+7 900 123 45 67',
            'apartment': '15'
        }
        
        is_valid = await validation_service.validate_user_data(registration_data)
        assert is_valid is True
        
        # 2. Создание пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name=registration_data['full_name'],
            phone_number=registration_data['phone_number'],
            apartment=registration_data['apartment']
        )
        
        assert user.status == USER_STATUSES['PENDING']
        assert user.role == ROLES['RESIDENT']
        
        # 3. Одобрение пользователя
        result = await user_service.approve_user(user.id, 1)
        assert result is True
        
        # 4. Проверка, что пользователь стал одобренным
        updated_user = await user_service.get_user_by_id(user.id)
        assert updated_user.status == USER_STATUSES['APPROVED']
        
        # 5. Проверка уведомления
        assert len(notification_service.sent_notifications) == 1
        assert notification_service.sent_notifications[0]['user_id'] == user.telegram_id
        assert 'одобрена' in notification_service.sent_notifications[0]['message']
    
    @pytest.mark.asyncio
    async def test_complete_pass_creation_workflow(self, services):
        """Тест полного workflow создания пропуска"""
        user_service = services['user_service']
        pass_service = services['pass_service']
        validation_service = services['validation_service']
        
        # 1. Создаем и одобряем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Иванов Иван Иванович',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # 2. Валидация номера автомобиля
        car_number = 'а123бв777'  # В нижнем регистре
        is_valid = await validation_service.validate_car_number(car_number)
        assert is_valid is True
        
        # 3. Создание пропуска
        pass_obj = await pass_service.create_pass(
            user_id=user.id,
            car_number=car_number
        )
        
        assert pass_obj.car_number == 'А123БВ777'  # Должен быть в верхнем регистре
        assert pass_obj.status == PASS_STATUSES['ACTIVE']
        assert pass_obj.user_id == user.id
        
        # 4. Проверка, что пропуск появился у пользователя
        user_passes = await pass_service.get_user_passes(user.id)
        assert len(user_passes) == 1
        assert user_passes[0].id == pass_obj.id
    
    @pytest.mark.asyncio
    async def test_complete_pass_usage_workflow(self, services):
        """Тест полного workflow использования пропуска"""
        user_service = services['user_service']
        pass_service = services['pass_service']
        notification_service = services['notification_service']
        
        # 1. Создаем жителя и одобряем его
        resident = await user_service.create_user(
            telegram_id=123456789,
            full_name='Житель',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(resident.id, 1)
        
        # 2. Создаем охранника
        security = await user_service.create_user(
            telegram_id=987654321,
            full_name='Охранник',
            phone_number='+7 900 987 65 43',
            apartment=None,
            role=ROLES['SECURITY']
        )
        await user_service.approve_user(security.id, 1)
        
        # 3. Житель создает пропуск
        pass_obj = await pass_service.create_pass(
            user_id=resident.id,
            car_number='А123БВ777'
        )
        
        # 4. Охранник ищет пропуск
        found_passes = await pass_service.search_passes_by_car_number('А123БВ777')
        assert len(found_passes) == 1
        assert found_passes[0].id == pass_obj.id
        
        # 5. Охранник отмечает пропуск как использованный
        result = await pass_service.mark_pass_as_used(pass_obj.id, security.id)
        assert result is True
        
        # 6. Проверяем, что пропуск стал использованным
        updated_pass = await pass_service.get_pass_by_id(pass_obj.id)
        assert updated_pass.status == PASS_STATUSES['USED']
        assert updated_pass.used_by_id == security.id
        
        # 7. Проверяем уведомление владельца пропуска
        assert len(notification_service.sent_notifications) == 1
        assert notification_service.sent_notifications[0]['user_id'] == resident.telegram_id
        assert 'использован' in notification_service.sent_notifications[0]['message']
    
    @pytest.mark.asyncio
    async def test_admin_management_workflow(self, services):
        """Тест workflow управления администратором"""
        user_service = services['user_service']
        pass_service = services['pass_service']
        
        # 1. Создаем администратора
        admin = await user_service.create_user(
            telegram_id=111111111,
            full_name='Администратор',
            phone_number='+7 900 111 11 11',
            apartment=None,
            role=ROLES['ADMIN']
        )
        await user_service.approve_user(admin.id, 1)
        
        # 2. Создаем нескольких пользователей на модерации
        user1 = await user_service.create_user(
            telegram_id=222222222,
            full_name='Пользователь 1',
            phone_number='+7 900 222 22 22',
            apartment='1'
        )
        user2 = await user_service.create_user(
            telegram_id=333333333,
            full_name='Пользователь 2',
            phone_number='+7 900 333 33 33',
            apartment='2'
        )
        
        # 3. Администратор получает список на модерации
        pending_users = await user_service.get_pending_users()
        assert len(pending_users) == 2
        
        # 4. Администратор одобряет одного пользователя
        await user_service.approve_user(user1.id, admin.id)
        
        # 5. Администратор отклоняет другого пользователя
        await user_service.reject_user(user2.id, admin.id)
        
        # 6. Проверяем статусы
        updated_user1 = await user_service.get_user_by_id(user1.id)
        updated_user2 = await user_service.get_user_by_id(user2.id)
        
        assert updated_user1.status == USER_STATUSES['APPROVED']
        assert updated_user2.status == USER_STATUSES['REJECTED']
        
        # 7. Одобренный пользователь может создавать пропуски
        pass_obj = await pass_service.create_pass(
            user_id=user1.id,
            car_number='В456ГД888'
        )
        assert pass_obj is not None
        
        # 8. Отклоненный пользователь не может создавать пропуски
        with pytest.raises(Exception):  # ValidationError
            await pass_service.create_pass(
                user_id=user2.id,
                car_number='Е789ЖЗ999'
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, services):
        """Тест workflow обработки ошибок"""
        user_service = services['user_service']
        pass_service = services['pass_service']
        validation_service = services['validation_service']
        
        # 1. Тест валидации неверных данных
        invalid_data = {
            'full_name': '',  # Пустое имя
            'phone_number': 'invalid_phone',
            'apartment': 'A' * 20  # Слишком длинная квартира
        }
        
        is_valid = await validation_service.validate_user_data(invalid_data)
        assert is_valid is False
        assert validation_service.has_errors()
        
        # 2. Тест создания пользователя с неверными данными
        with pytest.raises(Exception):  # ValidationError
            await user_service.create_user(
                telegram_id=123456789,
                full_name='',
                phone_number='invalid',
                apartment=''
            )
        
        # 3. Тест создания пропуска неодобренным пользователем
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        # Не одобряем пользователя
        
        with pytest.raises(Exception):  # ValidationError
            await pass_service.create_pass(
                user_id=user.id,
                car_number='А123БВ777'
            )
        
        # 4. Тест поиска несуществующего пропуска
        found_passes = await pass_service.search_passes_by_car_number('НЕСУЩЕСТВУЮЩИЙ')
        assert len(found_passes) == 0
    
    @pytest.mark.asyncio
    async def test_statistics_workflow(self, services):
        """Тест workflow получения статистики"""
        user_service = services['user_service']
        pass_service = services['pass_service']
        
        # 1. Создаем пользователей разных ролей
        resident = await user_service.create_user(
            telegram_id=111111111,
            full_name='Житель',
            phone_number='+7 900 111 11 11',
            apartment='1'
        )
        await user_service.approve_user(resident.id, 1)
        
        admin = await user_service.create_user(
            telegram_id=222222222,
            full_name='Админ',
            phone_number='+7 900 222 22 22',
            apartment=None,
            role=ROLES['ADMIN']
        )
        await user_service.approve_user(admin.id, 1)
        
        # 2. Создаем пропуски
        pass1 = await pass_service.create_pass(
            user_id=resident.id,
            car_number='А123БВ777'
        )
        pass2 = await pass_service.create_pass(
            user_id=resident.id,
            car_number='В456ГД888'
        )
        
        # 3. Отмечаем один пропуск как использованный
        await pass_service.mark_pass_as_used(pass1.id, admin.id)
        
        # 4. Получаем статистику пользователей
        user_stats = await user_service.get_user_statistics()
        assert user_stats['total'] == 2
        assert user_stats['approved_count'] == 2
        assert user_stats['pending_count'] == 0
        assert ROLES['RESIDENT'] in user_stats['by_role']
        assert ROLES['ADMIN'] in user_stats['by_role']
        
        # 5. Получаем статистику пропусков
        pass_stats = await pass_service.get_pass_statistics()
        assert pass_stats['total'] == 2
        assert pass_stats['active_count'] == 1
        assert pass_stats['used_count'] == 1
        assert pass_stats['cancelled_count'] == 0





