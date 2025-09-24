"""
Configuration for Easy Pass Bot bots
This module uses the unified settings system
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from easy_pass_bot.core.settings import settings

# Bot tokens
RESIDENT_BOT_TOKEN = settings.resident_bot_token
SECURITY_BOT_TOKEN = settings.security_bot_token

# Database
DATABASE_PATH = settings.database_path

# User roles
ROLES = settings.roles

# User statuses
USER_STATUSES = settings.user_statuses

# Pass statuses
PASS_STATUSES = settings.pass_statuses

# Limits
MAX_ACTIVE_PASSES = settings.max_active_passes

# Cache settings
CACHE_DEFAULT_TTL = settings.cache_default_ttl
CACHE_MAX_SIZE = settings.cache_max_size

# Retry settings
RETRY_MAX_ATTEMPTS = settings.retry_max_attempts
RETRY_BASE_DELAY = settings.retry_base_delay
RETRY_MAX_DELAY = settings.retry_max_delay

# Circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD = settings.circuit_breaker_failure_threshold
CIRCUIT_BREAKER_TIMEOUT = settings.circuit_breaker_timeout
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = settings.circuit_breaker_success_threshold

# Analytics
ANALYTICS_RETENTION_DAYS = settings.analytics_retention_days
ANALYTICS_BATCH_SIZE = settings.analytics_batch_size

# Confirmations
CONFIRMATION_TIMEOUT = settings.confirmation_timeout
CONFIRMATION_CLEANUP_INTERVAL = settings.confirmation_cleanup_interval

# Messages for residents
RESIDENT_MESSAGES = settings.messages

# Messages for security and admins
SECURITY_MESSAGES = settings.security_messages



