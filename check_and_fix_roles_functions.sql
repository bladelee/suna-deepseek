-- 角色权限检查与修复脚本（函数形式）

-- 清理可能存在的同名函数
DROP FUNCTION IF EXISTS check_auth_schema_exists();
DROP FUNCTION IF EXISTS fix_authenticator_role();
DROP FUNCTION IF EXISTS check_role_inheritance();
DROP FUNCTION IF EXISTS ensure_critical_roles_exist();
DROP FUNCTION IF EXISTS check_and_fix_auth_schema_permissions();
DROP FUNCTION IF EXISTS verify_final_permissions();
DROP FUNCTION IF EXISTS check_user_login_status();
DROP FUNCTION IF EXISTS fix_null_confirmation_tokens();
DROP FUNCTION IF EXISTS check_basejump_roles();
DROP FUNCTION IF EXISTS list_all_roles();
DROP FUNCTION IF EXISTS run_complete_role_check_and_fix();

-- 1. 检查auth schema是否存在
CREATE OR REPLACE FUNCTION check_auth_schema_exists()
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
    RAISE EXCEPTION 'Error: auth schema does not exist. Exiting script.';
    RETURN FALSE;
  ELSE
    RAISE NOTICE 'auth schema exists, proceeding with checks...';
    RETURN TRUE;
  END IF;
END;
$$;

-- 2. 检查并修复authenticator角色的继承设置
CREATE OR REPLACE FUNCTION fix_authenticator_role()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查authenticator角色设置...';
  
  -- 显示当前设置
  RAISE NOTICE '当前authenticator角色设置:';
  PERFORM pg_notify('role_check', (SELECT json_build_object('type', 'authenticator_role', 'data', 
    (SELECT row_to_json(t) FROM (SELECT rolname, rolinherit, rolcanlogin, rolbypassrls FROM pg_roles WHERE rolname = 'authenticator') t) 
  )::text));
  
  -- 修复继承设置
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator' AND rolinherit = false) THEN
    RAISE NOTICE '修复authenticator角色的继承设置...';
    ALTER ROLE authenticator WITH INHERIT;
    RAISE NOTICE '修复完成: authenticator角色现在可以继承其他角色权限';
  ELSE
    RAISE NOTICE 'authenticator角色的继承设置已经正确';
  END IF;
END;
$$;

-- 3. 检查角色继承关系
CREATE OR REPLACE FUNCTION check_role_inheritance()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查角色继承关系...';
  
  -- 显示角色继承关系
  RAISE NOTICE '角色继承关系:';
  PERFORM pg_notify('role_check', (SELECT json_build_object('type', 'role_inheritance', 'data', 
    (SELECT json_agg(row_to_json(t)) FROM (
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
        r1.rolname
    ) t) 
  )::text));
  
  -- 查询并显示结果（如果有结果）
  IF EXISTS (
    SELECT 1 
    FROM pg_roles r1
    JOIN pg_auth_members am ON r1.oid = am.member
    JOIN pg_roles r2 ON am.roleid = r2.oid
    WHERE r1.rolname IN ('authenticator', 'authenticated', 'anon', 'service_role')
  ) THEN
    SELECT rolname AS role_name, r2.rolname AS inherits_from
    FROM pg_roles r1
    JOIN pg_auth_members am ON r1.oid = am.member
    JOIN pg_roles r2 ON am.roleid = r2.oid
    WHERE r1.rolname IN ('authenticator', 'authenticated', 'anon', 'service_role')
    ORDER BY r1.rolname;
  ELSE
    RAISE NOTICE '未发现指定角色之间的继承关系';
  END IF;
END;
$$;

-- 4. 确保关键角色存在
CREATE OR REPLACE FUNCTION ensure_critical_roles_exist()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '确保关键角色存在...';
  
  -- 检查并创建authenticated角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    RAISE NOTICE '创建缺失的authenticated角色...';
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
  ELSE
    RAISE NOTICE 'authenticated角色已存在';
  END IF;
  
  -- 检查并创建anon角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    RAISE NOTICE '创建缺失的anon角色...';
    CREATE ROLE anon NOLOGIN NOINHERIT;
  ELSE
    RAISE NOTICE 'anon角色已存在';
  END IF;
  
  -- 检查并创建service_role角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    RAISE NOTICE '创建缺失的service_role角色...';
    CREATE ROLE service_role NOLOGIN NOINHERIT;
  ELSE
    RAISE NOTICE 'service_role角色已存在';
  END IF;
END;
$$;

