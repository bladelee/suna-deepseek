-- 修复用户登录问题的SQL脚本
-- 问题：
-- 1. raw_user_meta_data中的email_verified仍为false
-- 2. confirmation_token为NULL可能导致数据库扫描错误

-- 修复1：将email_verified设置为true
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(raw_user_meta_data, '{email_verified}', 'true')
WHERE email = '1907732701@qq.com';

-- 修复2：确保confirmation_token不是NULL而是空字符串
-- 注意：某些版本的GoTrue可能期望confirmation_token是字符串类型而非NULL
UPDATE auth.users
SET confirmation_token = ''
WHERE email = '1907732701@qq.com' AND confirmation_token IS NULL;

-- 再次查看用户状态
SELECT 
  id,
  email,
  email_confirmed_at,
  confirmed_at,
  confirmation_token,
  raw_user_meta_data->>'email_verified' AS email_verified
FROM auth.users
WHERE email = '1907732701@qq.com';