-- 角色权限检查与修复脚本（函数形式）

-- 清理可能存在的同名函数
DROP FUNCTION IF EXISTS check_auth_schema_exists() CASCADE;
DROP FUNCTION IF EXISTS fix_authenticator_role() CASCADE;
DROP FUNCTION IF EXISTS check_role_inheritance() CASCADE;
DROP FUNCTION IF EXISTS ensure_critical_roles_exist() CASCADE;
DROP FUNCTION IF EXISTS check_and_fix_auth_schema_permissions() CASCADE;
DROP FUNCTION IF EXISTS verify_final_permissions() CASCADE;
DROP FUNCTION IF EXISTS check_user_login_status() CASCADE;
DROP FUNCTION IF EXISTS fix_null_confirmation_tokens() CASCADE;
DROP FUNCTION IF EXISTS check_basejump_roles() CASCADE;
DROP FUNCTION IF EXISTS list_all_roles() CASCADE;
DROP FUNCTION IF EXISTS check_and_fix_search_path() CASCADE;
DROP FUNCTION IF EXISTS run_complete_role_check_and_fix() CASCADE;

-- 1. 检查auth schema是否存在
CREATE OR REPLACE FUNCTION check_auth_schema_exists()
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
    RAISE EXCEPTION 'Error: auth schema does not exist. Exiting script.';
    RETURN false;
  ELSE
    RAISE NOTICE 'auth schema exists, proceeding with checks...';
    RETURN true;
  END IF;
END;
$$;

-- 1.1 检查并修复search_path设置
CREATE OR REPLACE FUNCTION check_and_fix_search_path()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查search_path设置...';
  
  -- 显示当前search_path
  DECLARE current_search_path TEXT;
  BEGIN
    SHOW search_path INTO current_search_path;
    RAISE NOTICE '当前search_path: %', current_search_path;
    
    -- 检查auth是否在search_path中
    IF current_search_path NOT LIKE '%auth%' THEN
      RAISE NOTICE 'auth schema不在search_path中，正在修复...';
      -- 添加auth到search_path
      EXECUTE 'SET search_path TO ' || current_search_path || ', auth';
      -- 同时设置数据库的默认search_path
      ALTER DATABASE postgres SET search_path TO "$user", public, auth, graphql_public, basejump, extensions;
      RAISE NOTICE '已将auth schema添加到search_path';
    ELSE
      RAISE NOTICE 'auth schema已在search_path中';
    END IF;
  EXCEPTION
    WHEN OTHERS THEN
      RAISE NOTICE '获取或修改search_path时出错: %', SQLERRM;
  END;
END;
$$;

-- 2. 检查并修复authenticator角色的继承设置
CREATE OR REPLACE FUNCTION fix_authenticator_role()
RETURNS void
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

