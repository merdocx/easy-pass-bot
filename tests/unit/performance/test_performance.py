"""
Тесты производительности
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from src.easy_pass_bot.services.validation_service import ValidationService
from src.easy_pass_bot.services.user_service import UserService
from src.easy_pass_bot.services.pass_service import PassService
from tests.mocks.repository_mocks import MockUserRepository, MockPassRepository, MockNotificationService


class TestPerformance:
    """Тесты производительности системы"""
    
    @pytest.fixture
    async def performance_services(self):
        """Сервисы для тестов производительности"""
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
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_validation_performance(self, performance_services):
        """Тест производительности валидации"""
        validation_service = performance_services['validation_service']
        
        # Тестовые данные
        test_data = {
            'full_name': 'Иванов Иван Иванович',
            'phone_number': '+7 900 123 45 67',
            'apartment': '15'
        }
        
        # Измеряем время валидации
        start_time = time.time()
        
        for _ in range(1000):
            await validation_service.validate_user_data(test_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем, что валидация выполняется быстро
        assert duration < 1.0  # Менее 1 секунды для 1000 валидаций
        print(f"Validation performance: {duration:.3f}s for 1000 validations")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_user_creation_performance(self, performance_services):
        """Тест производительности создания пользователей"""
        user_service = performance_services['user_service']
        
        # Измеряем время создания пользователей
        start_time = time.time()
        
        for i in range(100):
            await user_service.create_user(
                telegram_id=100000000 + i,
                full_name=f'Пользователь {i}',
                phone_number=f'+7 900 {i:03d} {i:02d} {i:02d}',
                apartment=str(i % 100 + 1)
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем производительность
        assert duration < 2.0  # Менее 2 секунд для 100 пользователей
        print(f"User creation performance: {duration:.3f}s for 100 users")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_pass_creation_performance(self, performance_services):
        """Тест производительности создания пропусков"""
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Измеряем время создания пропусков
        start_time = time.time()
        
        for i in range(100):
            await pass_service.create_pass(
                user_id=user.id,
                car_number=f'А{i:03d}БВ{i:03d}'
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем производительность
        assert duration < 2.0  # Менее 2 секунд для 100 пропусков
        print(f"Pass creation performance: {duration:.3f}s for 100 passes")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_search_performance(self, performance_services):
        """Тест производительности поиска"""
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Создаем много пропусков
        for i in range(1000):
            await pass_service.create_pass(
                user_id=user.id,
                car_number=f'А{i:03d}БВ{i:03d}'
            )
        
        # Измеряем время поиска
        start_time = time.time()
        
        for i in range(100):
            await pass_service.search_passes_by_car_number(f'А{i:03d}', partial=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем производительность
        assert duration < 3.0  # Менее 3 секунд для 100 поисков
        print(f"Search performance: {duration:.3f}s for 100 searches in 1000 passes")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_operations(self, performance_services):
        """Тест производительности при concurrent операциях"""
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Создаем несколько пропусков
        passes = []
        for i in range(10):
            pass_obj = await pass_service.create_pass(
                user_id=user.id,
                car_number=f'А{i:03d}БВ{i:03d}'
            )
            passes.append(pass_obj)
        
        # Выполняем concurrent операции
        async def concurrent_operation(pass_id):
            # Имитируем поиск и использование пропуска
            found_passes = await pass_service.search_passes_by_car_number('А', partial=True)
            if found_passes:
                await pass_service.mark_pass_as_used(pass_id, 1)
        
        start_time = time.time()
        
        # Запускаем 50 concurrent операций
        tasks = [concurrent_operation(passes[i % len(passes)].id) for i in range(50)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем производительность
        assert duration < 5.0  # Менее 5 секунд для 50 concurrent операций
        print(f"Concurrent operations performance: {duration:.3f}s for 50 operations")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_memory_usage(self, performance_services):
        """Тест использования памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем много данных
        users = []
        for i in range(1000):
            user = await user_service.create_user(
                telegram_id=100000000 + i,
                full_name=f'Пользователь {i}',
                phone_number=f'+7 900 {i:03d} {i:02d} {i:02d}',
                apartment=str(i % 100 + 1)
            )
            await user_service.approve_user(user.id, 1)
            users.append(user)
        
        # Создаем пропуски для каждого пользователя
        for user in users:
            for j in range(5):  # 5 пропусков на пользователя
                await pass_service.create_pass(
                    user_id=user.id,
                    car_number=f'А{user.id:03d}БВ{j:03d}'
                )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Проверяем, что использование памяти разумное
        assert memory_increase < 100  # Менее 100MB для 1000 пользователей и 5000 пропусков
        print(f"Memory usage: {memory_increase:.1f}MB for 1000 users and 5000 passes")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_database_operations_performance(self, performance_services):
        """Тест производительности операций с базой данных"""
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Измеряем время различных операций
        operations = []
        
        # Создание пропусков
        start_time = time.time()
        for i in range(100):
            await pass_service.create_pass(
                user_id=user.id,
                car_number=f'А{i:03d}БВ{i:03d}'
            )
        operations.append(('Create passes', time.time() - start_time))
        
        # Поиск пропусков
        start_time = time.time()
        for i in range(100):
            await pass_service.search_passes_by_car_number(f'А{i:03d}', partial=True)
        operations.append(('Search passes', time.time() - start_time))
        
        # Получение пропусков пользователя
        start_time = time.time()
        for _ in range(100):
            await pass_service.get_user_passes(user.id)
        operations.append(('Get user passes', time.time() - start_time))
        
        # Проверяем производительность каждой операции
        for operation_name, duration in operations:
            assert duration < 2.0, f"{operation_name} took too long: {duration:.3f}s"
            print(f"{operation_name}: {duration:.3f}s")
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_load_testing(self, performance_services):
        """Нагрузочное тестирование"""
        user_service = performance_services['user_service']
        pass_service = performance_services['pass_service']
        
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name='Тестовый Пользователь',
            phone_number='+7 900 123 45 67',
            apartment='15'
        )
        await user_service.approve_user(user.id, 1)
        
        # Создаем пропуски
        passes = []
        for i in range(100):
            pass_obj = await pass_service.create_pass(
                user_id=user.id,
                car_number=f'А{i:03d}БВ{i:03d}'
            )
            passes.append(pass_obj)
        
        # Нагрузочное тестирование
        async def load_test_operation():
            # Имитируем типичную нагрузку
            tasks = []
            
            # 10 поисков
            for _ in range(10):
                tasks.append(pass_service.search_passes_by_car_number('А', partial=True))
            
            # 5 созданий пропусков
            for i in range(5):
                tasks.append(pass_service.create_pass(
                    user_id=user.id,
                    car_number=f'В{i:03d}ГД{i:03d}'
                ))
            
            # 5 использований пропусков
            for i in range(5):
                if i < len(passes):
                    tasks.append(pass_service.mark_pass_as_used(passes[i].id, 1))
            
            await asyncio.gather(*tasks)
        
        # Запускаем нагрузочное тестирование
        start_time = time.time()
        
        # 10 concurrent нагрузочных операций
        load_tasks = [load_test_operation() for _ in range(10)]
        await asyncio.gather(*load_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем, что система справляется с нагрузкой
        assert duration < 10.0  # Менее 10 секунд для нагрузочного теста
        print(f"Load test performance: {duration:.3f}s for 10 concurrent load operations")
