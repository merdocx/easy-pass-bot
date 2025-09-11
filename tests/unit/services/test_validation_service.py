"""
Unit тесты для ValidationService
"""
import pytest
from src.easy_pass_bot.services.validation_service import ValidationService
from src.easy_pass_bot.core.exceptions import ValidationError


class TestValidationService:
    """Тесты для ValidationService"""
    
    @pytest.fixture
    def validation_service(self):
        """Фикстура сервиса валидации"""
        return ValidationService()
    
    @pytest.mark.asyncio
    async def test_validate_user_data_success(self, validation_service):
        """Тест успешной валидации данных пользователя"""
        data = {
            'full_name': 'Иванов Иван Иванович',
            'phone_number': '+7 900 123 45 67',
            'apartment': '15'
        }
        
        result = await validation_service.validate_user_data(data)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_user_data_missing_fields(self, validation_service):
        """Тест валидации с отсутствующими полями"""
        data = {
            'full_name': 'Иванов Иван Иванович',
            'phone_number': '+7 900 123 45 67'
            # Отсутствует apartment
        }
        
        result = await validation_service.validate_user_data(data)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('apartment' in error for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_car_number_success(self, validation_service):
        """Тест успешной валидации номера автомобиля"""
        car_number = 'А123БВ777'
        
        result = await validation_service.validate_car_number(car_number)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_car_number_lowercase(self, validation_service):
        """Тест валидации номера автомобиля в нижнем регистре"""
        car_number = 'а123бв777'
        
        result = await validation_service.validate_car_number(car_number)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_car_number_invalid_format(self, validation_service):
        """Тест валидации неверного формата номера автомобиля"""
        car_number = '123ABC456'
        
        result = await validation_service.validate_car_number(car_number)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('формат' in error.lower() for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_car_number_empty(self, validation_service):
        """Тест валидации пустого номера автомобиля"""
        car_number = ''
        
        result = await validation_service.validate_car_number(car_number)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('пустым' in error for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_registration_form_success(self, validation_service):
        """Тест успешной валидации формы регистрации"""
        text = 'Иванов Иван Иванович, +7 900 123 45 67, 15'
        
        result = await validation_service.validate_registration_form(text)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_registration_form_wrong_format(self, validation_service):
        """Тест валидации формы регистрации с неверным форматом"""
        text = 'Иванов Иван Иванович, +7 900 123 45 67'  # Отсутствует квартира
        
        result = await validation_service.validate_registration_form(text)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('формат' in error.lower() for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_search_query_success(self, validation_service):
        """Тест успешной валидации поискового запроса"""
        query = 'А123БВ'
        
        result = await validation_service.validate_search_query(query)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_search_query_too_short(self, validation_service):
        """Тест валидации слишком короткого поискового запроса"""
        query = 'А'
        
        result = await validation_service.validate_search_query(query)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('минимум' in error for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_search_query_too_long(self, validation_service):
        """Тест валидации слишком длинного поискового запроса"""
        query = 'А' * 25  # 25 символов
        
        result = await validation_service.validate_search_query(query)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('длинный' in error for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_email_success(self, validation_service):
        """Тест успешной валидации email"""
        email = 'test@example.com'
        
        result = await validation_service.validate_email(email)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_email_invalid(self, validation_service):
        """Тест валидации неверного email"""
        email = 'invalid-email'
        
        result = await validation_service.validate_email(email)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('формат' in error.lower() for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_telegram_id_success(self, validation_service):
        """Тест успешной валидации Telegram ID"""
        telegram_id = 123456789
        
        result = await validation_service.validate_telegram_id(telegram_id)
        
        assert result is True
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_validate_telegram_id_invalid(self, validation_service):
        """Тест валидации неверного Telegram ID"""
        telegram_id = -1  # Отрицательный ID
        
        result = await validation_service.validate_telegram_id(telegram_id)
        
        assert result is False
        assert validation_service.has_errors()
        assert any('положительным' in error for error in validation_service.get_errors())
    
    @pytest.mark.asyncio
    async def test_validate_telegram_id_string(self, validation_service):
        """Тест валидации Telegram ID как строки"""
        telegram_id = '123456789'
        
        result = await validation_service.validate_telegram_id(telegram_id)
        
        assert result is True
        assert not validation_service.has_errors()
    
    def test_get_validation_rules(self, validation_service):
        """Тест получения правил валидации"""
        rules = validation_service.get_validation_rules()
        
        assert isinstance(rules, dict)
        assert 'name' in rules
        assert 'phone' in rules
        assert 'apartment' in rules
        assert 'car_number' in rules
        assert 'email' in rules
        
        # Проверяем структуру правил
        assert 'min_length' in rules['name']
        assert 'max_length' in rules['name']
        assert 'pattern' in rules['name']
    
    @pytest.mark.asyncio
    async def test_clear_errors(self, validation_service):
        """Тест очистки ошибок"""
        # Добавляем ошибку
        validation_service.add_error('Test error')
        assert validation_service.has_errors()
        
        # Очищаем ошибки
        validation_service.clear_errors()
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_name_validation_edge_cases(self, validation_service):
        """Тест граничных случаев валидации имени"""
        # Слишком короткое имя
        await validation_service._validate_name('А')
        assert validation_service.has_errors()
        validation_service.clear_errors()
        
        # Слишком длинное имя
        long_name = 'А' * 101
        await validation_service._validate_name(long_name)
        assert validation_service.has_errors()
        validation_service.clear_errors()
        
        # Имя с недопустимыми символами
        await validation_service._validate_name('Иван123')
        assert validation_service.has_errors()
        validation_service.clear_errors()
        
        # Валидное имя
        await validation_service._validate_name('Иван-Петр Иванович')
        assert not validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_phone_validation_edge_cases(self, validation_service):
        """Тест граничных случаев валидации телефона"""
        # Телефон с пробелами и дефисами
        await validation_service._validate_phone('+7 (900) 123-45-67')
        assert not validation_service.has_errors()
        validation_service.clear_errors()
        
        # Неверный формат телефона
        await validation_service._validate_phone('123456')
        assert validation_service.has_errors()
        validation_service.clear_errors()
        
        # Пустой телефон
        await validation_service._validate_phone('')
        assert validation_service.has_errors()
    
    @pytest.mark.asyncio
    async def test_apartment_validation_edge_cases(self, validation_service):
        """Тест граничных случаев валидации квартиры"""
        # Квартира с буквами
        await validation_service._validate_apartment('15А')
        assert not validation_service.has_errors()
        validation_service.clear_errors()
        
        # Пустая квартира
        await validation_service._validate_apartment('')
        assert validation_service.has_errors()
        validation_service.clear_errors()
        
        # Слишком длинная квартира
        long_apartment = '1' * 11
        await validation_service._validate_apartment(long_apartment)
        assert validation_service.has_errors()





