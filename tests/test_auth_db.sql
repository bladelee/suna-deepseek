-- 检查auth schema是否存在
SELECT EXISTS (SELECT FROM information_schema.schemata WHERE schema_name = 'auth') AS schema_exists;

-- 检查auth.identities表是否存在
SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'identities') AS table_exists;

-- 查看auth.identities表的结构
SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'auth' AND table_name = 'identities';

-- 尝试查询auth.identities表的前5行数据（如果表存在）
SELECT * FROM auth.identities LIMIT 5;