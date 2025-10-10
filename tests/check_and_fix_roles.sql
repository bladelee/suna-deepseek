-- 角色权限检查与修复脚本

-- 1. 检查auth schema是否存在，如果不存在则退出
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
    RAISE EXCEPTION 'Error: auth schema does not exist. Exiting script.';
  ELSE
    RAISE NOTICE 'auth schema exists, proceeding with checks...';
  END IF;
END $$;

-- 2. 检查并修复authenticator角色的继承设置
SELECT '当前authenticator角色设置:' AS status;
SELECT rolname, rolinherit, rolcanlogin, rolbypassrls FROM pg_roles WHERE rolname = 'authenticator';

-- 如果rolinherit为false，则修复
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator' AND rolinherit = false) THEN
    RAISE NOTICE '修复authenticator角色的继承设置...';
    ALTER ROLE authenticator WITH INHERIT;
    RAISE NOTICE '修复完成: authenticator角色现在可以继承其他角色权限';
  ELSE
    RAISE NOTICE 'authenticator角色的继承设置已经正确';
  END IF;
END $$;

-- 3. 检查角色继承关系
SELECT '角色继承关系检查:' AS status;
SELECT 
  r1.rolname AS role_name, 
  r2.rolname AS inherits_from
FROM 
  pg_roles r1
JOIN 
  pg_auth_members am ON r1.oid = am.member
JOIN 
  pg_roles r2 ON am.roleid = r2.oid
WHERE 
  r1.rolname IN ('authenticator', 'authenticated', 'anon', 'service_role')
ORDER BY 
  r1.rolname;

-- 4. 验证关键角色是否存在
DO $$
BEGIN
  -- 检查authenticated角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    RAISE NOTICE '创建缺失的authenticated角色...';
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
  END IF;
  
  -- 检查anon角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    RAISE NOTICE '创建缺失的anon角色...';
    CREATE ROLE anon NOLOGIN NOINHERIT;
  END IF;
  
  -- 检查service_role角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    RAISE NOTICE '创建缺失的service_role角色...';
    CREATE ROLE service_role NOLOGIN NOINHERIT;
  END IF;
END $$;

-- 5. 检查并修复auth schema权限
SELECT '当前auth schema权限设置:' AS status;
-- 检查schema级权限
SELECT grantee, privilege_type 
FROM information_schema.schema_privileges 
WHERE schema_name = 'auth' 
AND grantee IN ('authenticated', 'anon', 'service_role');

-- 检查表级权限
SELECT grantee, table_name, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_schema = 'auth' 
AND grantee IN ('authenticated', 'anon', 'service_role')
ORDER BY grantee, table_name;

-- 授予基本权限
GRANT USAGE ON SCHEMA auth TO authenticated, anon, service_role;
GRANT SELECT ON TABLE auth.users, auth.sessions, auth.refresh_tokens, auth.audit_log_entries TO authenticated, anon, service_role;

-- 为了确保系统正常运行，授予更广泛的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO authenticated, anon, service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO authenticated, anon, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL PRIVILEGES ON TABLES TO authenticated, anon, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL PRIVILEGES ON SEQUENCES TO authenticated, anon, service_role;

-- 6. 验证最终权限设置
SELECT '修复后auth schema权限设置:' AS status;
-- 检查schema级权限
SELECT grantee, privilege_type 
FROM information_schema.schema_privileges 
WHERE schema_name = 'auth' 
AND grantee IN ('authenticated', 'anon', 'service_role');

-- 检查表级权限
SELECT grantee, table_name, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_schema = 'auth' 
AND grantee IN ('authenticated', 'anon', 'service_role')
ORDER BY grantee, table_name;

-- 7. 检查用户登录状态相关字段
SELECT '检查用户登录状态字段:' AS status;
SELECT id, email, email_verified, confirmation_token 
FROM auth.users 
LIMIT 5; -- 仅显示前5个用户以验证

-- 8. 如果需要，自动修复confirmation_token为NULL的情况
DO $$
BEGIN
  RAISE NOTICE '检查并修复NULL的confirmation_token...';
  UPDATE auth.users
  SET confirmation_token = ''
  WHERE confirmation_token IS NULL;
  RAISE NOTICE '修复完成: 已将所有NULL的confirmation_token设置为空字符串';
END $$;

-- 9. 检查basejump相关角色设置
SELECT '检查basejump账户角色设置:' AS status;
SELECT DISTINCT account_role FROM basejump.account_user;

-- 10. 显示所有角色的完整列表
SELECT '系统中所有角色:' AS status;
SELECT rolname FROM pg_roles ORDER BY rolname;

-- 执行完成提示
RAISE NOTICE '角色权限检查与修复脚本执行完成！';