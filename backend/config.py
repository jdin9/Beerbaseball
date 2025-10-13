import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'beerbaseball.db'}")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
