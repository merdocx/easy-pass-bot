// Основной JavaScript файл для админки

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация
    initializeApp();
    
    // Обработчики событий
    setupEventListeners();
    
    // Автоматическое обновление данных
    setupAutoRefresh();
});

function initializeApp() {
    console.log('Easy Pass Admin Panel initialized');
    
    // Проверка сессии
    checkSession();
    
    // Настройка уведомлений
    setupNotifications();
}

function setupEventListeners() {
    // Поиск в реальном времени
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Можно добавить AJAX поиск в будущем
            }, 300);
        });
    });
    
    // Подтверждение действий
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Автосохранение фильтров
    const filterForm = document.querySelector('.filters-form');
    if (filterForm) {
        const inputs = filterForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            // Восстановление значений из localStorage
            const key = `filter_${input.name}`;
            const savedValue = localStorage.getItem(key);
            if (savedValue && input.type !== 'password') {
                input.value = savedValue;
            }
            
            // Сохранение при изменении
            input.addEventListener('change', function() {
                localStorage.setItem(key, this.value);
            });
        });
    }
}

function checkSession() {
    // Проверка активности сессии
    let lastActivity = Date.now();
    
    document.addEventListener('click', () => {
        lastActivity = Date.now();
    });
    
    document.addEventListener('keypress', () => {
        lastActivity = Date.now();
    });
    
    // Проверка каждые 5 минут
    setInterval(() => {
        const now = Date.now();
        const timeSinceActivity = now - lastActivity;
        
        // Если неактивность больше 7 часов (25,200,000 мс)
        if (timeSinceActivity > 25200000) {
            showNotification('Сессия истекла. Пожалуйста, войдите снова.', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
    }, 300000); // 5 минут
}

function setupAutoRefresh() {
    // Автообновление данных каждые 30 секунд
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            refreshStats();
        }
    }, 30000);
}

function refreshStats() {
    // Обновление статистики без перезагрузки страницы
    const currentPath = window.location.pathname;
    
    if (currentPath === '/users' || currentPath === '/passes') {
        // Можно добавить AJAX запросы для обновления статистики
        console.log('Refreshing stats...');
    }
}

function setupNotifications() {
    // Создание контейнера для уведомлений
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
    `;
    document.body.appendChild(notificationContainer);
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: white;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Цвета для разных типов уведомлений
    const colors = {
        info: '#06b6d4',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444'
    };
    
    notification.style.borderLeftColor = colors[type] || colors.info;
    
    // Иконки для разных типов
    const icons = {
        info: 'fas fa-info-circle',
        success: 'fas fa-check-circle',
        warning: 'fas fa-exclamation-triangle',
        error: 'fas fa-times-circle'
    };
    
    notification.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
            <i class="${icons[type] || icons.info}" style="color: ${colors[type] || colors.info}; margin-top: 0.125rem;"></i>
            <div style="flex: 1;">
                <p style="margin: 0; font-size: 0.875rem; color: #1e293b;">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: #64748b; cursor: pointer; padding: 0;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Автоматическое удаление
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }
    }, duration);
}

// Добавление CSS анимаций
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Утилиты
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPhone(phone) {
    if (!phone) return '-';
    // Простое форматирование телефона
    return phone.replace(/(\d{1})(\d{3})(\d{3})(\d{2})(\d{2})/, '+$1 ($2) $3-$4-$5');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Экспорт функций для использования в HTML
window.showNotification = showNotification;
window.formatDate = formatDate;
window.formatPhone = formatPhone;
