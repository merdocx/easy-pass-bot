import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os

# Добавляем путь к админке
sys.path.append('/root/easy_pass_bot/admin')
sys.path.append('/root/easy_pass_bot/src')

import main
app = main.app
admin_auth = main.admin_auth
db = main.db

class TestUserManagement:
    """Тесты для управления пользователями"""
    
    @pytest.fixture
    def client(self):
        """Создание тестового клиента"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Мок базы данных с новыми полями"""
        with patch.object(db, 'get_all_users') as mock_users, \
             patch.object(db, 'block_user') as mock_block, \
             patch.object(db, 'unblock_user') as mock_unblock, \
             patch.object(db, 'delete_user') as mock_delete, \
             patch.object(db, 'update_user_status') as mock_update:
            
            # Настройка моков
            mock_users.return_value = [
                type('User', (), {
                    'id': 1,
                    'telegram_id': 123456789,
                    'role': 'resident',
                    'full_name': 'Иван Иванов',
                    'phone_number': '+7 900 123 45 67',
                    'apartment': '15',
                    'status': 'pending',
                    'blocked_until': None,
                    'block_reason': None,
                    'created_at': '2024-01-01 12:00:00'
                })(),
                type('User', (), {
                    'id': 2,
                    'telegram_id': 987654321,
                    'role': 'resident',
                    'full_name': 'Петр Петров',
                    'phone_number': '+7 900 987 65 43',
                    'apartment': '20',
                    'status': 'approved',
                    'blocked_until': None,
                    'block_reason': None,
                    'created_at': '2024-01-02 12:00:00'
                })(),
                type('User', (), {
                    'id': 3,
                    'telegram_id': 555666777,
                    'role': 'resident',
                    'full_name': 'Анна Сидорова',
                    'phone_number': '+7 900 555 66 77',
                    'apartment': '30',
                    'status': 'blocked',
                    'blocked_until': '2024-12-31',
                    'block_reason': 'Нарушение правил',
                    'created_at': '2024-01-03 12:00:00'
                })()
            ]
            
            mock_block.return_value = None
            mock_unblock.return_value = None
            mock_delete.return_value = None
            mock_update.return_value = None
            
            yield {
                'users': mock_users,
                'block': mock_block,
                'unblock': mock_unblock,
                'delete': mock_delete,
                'update': mock_update
            }
    
    def test_block_user(self, client, mock_db):
        """Тест блокировки пользователя"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Блокируем пользователя
        response = client.post("/users/2/block", 
                             data={
                                 "blocked_until": "2024-12-31",
                                 "block_reason": "Тестовая блокировка"
                             },
                             cookies={"admin_session": session_cookie},
                             follow_redirects=True)
        
        assert response.status_code == 200
        mock_db['block'].assert_called_once_with(2, "2024-12-31", "Тестовая блокировка")
    
    def test_unblock_user(self, client, mock_db):
        """Тест разблокировки пользователя"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Разблокируем пользователя
        response = client.post("/users/3/unblock", 
                             cookies={"admin_session": session_cookie},
                             follow_redirects=True)
        
        assert response.status_code == 200
        mock_db['unblock'].assert_called_once_with(3)
    
    def test_delete_user(self, client, mock_db):
        """Тест удаления пользователя"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Удаляем пользователя
        response = client.post("/users/1/delete", 
                             cookies={"admin_session": session_cookie},
                             follow_redirects=True)
        
        assert response.status_code == 200
        mock_db['delete'].assert_called_once_with(1)
    
    def test_users_page_with_new_status(self, client, mock_db):
        """Тест страницы пользователей с новым статусом"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Запрашиваем страницу пользователей
        response = client.get("/users", cookies={"admin_session": session_cookie})
        assert response.status_code == 200
        assert "Заблокированы" in response.text
        assert "Анна Сидорова" in response.text
    
    def test_filter_blocked_users(self, client, mock_db):
        """Тест фильтрации заблокированных пользователей"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Фильтруем заблокированных пользователей
        response = client.get("/users?status_filter=blocked", 
                            cookies={"admin_session": session_cookie})
        
        assert response.status_code == 200
        # Проверяем, что мок был вызван с правильными параметрами
        mock_db['users'].assert_called()

class TestPassRestriction:
    """Тесты ограничений для заблокированных пользователей"""
    
    def test_blocked_user_cannot_create_pass(self):
        """Тест что заблокированный пользователь не может создать пропуск"""
        from easy_pass_bot.services.pass_service import PassService
        from easy_pass_bot.core.exceptions import DatabaseError
        
        # Создаем мок пользователя с блокировкой в будущем
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        blocked_user = type('User', (), {
            'id': 1,
            'status': 'blocked',
            'blocked_until': future_date,
            'block_reason': 'Нарушение правил'
        })()
        
        # Создаем мок репозитория
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = blocked_user
        
        pass_repo = AsyncMock()
        
        # Создаем сервис
        service = PassService(pass_repo, user_repo)
        
        # Пытаемся создать пропуск
        with pytest.raises(DatabaseError) as exc_info:
            asyncio.run(service.create_pass(1, "А123БВ777"))
        
        assert "Пользователь заблокирован до" in str(exc_info.value)
        assert "Нарушение правил" in str(exc_info.value)
    
    def test_expired_block_user_can_create_pass(self):
        """Тест что пользователь с истекшей блокировкой может создать пропуск"""
        from easy_pass_bot.services.pass_service import PassService
        from datetime import datetime, timedelta
        
        # Создаем мок пользователя с истекшей блокировкой
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        expired_blocked_user = type('User', (), {
            'id': 1,
            'status': 'blocked',
            'blocked_until': yesterday,
            'block_reason': 'Истекшая блокировка'
        })()
        
        # Создаем мок репозитория
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = expired_blocked_user
        
        pass_repo = AsyncMock()
        pass_repo.create.return_value = 1
        
        # Создаем сервис
        service = PassService(pass_repo, user_repo)
        
        # Пытаемся создать пропуск
        result = asyncio.run(service.create_pass(1, "А123БВ777"))
        
        # Должен создать пропуск успешно
        assert result is not None
        pass_repo.create.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
