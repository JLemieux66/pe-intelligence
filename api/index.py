"""
Vercel entry point for FastAPI application
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api_v2 import app

# Export for Vercel
__all__ = ['app']
