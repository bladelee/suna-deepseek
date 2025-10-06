import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取数据库连接信息
db_url = os.getenv('GOTRUE_DB_DATABASE_URL')
if not db_url:
    # 如果GOTRUE_DB_DATABASE_URL不存在，使用单独的环境变量构建连接字符串
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('PGPORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'postgres')
    db_url = f'postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

print(f"使用的数据库连接URL: {db_url}")

try:
    # 解析数据库URL以获取连接参数
    from urllib.parse import urlparse
    result = urlparse(db_url)
    conn = psycopg2.connect(
        dbname=result.path[1:],  # 去掉前面的斜杠
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    
    print("成功连接到数据库!")
    
    # 创建游标
    cur = conn.cursor()
    
    # 检查auth schema是否存在
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'auth');")
    schema_exists = cur.fetchone()[0]
    print(f"auth schema存在: {schema_exists}")
    
    # 检查auth.identities表是否存在
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'identities');")
    table_exists = cur.fetchone()[0]
    print(f"auth.identities表存在: {table_exists}")
    
    # 尝试查询auth.identities表的前5行数据（如果表存在）
    if table_exists:
        cur.execute("SELECT * FROM auth.identities LIMIT 5;")
        rows = cur.fetchall()
        print(f"auth.identities表的前5行数据: {rows}")
        
        # 检查列名
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'auth' AND table_name = 'identities';")
        columns = cur.fetchall()
        print(f"auth.identities表的列名: {[col[0] for col in columns]}")
    
    # 尝试插入一条测试数据（可选，根据需要取消注释）
    # cur.execute("INSERT INTO auth.identities (user_id, identity_data, provider, last_sign_in_at) VALUES ('test-user', '{\"email\":\"test@example.com\"}', 'email', NOW());")
    # conn.commit()
    # print("成功插入测试数据!")
    
    # 关闭游标和连接
    cur.close()
    conn.close()
    
    print("数据库测试完成!")
    
except Exception as e:
    print(f"数据库连接或操作失败: {e}")