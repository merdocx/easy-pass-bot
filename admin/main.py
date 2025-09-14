import os
import sys
import asyncio
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiosqlite
import logging

# Добавляем путь к основному проекту
sys.path.append('/root/easy_pass_bot/src')

from easy_pass_bot.database.models import User, Pass
from easy_pass_bot.database.database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Easy Pass Admin Panel", version="1.0.0")

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="/root/easy_pass_bot/admin/static"), name="static")
templates = Jinja2Templates(directory="/root/easy_pass_bot/admin/templates")


# Защищенные маршруты (требуют авторизации)
PROTECTED_ROUTES = {
    "/dashboard", "/users", "/passes", "/api/users", "/api/passes"
}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware для автоматического редиректа на логин"""
    # Проверяем только GET запросы к защищенным маршрутам
    if request.method == "GET" and request.url.path in PROTECTED_ROUTES:
        user = await get_current_user(request)
        if not user:
            # Для GET запросов сохраняем текущий URL
            current_url = str(request.url)
            redirect_url = f"/login?redirect={current_url}"
            return RedirectResponse(url=redirect_url, status_code=302)
    
    response = await call_next(request)
    return response

# Инициализация базы данных
db = Database('/root/easy_pass_bot/database/easy_pass.db')

# Секретный ключ для сессий (в продакшене должен быть в переменных окружения)
SECRET_KEY = "easy_pass_admin_secret_key_2024"
security = HTTPBearer(auto_error=False)

# Словарь для хранения активных сессий (в продакшене использовать Redis)
active_sessions: Dict[str, Dict[str, Any]] = {}

class AdminAuth:
    def __init__(self, database=None):
        # Подключение к базе данных
        self.db = database
    
    def normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона для авторизации"""
        try:
            from easy_pass_bot.utils.phone_normalizer import normalize_phone_number
            return normalize_phone_number(phone)
        except Exception as e:
            logger.error(f"Error normalizing phone {phone}: {e}")
            return phone
    
    async def verify_admin_credentials(self, phone: str, password: str) -> Optional['Admin']:
        """Проверка учетных данных администратора"""
        try:
            # Нормализуем номер телефона
            normalized_phone = self.normalize_phone(phone)
            
            # Ищем администратора по номеру телефона
            admin = await self.db.get_admin_by_phone(normalized_phone)
            if not admin:
                logger.warning(f"Admin not found for phone: {normalized_phone}")
                return None
            
            # Проверяем пароль
            if not bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
                logger.warning(f"Invalid password for admin: {admin.full_name}")
                return None
            
            # Проверяем, что связанный пользователь имеет роль admin
            user = await self.db.get_user_by_id(admin.user_id)
            if not user or user.role != 'admin':
                logger.warning(f"User {admin.user_id} is not admin role")
                return None
            
            # Обновляем время последнего входа
            await self.db.update_admin_last_login(admin.id)
            
            logger.info(f"Admin {admin.full_name} successfully authenticated")
            return admin
            
        except Exception as e:
            logger.error(f"Error verifying admin credentials: {e}")
            return None
    
    def create_admin_session(self, admin: 'Admin') -> str:
        """Создание сессии для администратора"""
        session_id = secrets.token_urlsafe(32)
        active_sessions[session_id] = {
            "admin_id": admin.id,
            "user_id": admin.user_id,
            "full_name": admin.full_name,
            "phone_number": admin.phone_number,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.info(f"Admin session created for {admin.full_name}")
        return session_id
    
    def verify_session(self, session_id: str) -> bool:
        """Проверка валидности сессии"""
        if session_id not in active_sessions:
            return False
        
        session = active_sessions[session_id]
        # Сессия истекает через 8 часов неактивности
        if datetime.now() - session["last_activity"] > timedelta(hours=8):
            del active_sessions[session_id]
            return False
        
        # Обновляем время последней активности
        active_sessions[session_id]["last_activity"] = datetime.now()
        return True
    
    def get_session_admin(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных администратора из сессии"""
        if session_id in active_sessions:
            return active_sessions[session_id]
        return None
    
    def get_session_user_id(self, session_id: str) -> Optional[int]:
        """Получение user_id из сессии (для обратной совместимости)"""
        session = self.get_session_admin(session_id)
        return session.get("user_id") if session else None
    
    # Методы для обратной совместимости (будут удалены в будущем)
    def verify_password(self, password: str) -> bool:
        """УСТАРЕВШИЙ МЕТОД - используется только для совместимости"""
        logger.warning("Using deprecated verify_password method")
        return False
    
    def create_session(self, username: str) -> str:
        """УСТАРЕВШИЙ МЕТОД - используется только для совместимости"""
        logger.warning("Using deprecated create_session method")
        return ""
    
    def get_session_user(self, session_id: str) -> Optional[str]:
        """УСТАРЕВШИЙ МЕТОД - используется только для совместимости"""
        session = self.get_session_admin(session_id)
        return session.get("full_name") if session else None

admin_auth = AdminAuth(db)

async def get_current_user(request: Request) -> Optional[str]:
    """Получение текущего пользователя из сессии (для обратной совместимости)"""
    session_id = request.cookies.get("admin_session")
    if not session_id or not admin_auth.verify_session(session_id):
        return None
    return admin_auth.get_session_user(session_id)

async def get_current_admin(request: Request) -> Optional[Dict[str, Any]]:
    """Получение данных текущего администратора из сессии"""
    session_id = request.cookies.get("admin_session")
    if not session_id or not admin_auth.verify_session(session_id):
        return None
    return admin_auth.get_session_admin(session_id)

async def require_auth_dependency(request: Request):
    """Проверка авторизации для использования в Depends"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

async def require_auth_redirect(request: Request):
    """Проверка авторизации с автоматическим редиректом"""
    user = await get_current_user(request)
    if not user:
        # Получаем текущий URL для редиректа после авторизации
        current_url = str(request.url)
        redirect_url = f"/login?redirect={current_url}"
        return RedirectResponse(url=redirect_url, status_code=302)
    return user

async def check_auth_for_post(request: Request):
    """Проверка авторизации для POST запросов с редиректом"""
    user = await get_current_user(request)
    if not user:
        # Для POST запросов редиректим на соответствующую GET страницу
        if request.url.path.startswith("/users"):
            redirect_url = "/login?redirect=http://89.110.96.90:8080/users"
        elif request.url.path.startswith("/passes"):
            redirect_url = "/login?redirect=http://89.110.96.90:8080/passes"
        else:
            redirect_url = "/login?redirect=http://89.110.96.90:8080/dashboard"
        return RedirectResponse(url=redirect_url, status_code=302)
    return user

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница авторизации"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    # Получаем redirect параметр
    redirect_url = request.query_params.get("redirect", "/dashboard")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect_url": redirect_url
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page_alt(request: Request):
    """Альтернативная страница авторизации"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    # Получаем redirect параметр
    redirect_url = request.query_params.get("redirect", "/dashboard")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect_url": redirect_url
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), redirect_url: str = Form("/dashboard")):
    """Обработка авторизации"""
    
    try:
        # Нормализуем username (номер телефона) и проверяем учетные данные
        admin = await admin_auth.verify_admin_credentials(username, password)
        
        if admin:
            # Создаем сессию для администратора
            session_id = admin_auth.create_admin_session(admin)
            response = RedirectResponse(url=redirect_url, status_code=302)
            response.set_cookie(
                key="admin_session",
                value=session_id,
                httponly=True,
                secure=False,  # В продакшене должно быть True
                samesite="lax",
                max_age=8 * 60 * 60  # 8 часов
            )
            logger.info(f"Admin {admin.full_name} logged in successfully")
            return response
        else:
            logger.warning(f"Failed login attempt with username: {username}")
            return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Неверные учетные данные",
                    "redirect_url": redirect_url
                }
            )
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Ошибка сервера",
                "redirect_url": redirect_url
            }
        )

@app.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    session_id = request.cookies.get("admin_session")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("admin_session")
    logger.info("Admin logged out")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(require_auth_dependency)):
    """Главная страница админки"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/dashboard", response_class=HTMLResponse)
async def dashboard_post(request: Request, current_user: str = Depends(require_auth_dependency)):
    """Обработка POST запросов на dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request, 
    current_user: str = Depends(require_auth_dependency)
):
    """Страница управления пользователями"""
    try:
        # Получаем всех пользователей для статистики
        all_users = await db.get_all_users()
        
        # Статистика
        total_users = len(all_users)
        pending_users = len([u for u in all_users if u.status == 'pending'])
        approved_users = len([u for u in all_users if u.status == 'approved'])
        rejected_users = len([u for u in all_users if u.status == 'rejected'])
        blocked_users = len([u for u in all_users if u.status == 'blocked'])
        
        # Для таблицы загружаем только первые 20 пользователей
        users = all_users[:20] if all_users else []
        
        return templates.TemplateResponse("users.html", {
            "request": request,
            "current_user": current_user,
            "users": users,
            "total_users": total_users,
            "pending_users": pending_users,
            "approved_users": approved_users,
            "rejected_users": rejected_users,
            "blocked_users": blocked_users,
            "has_more": len(all_users) > 20 if all_users else False
        })
    except Exception as e:
        logger.error(f"Error loading users page: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки страницы пользователей")

@app.post("/users/{user_id}/status")
async def update_user_status(
    request: Request,
    user_id: int,
    status: str = Form(...)
):
    """Обновление статуса пользователя"""
    # Проверка аутентификации с редиректом
    auth_result = await check_auth_for_post(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    current_user = auth_result
    
    try:
        if status not in ['pending', 'approved', 'rejected']:
            raise HTTPException(status_code=400, detail="Неверный статус")
        
        await db.update_user_status(user_id, status)
        logger.info(f"Admin {current_user} updated user {user_id} status to {status}")
        
        return RedirectResponse(url="/users", status_code=302)
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса")

@app.get("/passes", response_class=HTMLResponse)
async def passes_page(
    request: Request,
    current_user: str = Depends(require_auth_dependency)
):
    """Страница просмотра пропусков"""
    try:
        # Получаем все пропуски для статистики
        all_passes = await db.get_all_passes()
        
        # Статистика
        total_passes = len(all_passes)
        active_passes = len([p for p in all_passes if p.status == 'active'])
        used_passes = len([p for p in all_passes if p.status == 'used'])
        cancelled_passes = len([p for p in all_passes if p.status == 'cancelled'])
        
        # Для таблицы загружаем только первые 20 пропусков
        passes = all_passes[:20] if all_passes else []
        
        # Получаем информацию о пользователях для каждого пропуска
        passes_with_users = []
        for pass_obj in passes:
            user = await db.get_user_by_id(pass_obj.user_id)
            passes_with_users.append({
                "pass": pass_obj,
                "user": user
            })
        
        return templates.TemplateResponse("passes.html", {
            "request": request,
            "current_user": current_user,
            "passes_with_users": passes_with_users,
            "total_passes": total_passes,
            "active_passes": active_passes,
            "used_passes": used_passes,
            "cancelled_passes": cancelled_passes,
            "has_more": len(all_passes) > 20 if all_passes else False
        })
    except Exception as e:
        logger.error(f"Error loading passes page: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки страницы пропусков")

@app.get("/api/users")
async def api_get_users(
    current_user: str = Depends(require_auth_dependency),
    offset: int = 0,
    limit: int = 20,
    search: str = None
):
    """API для получения списка пользователей с пагинацией и поиском"""
    try:
        users = await db.get_all_users()
        
        # Применяем поиск если указан
        if search and search.strip():
            search_term = search.strip().lower()
            filtered_users = []
            for user in users:
                # Поиск по ФИО, телефону, квартире, Telegram ID
                if (search_term in user.full_name.lower() or
                    search_term in user.phone_number.lower() or
                    search_term in (user.apartment or "").lower() or
                    search_term in str(user.telegram_id) or
                    search_term in str(user.id)):
                    filtered_users.append(user)
            users = filtered_users
        
        total_count = len(users)
        
        # Применяем пагинацию
        paginated_users = users[offset:offset + limit]
        
        return {
            "users": [user.__dict__ for user in paginated_users],
            "total_count": total_count,
            "has_more": offset + limit < total_count,
            "search_term": search
        }
    except Exception as e:
        logger.error(f"Error getting users via API: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователей")

@app.get("/api/passes")
async def api_get_passes(
    current_user: str = Depends(require_auth_dependency),
    offset: int = 0,
    limit: int = 20,
    search: str = None
):
    """API для получения списка пропусков с пагинацией и поиском"""
    try:
        passes = await db.get_all_passes()
        
        # Применяем поиск если указан
        if search and search.strip():
            search_term = search.strip().lower()
            filtered_passes = []
            for pass_obj in passes:
                # Получаем информацию о пользователе для поиска
                user = await db.get_user_by_id(pass_obj.user_id)
                
                # Поиск по номеру автомобиля, ФИО владельца, телефону, квартире, ID пропуска
                if (search_term in pass_obj.car_number.lower() or
                    search_term in str(pass_obj.id) or
                    (user and (
                        search_term in user.full_name.lower() or
                        search_term in user.phone_number.lower() or
                        search_term in (user.apartment or "").lower()
                    ))):
                    filtered_passes.append(pass_obj)
            passes = filtered_passes
        
        total_count = len(passes)
        
        # Применяем пагинацию
        paginated_passes = passes[offset:offset + limit]
        
        # Получаем информацию о пользователях для каждого пропуска
        passes_with_users = []
        for pass_obj in paginated_passes:
            user = await db.get_user_by_id(pass_obj.user_id)
            passes_with_users.append({
                "pass": pass_obj.__dict__,
                "user": user.__dict__ if user else None
            })
        
        return {
            "passes_with_users": passes_with_users,
            "total_count": total_count,
            "has_more": offset + limit < total_count,
            "search_term": search
        }
    except Exception as e:
        logger.error(f"Error getting passes via API: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пропусков")

@app.post("/users/{user_id}/block")
async def block_user(
    request: Request,
    user_id: int,
    blocked_until: str = Form(...),
    block_reason: str = Form(...)
):
    """Блокировка пользователя"""
    # Проверка аутентификации с редиректом
    auth_result = await check_auth_for_post(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    current_user = auth_result
    
    try:
        await db.block_user(user_id, blocked_until, block_reason)
        logger.info(f"Admin {current_user} blocked user {user_id} until {blocked_until}")
        return RedirectResponse(url="/users", status_code=302)
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(status_code=500, detail="Ошибка блокировки пользователя")

@app.post("/users/{user_id}/unblock")
async def unblock_user(
    request: Request,
    user_id: int
):
    """Разблокировка пользователя"""
    # Проверка аутентификации с редиректом
    auth_result = await check_auth_for_post(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    current_user = auth_result
    
    try:
        await db.unblock_user(user_id)
        logger.info(f"Admin {current_user} unblocked user {user_id}")
        return RedirectResponse(url="/users", status_code=302)
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        raise HTTPException(status_code=500, detail="Ошибка разблокировки пользователя")

@app.post("/users/{user_id}/role")
async def change_user_role(
    request: Request,
    user_id: int,
    new_role: str = Form(...),
    current_user: str = Depends(require_auth_dependency)
):
    """Изменение роли пользователя"""
    try:
        # Проверяем, что текущий пользователь - админ
        current_user_obj = await db.get_user_by_username(current_user)
        if not current_user_obj or current_user_obj.role != 'admin':
            logger.warning(f"Non-admin user {current_user} attempted to change role")
            raise HTTPException(status_code=403, detail="Только администраторы могут изменять роли")
        
        # Получаем пользователя для изменения роли
        user = await db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем валидность новой роли
        valid_roles = ['resident', 'security', 'admin']
        if new_role not in valid_roles:
            raise HTTPException(status_code=400, detail="Недопустимая роль")
        
        # Проверяем, что админ не может изменить роль другого админа только если пытается повысить до admin
        # Но может понижать других админов до resident или security
        if user.role == 'admin' and current_user_obj.id != user.id and new_role == 'admin':
            logger.warning(f"Admin {current_user} attempted to promote another admin to admin role")
            raise HTTPException(status_code=403, detail="Нельзя назначить роль администратора другому администратору")
        
        # Проверяем, что админ не может изменить свою роль
        if current_user_obj.id == user.id:
            logger.warning(f"Admin {current_user} attempted to change their own role")
            raise HTTPException(status_code=403, detail="Нельзя изменить собственную роль")
        
        # Сохраняем старую роль для логирования
        old_role = user.role
        
        # Изменяем роль
        await db.change_user_role(user_id, new_role)
        
        # Если роль изменилась с admin на другую, деактивируем админа
        if old_role == 'admin' and new_role != 'admin':
            try:
                # Деактивируем админа
                await db.deactivate_admin(user_id)
                logger.info(f"Deactivated admin for user {user.full_name} (ID: {user_id}) after role change to {new_role}")
            except Exception as e:
                logger.error(f"Failed to deactivate admin for user {user_id}: {e}")
        
        # Если роль изменилась на admin, создаем админа и отправляем уведомление
        if new_role == 'admin':
            try:
                # Проверяем, есть ли уже админ с этим user_id
                existing_admin = await db.get_admin_by_user_id(user_id)
                if not existing_admin:
                    # Создаем нового админа
                    from easy_pass_bot.utils.password_generator import generate_secure_password, hash_password
                    from easy_pass_bot.utils.telegram_notifier import TelegramNotifier
                    
                    # Генерируем пароль
                    password = generate_secure_password()
                    password_hash = hash_password(password)
                    
                    # Нормализуем номер телефона
                    from easy_pass_bot.utils.phone_normalizer import normalize_phone_number
                    normalized_phone = normalize_phone_number(user.phone_number)
                    
                    # Создаем админа
                    from easy_pass_bot.database.models import Admin
                    
                    new_admin = Admin(
                        username=normalized_phone,
                        full_name=user.full_name,
                        password_hash=password_hash,
                        role='admin',
                        is_active=True,
                        user_id=user_id,
                        phone_number=normalized_phone
                    )
                    
                    admin_id = await db.create_admin(
                        username=new_admin.username,
                        full_name=new_admin.full_name,
                        password_hash=new_admin.password_hash,
                        user_id=new_admin.user_id,
                        phone_number=new_admin.phone_number,
                        role=new_admin.role
                    )
                    logger.info(f"Created admin record for user {user.full_name} (ID: {user_id}) with admin ID {admin_id}")
                    
                    # Отправляем уведомление в Telegram
                    try:
                        bot_token = os.getenv('BOT_TOKEN')
                        if bot_token:
                            notifier = TelegramNotifier(bot_token)
                            admin_url = f"http://{request.headers.get('host', 'localhost:8000')}"
                            
                            # Отправляем приветствие
                            await notifier.send_admin_welcome(
                                user.telegram_id, 
                                user.full_name
                            )
                            
                            # Отправляем учетные данные
                            await notifier.send_admin_credentials(
                                user.telegram_id,
                                user.full_name,
                                normalized_phone,
                                password
                            )
                            
                            logger.info(f"Sent admin credentials to user {user.full_name} (Telegram ID: {user.telegram_id})")
                        else:
                            logger.warning("BOT_TOKEN not found, cannot send Telegram notification")
                    except Exception as e:
                        logger.error(f"Failed to send Telegram notification: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to create admin for user {user_id}: {e}")
        
        # Отправляем уведомление о смене роли (для всех ролей кроме admin, так как для admin уже отправлены специальные уведомления)
        if new_role != 'admin':
            try:
                bot_token = os.getenv('BOT_TOKEN')
                if bot_token and user.telegram_id:
                    from easy_pass_bot.utils.telegram_notifier import TelegramNotifier
                    notifier = TelegramNotifier(bot_token)
                    
                    await notifier.send_role_change_notification(
                        user.telegram_id,
                        user.full_name,
                        old_role,
                        new_role
                    )
                    
                    logger.info(f"Sent role change notification to user {user.full_name} (Telegram ID: {user.telegram_id}): {old_role} -> {new_role}")
                else:
                    if not bot_token:
                        logger.warning("BOT_TOKEN not found, cannot send role change notification")
                    if not user.telegram_id:
                        logger.warning(f"User {user.full_name} has no Telegram ID, cannot send role change notification")
            except Exception as e:
                logger.error(f"Failed to send role change notification to user {user_id}: {e}")
        
        # Логируем изменение роли
        logger.info(f"Admin {current_user} (ID: {current_user_obj.id}) changed user {user.full_name} (ID: {user_id}) role from '{old_role}' to '{new_role}'")
        
        return RedirectResponse(url="/users", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing user {user_id} role: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения роли пользователя")

@app.post("/users/{user_id}/delete")
async def delete_user(
    request: Request,
    user_id: int
):
    """Удаление пользователя"""
    # Проверка аутентификации с редиректом
    auth_result = await check_auth_for_post(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    current_user = auth_result
    
    try:
        await db.delete_user(user_id)
        logger.info(f"Admin {current_user} deleted user {user_id}")
        return RedirectResponse(url="/users", status_code=302)
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления пользователя")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        log_level="info"
    )
