#!/bin/bash

# 执行角色权限检查与修复脚本

# 方法1: 通过docker exec直接运行SQL脚本
# 使用此方法如果您已经有正在运行的Supabase数据库容器
echo "正在执行角色权限检查与修复脚本..."
docker exec -i supabase-db psql -U postgres -d postgres -f check_and_fix_roles.sql

# 方法2: 如果方法1失败，可以尝试直接连接到数据库
# 如果您知道数据库的连接信息，可以取消下面的注释并修改连接参数

## 使用psql命令行工具连接并执行脚本
# psql -h localhost -p 5432 -U postgres -d postgres -f check_and_fix_roles.sql

# 执行完成后提示
echo "角色权限检查与修复脚本执行完成！"
echo "请查看输出结果以确认修复情况。"