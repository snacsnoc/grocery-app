# config.py
import os

class Config:
    DEBUG = os.getenv("DEBUG_MODE")
    OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
    MEMCACHED_SERVER = os.getenv("MEMCACHED_SERVER")
    CACHE_DIR = "cache"