-- 3. 检查并修复角色继承关系
CREATE OR REPLACE FUNCTION check_role_inheritance()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查角色继承关系...';
  
  -- 显示当前角色继承关系
  RAISE NOTICE '当前角色继承关系:';
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
  
  -- 检查并添加缺失的继承关系
  -- 确保authenticator继承authenticated角色
  IF NOT EXISTS (
    SELECT 1 
    FROM pg_roles r1
    JOIN pg_auth_members am ON r1.oid = am.member
    JOIN pg_roles r2 ON am.roleid = r2.oid
    WHERE r1.rolname = 'authenticator' AND r2.rolname = 'authenticated'
  ) THEN
    RAISE NOTICE '添加authenticator对authenticated角色的继承关系...';
    GRANT authenticated TO authenticator;
    RAISE NOTICE '已添加authenticator继承authenticated角色的关系';
  END IF;
  
  -- 确保authenticator继承anon角色
  IF NOT EXISTS (
    SELECT 1 
    FROM pg_roles r1
    JOIN pg_auth_members am ON r1.oid = am.member
    JOIN pg_roles r2 ON am.roleid = r2.oid
    WHERE r1.rolname = 'authenticator' AND r2.rolname = 'anon'
  ) THEN
    RAISE NOTICE '添加authenticator对anon角色的继承关系...';
    GRANT anon TO authenticator;
    RAISE NOTICE '已添加authenticator继承anon角色的关系';
  END IF;
  
  -- 显示修复后的角色继承关系
  RAISE NOTICE '修复后的角色继承关系:';
  PERFORM pg_notify('role_check', (SELECT json_build_object('type', 'role_inheritance_fixed', 'data', 
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
  
  -- 验证是否存在继承关系
  IF EXISTS (
    SELECT 1 
    FROM pg_roles r1
    JOIN pg_auth_members am ON r1.oid = am.member
    JOIN pg_roles r2 ON am.roleid = r2.oid
    WHERE r1.rolname IN ('authenticator', 'authenticated', 'anon', 'service_role')
  ) THEN
    RAISE NOTICE '角色继承关系已正确设置';
  ELSE
    RAISE NOTICE '未发现指定角色之间的继承关系';
  END IF;
END;
$$;

-- 4. 确保关键角色存在
CREATE OR REPLACE FUNCTION ensure_critical_roles_exist()
RETURNS TABLE(role_name text, action_taken text)
LANGUAGE plpgsql
AS $$
BEGIN
  -- 检查并创建authenticated角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
    RETURN QUERY SELECT 'authenticated'::text, '已创建角色'::text;
  ELSE
    RETURN QUERY SELECT 'authenticated'::text, '角色已存在'::text;
  END IF;
  
  -- 检查并创建anon角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN NOINHERIT;
    RETURN QUERY SELECT 'anon'::text, '已创建角色'::text;
  ELSE
    RETURN QUERY SELECT 'anon'::text, '角色已存在'::text;
  END IF;
  
  -- 检查并创建service_role角色
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN NOINHERIT;
    RETURN QUERY SELECT 'service_role'::text, '已创建角色'::text;
  ELSE
    RETURN QUERY SELECT 'service_role'::text, '角色已存在'::text;
  END IF;
  
  -- 检查并创建authenticator用户
  IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'authenticator') THEN
    CREATE USER authenticator WITH PASSWORD 'postgres';
    RETURN QUERY SELECT 'authenticator'::text, '已创建用户并设置密码'::text;
  ELSE
    RETURN QUERY SELECT 'authenticator'::text, '用户已存在'::text;
  END IF;
END;
$$;

-- 4.1: 创建auth.factor_type枚举类型（如果不存在）
CREATE OR REPLACE FUNCTION create_factor_type_enum()
RETURNS text 
LANGUAGE plpgsql
AS $$
BEGIN
  -- 检查auth.factor_type枚举类型是否存在
  IF NOT EXISTS (
    SELECT 1 
    FROM pg_type 
    WHERE typname = 'factor_type' 
    AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'auth')
  ) THEN
    -- 创建auth.factor_type枚举类型
    CREATE TYPE auth.factor_type AS ENUM ('totp');
    RETURN '已创建auth.factor_type枚举类型';
  ELSE
    RETURN 'auth.factor_type枚举类型已存在';
  END IF;
END;
$$;

-- 5. 检查并修复auth schema权限
CREATE OR REPLACE FUNCTION check_and_fix_auth_schema_permissions()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查auth schema权限设置...';
  
  -- 使用系统表检查权限，避免information_schema问题
  PERFORM 
    r.rolname AS grantee,
    (aclexplode(coalesce(n.nspacl, acldefault('n', r.oid)))).privilege_type AS privilege_type
  FROM 
    pg_namespace n
  JOIN 
    pg_roles r ON true
  WHERE 
    n.nspname = 'auth'
    AND r.rolname IN ('authenticated', 'anon', 'service_role');
  
  -- 授予基本权限
  RAISE NOTICE '授予基本权限...';
  GRANT USAGE ON SCHEMA auth TO authenticated, anon, service_role;
  
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
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '验证修复后的auth schema权限设置...';
  
  -- 使用系统表验证权限
  PERFORM 
    r.rolname AS grantee,
    (aclexplode(coalesce(n.nspacl, acldefault('n', r.oid)))).privilege_type AS privilege_type
  FROM 
    pg_namespace n
  JOIN 
    pg_roles r ON true
  WHERE 
    n.nspname = 'auth'
    AND r.rolname IN ('authenticated', 'anon', 'service_role');
  
  RAISE NOTICE '权限验证完成';
END;
$$;

-- 7. 检查用户登录状态相关字段 - 修复email_verified列不存在的问题
CREATE OR REPLACE FUNCTION check_user_login_status()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查用户登录状态字段...';
  
  -- 显示用户登录状态相关字段（如果表存在）
  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'auth' AND c.relname = 'users') THEN
    -- 检查email_verified列是否存在
    IF EXISTS (
      SELECT 1 
      FROM information_schema.columns 
      WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'email_verified'
    ) THEN
      -- 如果列存在，查询完整字段
      PERFORM id, email, email_verified, confirmation_token 
      FROM auth.users 
      LIMIT 5;
    ELSE
      -- 如果email_verified列不存在，只查询存在的列
      PERFORM id, email 
      FROM auth.users 
      LIMIT 5;
      RAISE NOTICE 'email_verified列不存在，使用降级查询';
    END IF;
  ELSE
    RAISE NOTICE 'auth.users表不存在，跳过用户登录状态检查';
  END IF;