-- 5. 检查并修复auth schema权限
CREATE OR REPLACE FUNCTION check_and_fix_auth_schema_permissions()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查auth schema权限设置...';
  
  -- 显示当前schema级权限
  RAISE NOTICE '当前schema级权限:';
  SELECT grantee, privilege_type 
  FROM information_schema.schema_privileges 
  WHERE schema_name = 'auth' 
  AND grantee IN ('authenticated', 'anon', 'service_role');
  
  -- 显示当前表级权限
  RAISE NOTICE '当前表级权限:';
  SELECT grantee, table_name, privilege_type 
  FROM information_schema.role_table_grants 
  WHERE table_schema = 'auth' 
  AND grantee IN ('authenticated', 'anon', 'service_role')
  ORDER BY grantee, table_name;
  
  -- 授予基本权限
  RAISE NOTICE '授予基本权限...';
  GRANT USAGE ON SCHEMA auth TO authenticated, anon, service_role;
  GRANT SELECT ON TABLE auth.users, auth.sessions, auth.refresh_tokens, auth.audit_log_entries TO authenticated, anon, service_role;
  
  -- 为了确保系统正常运行，授予更广泛的权限
  RAISE NOTICE '授予更广泛的权限以确保系统正常运行...';
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO authenticated, anon, service_role;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO authenticated, anon, service_role;
  ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL PRIVILEGES ON TABLES TO authenticated, anon, service_role;
  ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL PRIVILEGES ON SEQUENCES TO authenticated, anon, service_role;
  
  RAISE NOTICE 'auth schema权限修复完成';
END;
$$;

-- 6. 验证最终权限设置
CREATE OR REPLACE FUNCTION verify_final_permissions()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '验证修复后的auth schema权限设置...';
  
  -- 显示修复后的schema级权限
  RAISE NOTICE '修复后的schema级权限:';
  SELECT grantee, privilege_type 
  FROM information_schema.schema_privileges 
  WHERE schema_name = 'auth' 
  AND grantee IN ('authenticated', 'anon', 'service_role');
  
  -- 显示修复后的表级权限
  RAISE NOTICE '修复后的表级权限:';
  SELECT grantee, table_name, privilege_type 
  FROM information_schema.role_table_grants 
  WHERE table_schema = 'auth' 
  AND grantee IN ('authenticated', 'anon', 'service_role')
  ORDER BY grantee, table_name;
END;
$$;

-- 7. 检查用户登录状态相关字段
CREATE OR REPLACE FUNCTION check_user_login_status()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查用户登录状态字段...';
  
  -- 显示用户登录状态相关字段
  SELECT id, email, email_verified, confirmation_token 
  FROM auth.users 
  LIMIT 5; -- 仅显示前5个用户以验证
END;
$$;

-- 8. 修复NULL的confirmation_token
CREATE OR REPLACE FUNCTION fix_null_confirmation_tokens()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查并修复NULL的confirmation_token...';
  
  -- 修复NULL的confirmation_token
  UPDATE auth.users
  SET confirmation_token = ''
  WHERE confirmation_token IS NULL;
  
  RAISE NOTICE '修复完成: 已将所有NULL的confirmation_token设置为空字符串';
END;
$$;

-- 9. 检查basejump相关角色设置
CREATE OR REPLACE FUNCTION check_basejump_roles()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查basejump账户角色设置...';
  
  -- 显示basejump账户角色
  SELECT DISTINCT account_role FROM basejump.account_user;
END;
$$;

-- 10. 显示所有角色的完整列表
CREATE OR REPLACE FUNCTION list_all_roles()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '系统中所有角色:';
  
  -- 显示所有角色
  SELECT rolname FROM pg_roles ORDER BY rolname;
END;
$$;

-- 主函数：按顺序执行所有检查和修复
CREATE OR REPLACE FUNCTION run_complete_role_check_and_fix()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '====================================';
  RAISE NOTICE '开始执行角色权限完整检查与修复...';
  RAISE NOTICE '====================================';
  
  -- 1. 检查auth schema是否存在
  IF check_auth_schema_exists() THEN
    -- 2. 检查并修复authenticator角色
    PERFORM fix_authenticator_role();
    
    -- 3. 检查角色继承关系
    PERFORM check_role_inheritance();
    
    -- 4. 确保关键角色存在
    PERFORM ensure_critical_roles_exist();
    
    -- 5. 检查并修复auth schema权限
    PERFORM check_and_fix_auth_schema_permissions();
    
    -- 6. 验证最终权限设置
    PERFORM verify_final_permissions();
    
    -- 7. 检查用户登录状态
    PERFORM check_user_login_status();
    
    -- 8. 修复NULL的confirmation_token
    PERFORM fix_null_confirmation_tokens();
    
    -- 9. 检查basejump相关角色
    PERFORM check_basejump_roles();
    
    -- 10. 显示所有角色
    PERFORM list_all_roles();
    
    RAISE NOTICE '====================================';
    RAISE NOTICE '角色权限完整检查与修复执行完成！';
    RAISE NOTICE '====================================';
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    RAISE NOTICE '执行过程中发生错误: %', SQLERRM;
    RAISE NOTICE '脚本终止执行';
END;
$$;

-- 执行主函数
SELECT run_complete_role_check_and_fix();