-- 模拟邮箱激活确认的SQL脚本
-- 说明：此脚本用于在没有配置SMTP的情况下，手动将用户标记为已激活

-- 通过邮箱地址激活用户
-- 注意：email_confirmed_at是主要的激活状态字段，confirmed_at是生成列无法直接更新
UPDATE auth.users
SET 
  email_confirmed_at = NOW(),
  confirmation_token = NULL,
  updated_at = NOW()
WHERE email IN ('1907732701@qq.com', 'testuser@example.com');

-- 查看更新后的用户状态
SELECT 
  id,
  email,
  email_confirmed_at,
  confirmed_at,
  confirmation_token,
  created_at,
  updated_at
FROM auth.users
WHERE email IN ('1907732701@qq.com', 'testuser@example.com');