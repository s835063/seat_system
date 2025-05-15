import sqlite3  # 匯入 SQLite 模組

# 1. 連接到 SQLite 資料庫（檔名叫 database.db，如果沒有會自動建立）
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 2. 建立 users 資料表（如果還沒有的話）
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

# 3. 批量新增學生帳號的函式
def add_students(start_num, end_num):
    for i in range(start_num, end_num + 1):
        username = f'student{i:02d}'  # 產生 student01、student02...這種格式
        password = f'pass{i:03d}'      # 產生 pass001、pass002...這種格式
        role = 'student'               # 給每個帳號加上學生身分
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                           (username, password, role))
            print(f'✅ 已新增：{username}')
        except sqlite3.IntegrityError:
            print(f'⚠️ {username} 已經存在，跳過。')

# 4. 執行批量新增 (這裡是新增 student01 ~ student50)
add_students(1, 50)

# 5. 儲存變更並關閉連線
conn.commit()
conn.close()

print('🎉 批次新增完成！')
