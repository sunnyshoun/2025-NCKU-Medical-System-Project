import json
import psycopg2
from psycopg2.extras import execute_values
import os

def load_json(file_path):
    """讀取 JSON 文件並返回數據"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

def connect_db():
    """連接到 PostgreSQL 資料庫"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=os.getenv('POSTGRES_PORT', 5432),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'mysecretpassword'),
            database='postgres'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def insert_knowledge(conn, knowledge_data):
    """將知識點數據插入 knowledges 表"""
    if not knowledge_data:
        print("No knowledge data to insert.")
        return

    try:
        cursor = conn.cursor()
        # 準備插入語句
        query = """
            INSERT INTO knowledges (knowledge_id, knowledge_point, tags, summary, source)
            VALUES %s
            ON CONFLICT (knowledge_id) DO NOTHING
        """
        # 格式化數據
        values = [
            (
                item['id'],
                item['knowledge_point'].replace("'", "''"),  # 轉義單引號
                item['tags'],
                item['summary'].replace("'", "''"),  # 轉義單引號
                item['source']
            )
            for item in knowledge_data
        ]
        # 批量插入
        execute_values(cursor, query, values)
        conn.commit()
        print(f"Inserted {len(values)} knowledge points successfully.")
    except Exception as e:
        print(f"Error inserting knowledge data: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    # JSON 文件路徑
    json_file = os.getenv('KNOWLEDGE_JSON_PATH', '/app/data/vision_health_knowledge_base.json')
    # 讀取 JSON
    knowledge_data = load_json(json_file)
    # 連接到資料庫
    conn = connect_db()
    if conn:
        try:
            # 插入數據
            insert_knowledge(conn, knowledge_data)
        finally:
            conn.close()

if __name__ == "__main__":
    main()