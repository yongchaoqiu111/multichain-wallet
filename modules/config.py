"""
配置管理模块 - 支持多环境配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """全局配置类"""
    
    # API服务配置
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 5001))
    
    # 域名配置
    DOMAIN = os.getenv('DOMAIN', 'localhost')
    PROTOCOL = os.getenv('PROTOCOL', 'http')
    
    # 调试模式
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # 数据库配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'wallet_backup')
    
    @staticmethod
    def get_api_base_url():
        """获取API基础URL（用于客户端）"""
        return f"{Config.PROTOCOL}://{Config.DOMAIN}:{Config.API_PORT}/api"
    
    @staticmethod
    def get_local_api_url():
        """获取本地API URL（用于桌面端）"""
        return f"http://127.0.0.1:{Config.API_PORT}/api"
    
    @staticmethod
    def get_db_config():
        """获取数据库配置字典"""
        return {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4'
        }
