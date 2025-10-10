#!/bin/bash

# 执行函数形式的角色权限检查与修复脚本

# 使用说明
# 此脚本用于运行以函数形式组织的角色权限检查与修复SQL脚本
# 函数形式的脚本提供了更好的组织性和可维护性

# 方法1: 通过docker exec和管道运行SQL脚本
# 使用此方法如果您已经有正在运行的Supabase数据库容器
echo "正在执行函数形式的角色权限检查与修复脚本..."
cat check_and_fix_roles_functions.sql | docker exec -i supabase-db psql -U postgres -d postgres

# 方法2: 如果方法1失败，可以尝试直接连接到数据库
# 如果您知道数据库的连接信息，可以取消下面的注释并修改连接参数

## 使用psql命令行工具连接并执行脚本
# psql -h localhost -p 5432 -U postgres -d postgres -f check_and_fix_roles_functions.sql

# 执行完成后提示
echo "函数形式的角色权限检查与修复脚本执行完成！"
echo "请查看输出结果以确认修复情况。"

# 可选: 清理创建的函数
echo "\n是否要清理脚本创建的函数？(y/n)"
read -r cleanup_choice

if [[ $cleanup_choice == [Yy]* ]]; then
  echo "正在清理创建的函数..."
  cat << EOF | docker exec -i supabase-db psql -U postgres -d postgres
    DROP FUNCTION IF EXISTS check_auth_schema_exists();
    DROP FUNCTION IF EXISTS create_factor_type_enum();
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
EOF
  echo "函数清理完成！"
else
  echo "保留创建的函数，您可以在后续手动调用它们。"
  echo "例如: SELECT check_role_inheritance();"
echo "     SELECT check_and_fix_auth_schema_permissions();"
fi