import os
import sys
import asyncio
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
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
    def __init__(self):
        # Хэш пароля по умолчанию: admin123
        self.admin_password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.admin_password_hash)
    
    def create_session(self, username: str) -> str:
        session_id = secrets.token_urlsafe(32)
        active_sessions[session_id] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        return session_id
    
    def verify_session(self, session_id: str) -> bool:
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
    
    def get_session_user(self, session_id: str) -> Optional[str]:
        if session_id in active_sessions:
            return active_sessions[session_id]["username"]
        return None

admin_auth = AdminAuth()

async def get_current_user(request: Request) -> Optional[str]:
    """Получение текущего пользователя из сессии"""
    session_id = request.cookies.get("admin_session")
    if not session_id or not admin_auth.verify_session(session_id):
        return None
    return admin_auth.get_session_user(session_id)

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
    
    if username == "admin" and admin_auth.verify_password(password):
        session_id = admin_auth.create_session(username)
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="admin_session",
            value=session_id,
            httponly=True,
            secure=False,  # В продакшене должно быть True
            samesite="lax",
            max_age=8 * 60 * 60  # 8 часов
        )
        logger.info(f"Admin {username} logged in successfully")
        return response
    else:
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": "Неверные учетные данные",
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
    current_user: str = Depends(require_auth_dependency),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None
):
    """Страница управления пользователями"""
    try:
        users = await db.get_all_users()
        
        # Фильтрация пользователей
        if search:
            users = [u for u in users if search.lower() in u.full_name.lower() 
                    or search in str(u.telegram_id) 
                    or search in u.phone_number]
        
        if status_filter:
            users = [u for u in users if u.status == status_filter]
        
        if role_filter:
            users = [u for u in users if u.role == role_filter]
        
        # Статистика
        all_users = await db.get_all_users()
        total_users = len(all_users)
        pending_users = len([u for u in all_users if u.status == 'pending'])
        approved_users = len([u for u in all_users if u.status == 'approved'])
        rejected_users = len([u for u in all_users if u.status == 'rejected'])
        blocked_users = len([u for u in all_users if u.status == 'blocked'])
        
        return templates.TemplateResponse("users.html", {
            "request": request,
            "current_user": current_user,
            "users": users,
            "search": search or "",
            "status_filter": status_filter or "",
            "role_filter": role_filter or "",
            "total_users": total_users,
            "pending_users": pending_users,
            "approved_users": approved_users,
            "rejected_users": rejected_users,
            "blocked_users": blocked_users
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
    current_user: str = Depends(require_auth_dependency),
    search: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """Страница просмотра пропусков"""
    try:
        passes = await db.get_all_passes()
        
        # Фильтрация пропусков
        if search:
            passes = [p for p in passes if search.lower() in p.car_number.lower()]
        
        if status_filter:
            passes = [p for p in passes if p.status == status_filter]
        
        # Получаем информацию о пользователях для каждого пропуска
        passes_with_users = []
        for pass_obj in passes:
            user = await db.get_user_by_id(pass_obj.user_id)
            passes_with_users.append({
                "pass": pass_obj,
                "user": user
            })
        
        # Статистика
        total_passes = len(await db.get_all_passes())
        active_passes = len([p for p in passes if p.status == 'active'])
        used_passes = len([p for p in passes if p.status == 'used'])
        cancelled_passes = len([p for p in passes if p.status == 'cancelled'])
        
        return templates.TemplateResponse("passes.html", {
            "request": request,
            "current_user": current_user,
            "passes_with_users": passes_with_users,
            "search": search or "",
            "status_filter": status_filter or "",
            "total_passes": total_passes,
            "active_passes": active_passes,
            "used_passes": used_passes,
            "cancelled_passes": cancelled_passes
        })
    except Exception as e:
        logger.error(f"Error loading passes page: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки страницы пропусков")

@app.get("/api/users")
async def api_get_users(current_user: str = Depends(require_auth_dependency)):
    """API для получения списка пользователей"""
    try:
        users = await db.get_all_users()
        return {"users": [user.__dict__ for user in users]}
    except Exception as e:
        logger.error(f"Error getting users via API: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователей")

@app.get("/api/passes")
async def api_get_passes(current_user: str = Depends(require_auth_dependency)):
    """API для получения списка пропусков"""
    try:
        passes = await db.get_all_passes()
        return {"passes": [pass_obj.__dict__ for pass_obj in passes]}
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
