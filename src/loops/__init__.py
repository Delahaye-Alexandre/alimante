"""
Boucles principales pour Alimante
Orchestration du fonctionnement continu du système
"""

from .main_loop import MainLoop
from .watchdog import Watchdog

__all__ = [
    'MainLoop',
    'Watchdog'
]