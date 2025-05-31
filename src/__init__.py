"""
QuantFlow package initialization
"""

__version__ = "0.1.0"
__author__ = "QuantFlow Team"
__description__ = "High-performance algorithmic trading system"

from .engine import QuantFlowEngine
from .config import config

__all__ = ['QuantFlowEngine', 'config']
