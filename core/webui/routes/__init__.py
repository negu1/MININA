"""
Routes package initialization
"""
from . import dashboard
from . import pc_explorer
from . import bot_config
from . import llm_config
from . import skills
from . import chat
from . import backup
from . import logs
from . import marketplace
from . import credentials

__all__ = [
    'dashboard',
    'pc_explorer',
    'bot_config',
    'llm_config',
    'skills',
    'chat',
    'backup',
    'logs',
    'marketplace',
    'credentials',
]