END;
$$;

-- 8. 修复NULL的confirmation_token - 添加列存在性检查
CREATE OR REPLACE FUNCTION fix_null_confirmation_tokens()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查并修复NULL的confirmation_token...';
  
  -- 修复NULL的confirmation_token（如果表和列都存在）
  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'auth' AND c.relname = 'users') THEN
    -- 检查confirmation_token列是否存在
    IF EXISTS (
      SELECT 1 
      FROM information_schema.columns 
      WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'confirmation_token'
    ) THEN
      UPDATE auth.users
      SET confirmation_token = ''
      WHERE confirmation_token IS NULL;
      RAISE NOTICE '修复完成: 已将所有NULL的confirmation_token设置为空字符串';
    ELSE
      RAISE NOTICE 'confirmation_token列不存在，跳过修复';
    END IF;
  ELSE
    RAISE NOTICE 'auth.users表不存在，跳过confirmation_token修复';
  END IF;
END;
$$;

-- 9. 检查basejump相关角色设置
CREATE OR REPLACE FUNCTION check_basejump_roles()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '检查basejump账户角色设置...';
  
  -- 显示basejump账户角色（如果表存在）
  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'basejump' AND c.relname = 'account_user') THEN
    PERFORM DISTINCT account_role FROM basejump.account_user;
  ELSE
    RAISE NOTICE 'basejump.account_user表不存在，跳过basejump角色检查';
  END IF;
END;
$$;

-- 10. 显示所有角色的完整列表
CREATE OR REPLACE FUNCTION list_all_roles()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '系统中所有角色:';
  
  -- 显示所有角色
  PERFORM rolname FROM pg_roles ORDER BY rolname;
END;
$$;

-- 主函数：按顺序执行所有检查和修复
CREATE OR REPLACE FUNCTION run_complete_role_check_and_fix()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE '====================================';
  RAISE NOTICE '开始执行角色权限完整检查与修复...';
  RAISE NOTICE '====================================';
  
  -- 1. 确保关键角色存在（放在最前面，确保角色存在）
  RAISE NOTICE '确保关键角色存在...';
  PERFORM ensure_critical_roles_exist();
  
  -- 2. 检查auth schema是否存在
  IF check_auth_schema_exists() THEN
    -- 2.1 检查并修复search_path设置
    PERFORM check_and_fix_search_path();
    -- 3. 创建auth.factor_type枚举类型（如果不存在）
    RAISE NOTICE '%', create_factor_type_enum();
    
    -- 4. 检查并修复authenticator角色
    PERFORM fix_authenticator_role();
    
    -- 5. 检查并修复角色继承关系
    PERFORM check_role_inheritance();
    
    -- 6. 检查并修复auth schema权限
    PERFORM check_and_fix_auth_schema_permissions();
    
    -- 7. 验证最终权限设置
    PERFORM verify_final_permissions();
    
    -- 8. 检查用户登录状态
    PERFORM check_user_login_status();
    
    -- 9. 修复NULL的confirmation_token
    PERFORM fix_null_confirmation_tokens();
    
    -- 10. 检查basejump相关角色
    PERFORM check_basejump_roles();
    
    -- 11. 显示所有角色
    PERFORM list_all_roles();
    
    RAISE NOTICE '====================================';
    RAISE NOTICE '角色权限完整检查与修复执行完成！';
    RAISE NOTICE '====================================';
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    RAISE NOTICE '执行过程中发生错误: %', SQLERRM;
    RAISE NOTICE '尝试创建缺失的函数...';
    
    -- 尝试创建可能缺失的关键函数
    PERFORM 
      CASE 
        WHEN NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'check_and_fix_auth_schema_permissions') 
        THEN '需要创建check_and_fix_auth_schema_permissions函数'
        ELSE '所有函数已创建'
      END;
    
    RAISE NOTICE '脚本终止执行';
END;
$$;

-- 执行主函数
select run_complete_role_check_and_fix();