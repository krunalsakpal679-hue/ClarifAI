"""
Test settings for ClarifAI Django service.
Configures deterministic, fast, in-memory test environment.
"""
from .dev import *

# Fast, deterministic in-memory Celery execution for unit test suite
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
