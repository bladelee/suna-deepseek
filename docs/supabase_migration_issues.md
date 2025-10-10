# Supabase 数据库迁移问题总结

本文档总结了在执行 `supabase db push --local` 命令过程中遇到的问题、解决方案以及对迁移脚本的修改。

## 问题1：pgcrypto 扩展缺失

### 问题描述
迁移过程中出现 `gen_random_bytes` 函数不存在的错误。

### 解决方案
直接在数据库中安装 pgcrypto 扩展：
```bash
docker exec -it supabase-db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### 状态
已解决。

## 问题2：extensions 模式不存在

### 问题描述
迁移脚本中使用了 `extensions.uuid_generate_v4()` 函数，但数据库中不存在 extensions 模式。

### 解决方案
1. 创建 extensions 模式
2. 在该模式下安装 uuid-ossp 扩展
```bash
docker exec -it supabase-db psql -U postgres -c "CREATE SCHEMA IF NOT EXISTS extensions; DROP EXTENSION IF EXISTS \"uuid-ossp\"; CREATE EXTENSION \"uuid-ossp\" SCHEMA extensions;"
```

### 状态
已解决。

## 问题3：数据库搜索路径问题

### 问题描述
迁移脚本中直接调用 `uuid_generate_v4()` 函数，但数据库默认搜索路径中不包含 extensions 模式。

### 解决方案
修改数据库的搜索路径，添加 extensions 模式：
```bash
docker exec -it supabase-db psql -U postgres -c "ALTER DATABASE postgres SET search_path TO public, graphql_public, basejump, extensions;"
```

### 状态
已解决。

## 问题4：storage 相关表缺失

### 问题描述
迁移脚本尝试访问 `storage.buckets` 和 `storage.objects` 表，但这些表不存在。

### 解决方案
创建 storage 模式、buckets 表和 objects 表，并添加必要的列和函数：
```bash
docker exec -it supabase-db psql -U postgres -c "CREATE SCHEMA IF NOT EXISTS storage; CREATE TABLE IF NOT EXISTS storage.buckets (id TEXT PRIMARY KEY, name TEXT, owner TEXT, public BOOLEAN, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()); ALTER TABLE storage.buckets ADD COLUMN IF NOT EXISTS file_size_limit BIGINT; ALTER TABLE storage.buckets ADD COLUMN IF NOT EXISTS allowed_mime_types TEXT[]; CREATE TABLE IF NOT EXISTS storage.objects (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), bucket_id TEXT REFERENCES storage.buckets(id), name TEXT, owner TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), last_accessed_at TIMESTAMP WITH TIME ZONE, metadata JSONB, path_tokens TEXT[], size BIGINT, mime_type TEXT); CREATE OR REPLACE FUNCTION storage.foldername(name TEXT) RETURNS TEXT[] AS $$ SELECT string_to_array(regexp_replace(name, '^/?|/?$', '', 'g'), '/') $$ LANGUAGE sql IMMUTABLE;"
```

### 状态
已解决。

## 问题5：pg_cron 扩展不可用

### 问题描述
迁移脚本中尝试创建 `pg_cron` 和 `pg_net` 扩展，但在当前的 PostgreSQL 容器中无法安装这些扩展。

### 关于 pg_cron 扩展不可用的说明
**pg_cron 扩展不可用是指无法在当前的 PostgreSQL 容器中安装该扩展**，而不是无法启用。错误信息显示：
```
ERROR: extension "pg_cron" is not available
DETAIL: Could not open extension control file "/usr/local/share/postgresql/extension/pg_cron.control": No such file or directory.
```

这表明在当前的 PostgreSQL 容器中，pg_cron 扩展的控制文件不存在。pg_cron 是 PostgreSQL 的一个定时任务扩展，不是核心扩展，需要单独安装到 PostgreSQL 服务器上。在标准的 PostgreSQL Docker 镜像中通常不包含此扩展，而 Supabase 的官方镜像中可能会预安装这些扩展。

### 解决方案
修改迁移文件 `20250808120000_supabase_cron.sql`，注释掉扩展创建代码，并添加模拟的 cron 和 net 模式以及相关函数：

```sql
-- Enable required extensions if not already enabled
-- Note: pg_cron and pg_net are skipped in development environment
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create dummy cron schema and tables to allow migration to proceed
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'cron') THEN
    CREATE SCHEMA cron;
    CREATE TABLE cron.job (jobid bigint, jobname text);
    CREATE OR REPLACE FUNCTION cron.schedule(text, text, text) RETURNS bigint LANGUAGE sql AS 'SELECT 1::bigint;';
    CREATE OR REPLACE FUNCTION cron.unschedule(bigint) RETURNS boolean LANGUAGE sql AS 'SELECT true;';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'net') THEN
    CREATE SCHEMA net;
    CREATE OR REPLACE FUNCTION net.http_post(text, jsonb, jsonb, integer) RETURNS TABLE(status bigint, content_type text, headers jsonb, content jsonb) LANGUAGE sql AS 'SELECT 200::bigint, ''application/json''::text, ''{}''::jsonb, ''{}''::jsonb;';
  END IF;
END $$;
```

### 状态
已解决。

## 问题6：supabase_realtime publication 缺失

### 问题描述
迁移脚本尝试为 projects 表启用实时功能，但 `supabase_realtime` publication 不存在。

### 解决方案
创建 supabase_realtime publication：
```bash
docker exec -it supabase-db psql -U postgres -c "CREATE PUBLICATION supabase_realtime;"
```

### 状态
已解决。

## 总结

通过以上步骤，我们成功解决了所有迁移过程中的问题，使 `supabase db push --local` 命令能够顺利完成。主要的修改包括：

1. **修改了迁移脚本**: `20250808120000_supabase_cron.sql` - 注释掉扩展创建代码并添加模拟的 cron 和 net 功能

2. **在数据库中直接执行的操作**: 
   - 安装 pgcrypto 扩展
   - 创建 extensions 模式并安装 uuid-ossp 扩展
   - 修改数据库搜索路径
   - 创建 storage 模式、表和函数
   - 创建 supabase_realtime publication

这些修改使得在开发环境中能够成功运行数据库迁移，而不需要完整的 Supabase 扩展支持。在生产环境中，建议使用官方的 Supabase 服务或包含所有必要扩展的自定义 Docker 镜像。