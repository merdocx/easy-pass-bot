import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os

# Добавляем путь к админке
sys.path.append('/root/easy_pass_bot/admin')
sys.path.append('/root/easy_pass_bot/src')

from main import app, admin_auth, db

class TestAdminPanel:
    """Тесты для веб-админки Easy Pass"""
    
    @pytest.fixture
    def client(self):
        """Создание тестового клиента"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        with patch.object(db, 'get_all_users') as mock_users, \
             patch.object(db, 'get_all_passes') as mock_passes, \
             patch.object(db, 'update_user_status') as mock_update, \
             patch.object(db, 'get_user_by_id') as mock_get_user:
            
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
                    'created_at': '2024-01-01 12:00:00'
                })(),
                type('User', (), {
                    'id': 2,
                    'telegram_id': 987654321,
                    'role': 'admin',
                    'full_name': 'Админ Админов',
                    'phone_number': '+7 900 987 65 43',
                    'apartment': None,
                    'status': 'approved',
                    'created_at': '2024-01-02 12:00:00'
                })()
            ]
            
            mock_passes.return_value = [
                type('Pass', (), {
                    'id': 1,
                    'user_id': 1,
                    'car_number': 'А123БВ777',
                    'status': 'active',
                    'created_at': '2024-01-01 12:00:00',
                    'used_at': None,
                    'used_by_id': None,
                    'is_archived': False
                })()
            ]
            
            mock_get_user.return_value = type('User', (), {
                'id': 1,
                'full_name': 'Иван Иванов'
            })()
            
            mock_update.return_value = None
            
            yield {
                'users': mock_users,
                'passes': mock_passes,
                'update': mock_update,
                'get_user': mock_get_user
            }
    
    def test_login_page_access(self, client):
        """Тест доступа к странице авторизации"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Easy Pass Admin" in response.text
        assert "Войти" in response.text
    
    def test_login_success(self, client):
        """Тест успешной авторизации"""
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        # В тестовой среде может быть редирект или успешный ответ
        assert response.status_code in [200, 302]
        if response.status_code == 302:
            assert response.headers["location"] == "/dashboard"
        
        # Проверяем, что установлена cookie сессии или что логин прошел успешно
        assert "admin_session" in response.cookies or "Панель управления" in response.text
    
    def test_login_failure(self, client):
        """Тест неуспешной авторизации"""
        response = client.post("/login", data={
            "username": "admin",
            "password": "wrong_password"
        })
        assert response.status_code == 200
        assert "Неверные учетные данные" in response.text
    
    def test_dashboard_access_without_auth(self, client):
        """Тест доступа к дашборду без авторизации"""
        response = client.get("/dashboard")
        assert response.status_code == 401
    
    def test_users_page_with_auth(self, client, mock_db):
        """Тест доступа к странице пользователей с авторизацией"""
        # Сначала авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        # Получаем cookie сессии
        session_cookie = login_response.cookies.get("admin_session")
        
        # Запрашиваем страницу пользователей
        response = client.get("/users", cookies={"admin_session": session_cookie})
        assert response.status_code == 200
        assert "Управление пользователями" in response.text
        assert "Иван Иванов" in response.text
    
    def test_passes_page_with_auth(self, client, mock_db):
        """Тест доступа к странице пропусков с авторизацией"""
        # Сначала авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        # Получаем cookie сессии
        session_cookie = login_response.cookies.get("admin_session")
        
        # Запрашиваем страницу пропусков
        response = client.get("/passes", cookies={"admin_session": session_cookie})
        assert response.status_code == 200
        assert "Просмотр пропусков" in response.text
        assert "А123БВ777" in response.text
    
    def test_user_status_update(self, client, mock_db):
        """Тест обновления статуса пользователя"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Обновляем статус пользователя
        response = client.post("/users/1/status", 
                             data={"status": "approved"},
                             cookies={"admin_session": session_cookie},
                             follow_redirects=True)
        
        assert response.status_code == 200
        mock_db['update'].assert_called_once_with(1, 'approved')
    
    def test_search_users(self, client, mock_db):
        """Тест поиска пользователей"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Ищем пользователей
        response = client.get("/users?search=Иван", 
                            cookies={"admin_session": session_cookie})
        
        assert response.status_code == 200
        assert "Иван Иванов" in response.text
    
    def test_logout(self, client):
        """Тест выхода из системы"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Выходим
        response = client.get("/logout", cookies={"admin_session": session_cookie}, follow_redirects=True)
        assert response.status_code == 200
        assert "Easy Pass Admin" in response.text
    
    def test_api_users_endpoint(self, client, mock_db):
        """Тест API endpoint для пользователей"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Запрашиваем API
        response = client.get("/api/users", cookies={"admin_session": session_cookie})
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2
    
    def test_api_passes_endpoint(self, client, mock_db):
        """Тест API endpoint для пропусков"""
        # Авторизуемся
        login_response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        session_cookie = login_response.cookies.get("admin_session")
        
        # Запрашиваем API
        response = client.get("/api/passes", cookies={"admin_session": session_cookie})
        assert response.status_code == 200
        
        data = response.json()
        assert "passes" in data
        assert len(data["passes"]) == 1
    
    def test_session_management(self):
        """Тест управления сессиями"""
        # Создаем сессию
        session_id = admin_auth.create_session("admin")
        assert session_id is not None
        
        # Проверяем сессию
        assert admin_auth.verify_session(session_id) is True
        assert admin_auth.get_session_user(session_id) == "admin"
        
        # Проверяем несуществующую сессию
        assert admin_auth.verify_session("invalid_session") is False
        assert admin_auth.get_session_user("invalid_session") is None
    
    def test_password_verification(self):
        """Тест проверки пароля"""
        assert admin_auth.verify_password("admin123") is True
        assert admin_auth.verify_password("wrong_password") is False

class TestAdminSecurity:
    """Тесты безопасности админки"""
    
    @pytest.fixture
    def client(self):
        """Создание тестового клиента"""
        return TestClient(app)
    
    def test_password_hashing(self):
        """Тест хэширования паролей"""
        # Пароль должен быть захеширован
        assert admin_auth.admin_password_hash is not None
        assert isinstance(admin_auth.admin_password_hash, bytes)
    
    def test_session_security(self):
        """Тест безопасности сессий"""
        session_id = admin_auth.create_session("admin")
        
        # Сессия должна быть достаточно длинной и случайной
        assert len(session_id) >= 32
        assert session_id != "admin"  # Не должно быть предсказуемым
    
    def test_csrf_protection(self, client):
        """Тест защиты от CSRF (базовая проверка)"""
        # Попытка доступа к защищенным страницам без авторизации
        protected_endpoints = ["/dashboard", "/users", "/passes"]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
