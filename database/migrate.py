import os
import shutil
import sqlite3
from datetime import datetime

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_old_db_path():
    return os.path.join(get_project_root(), 'backend', 'data', 'attention.db')

def get_new_db_path():
    return os.path.join(get_project_root(), 'database', 'attention.db')

def get_backup_path():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(get_project_root(), 'database', f'attention_backup_{timestamp}.db')

def backup_database(db_path, backup_path):
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(db_path, backup_path)
    print(f"备份已创建: {backup_path}")
    return True

def migrate_database():
    old_db_path = get_old_db_path()
    new_db_path = get_new_db_path()
    
    if not os.path.exists(old_db_path):
        print(f"源数据库不存在: {old_db_path}")
        print("跳过迁移，将创建新数据库")
        return False
    
    if os.path.exists(new_db_path):
        backup_path = get_backup_path()
        backup_database(new_db_path, backup_path)
        os.remove(new_db_path)
        print(f"已删除旧目标数据库: {new_db_path}")
    
    os.makedirs(os.path.dirname(new_db_path), exist_ok=True)
    shutil.copy2(old_db_path, new_db_path)
    print(f"数据库已迁移: {old_db_path} -> {new_db_path}")
    
    backup_path = get_backup_path()
    backup_database(old_db_path, backup_path)
    
    return True

def verify_migration():
    old_db_path = get_old_db_path()
    new_db_path = get_new_db_path()
    
    if not os.path.exists(new_db_path):
        print("新数据库不存在")
        return False
    
    conn = sqlite3.connect(new_db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"数据库表数量: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} 条记录")
    
    conn.close()
    return True

def main():
    print("=" * 50)
    print("数据库迁移工具")
    print("=" * 50)
    
    print("\n步骤 1: 检查源数据库")
    old_db_path = get_old_db_path()
    if os.path.exists(old_db_path):
        print(f"源数据库存在: {old_db_path}")
    else:
        print(f"源数据库不存在: {old_db_path}")
    
    print("\n步骤 2: 迁移数据库")
    if migrate_database():
        print("迁移成功")
    else:
        print("无需迁移或迁移失败")
    
    print("\n步骤 3: 验证迁移")
    if verify_migration():
        print("验证成功")
    else:
        print("验证失败")
    
    print("\n" + "=" * 50)
    print("迁移完成")
    print("=" * 50)

if __name__ == '__main__':
    main()
