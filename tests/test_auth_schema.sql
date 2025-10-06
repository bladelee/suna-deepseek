-- 以postgres用户身份登录，验证search_path设置是否正确
SHOW search_path;

-- 直接使用auth.identities表名（带schema前缀）
SELECT * FROM auth.identities LIMIT 1;

-- 不使用schema前缀，直接使用表名（依赖search_path）
SELECT * FROM identities LIMIT 1;

-- 检查auth schema下的所有表
SELECT table_name FROM information_schema.tables WHERE table_schema = 'auth';

-- 尝试插入一条测试数据到auth.identities表（可选）
-- INSERT INTO auth.identities (id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at) 
-- VALUES (uuid_generate_v4(), uuid_generate_v4(), '{"email":"test@example.com"}', 'email', NOW(), NOW(), NOW());
-- COMMIT;
-- SELECT * FROM auth.identities ORDER BY created_at DESC LIMIT 1;