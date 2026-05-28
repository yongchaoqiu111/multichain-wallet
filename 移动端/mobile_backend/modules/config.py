"""
配置管理模块 - 移动端后端专用
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5001))
    
    DOMAIN = os.getenv('DOMAIN', 'localhost')
    PROTOCOL = os.getenv('PROTOCOL', 'http')
    
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'wallet_backup')
    
    @staticmethod
    def get_api_base_url():
        return f"{Config.PROTOCOL}://{Config.DOMAIN}:{Config.API_PORT}/api"
    
    @staticmethod
    def get_local_api_url():
        return f"http://127.0.0.1:{Config.API_PORT}/api"
    
    @staticmethod
    def get_db_config():
        return {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4'
        }
