"""
数据库连接管理
"""

import sqlite3
from typing import Optional
from contextlib import contextmanager
from app.config import settings

class Database:
    """SQLite 数据库连接管理器"""
    
    @staticmethod
    @contextmanager
    def get_connection(db_path: Optional[str] = None):
        """
        获取数据库连接（上下文管理器）
        
        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stocks")
        """
        if db_path is None:
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_kline_connection():
        """获取K线数据库连接"""
        return Database.get_connection(settings.DATABASE_URL.replace("sqlite:///", ""))
    
    @staticmethod
    def get_fundamental_connection():
        """获取基本面数据库连接"""
        return Database.get_connection(settings.FUNDAMENTAL_DB_URL.replace("sqlite:///", ""))

# 便捷函数
def execute_query(query: str, params: tuple = (), db_type: str = "kline"):
    """
    执行 SQL 查询并返回结果
    
    Args:
        query: SQL 查询语句
        params: 查询参数
        db_type: 数据库类型 ('kline' 或 'fundamental')
    
    Returns:
        List[dict]: 查询结果列表
    """
    conn_func = Database.get_kline_connection if db_type == "kline" else Database.get_fundamental_connection
    
    with conn_func() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def execute_update(query: str, params: tuple = (), db_type: str = "kline"):
    """
    执行 SQL 更新语句
    
    Args:
        query: SQL 更新语句
        params: 更新参数
        db_type: 数据库类型
    
    Returns:
        int: 受影响的行数
    """
    conn_func = Database.get_kline_connection if db_type == "kline" else Database.get_fundamental_connection
    
    with conn_func() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount
