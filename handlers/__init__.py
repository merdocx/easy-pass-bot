from .resident_handlers import register_resident_handlers
from .security_handlers import register_security_handlers
from .admin_handlers import register_admin_handlers
from .common_handlers import register_common_handlers

__all__ = [
    'register_resident_handlers',
    'register_security_handlers', 
    'register_admin_handlers',
    'register_common_handlers'
]






