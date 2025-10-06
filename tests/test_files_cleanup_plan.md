# 测试文件整理计划

## 根目录下的测试文件分析

根据对项目中以`test`开头的测试文件的分析，发现存在一些功能重叠和冗余的文件。下面是具体分析和整理建议：

### 文件列表及功能分析

1. **test_fixed_db_push.py**
   - **功能**：专门测试`supabase db push --local`命令是否正常工作
   - **特点**：包含Docker容器状态检查、Supabase CLI查找和db push命令执行测试
   - **保留理由**：在之前的迁移过程中遇到过db push相关问题，此脚本专门用于测试这一关键功能

2. **test_local_setup.py**
   - **功能**：测试local_setup.py中的数据导入功能
   - **特点**：检查Supabase CLI是否可用、本地Supabase是否运行、验证local_setup.py是否已修改
   - **删除理由**：功能与local_setup.py本身重叠，且local_setup.py已经包含了完整的设置逻辑

3. **test_local_supabase.py**
   - **功能**：测试本地Supabase数据库的各种命令
   - **特点**：包含DB状态检查、db push命令测试等多项功能，较为全面
   - **保留理由**：功能全面，测试了Supabase的核心操作，对确保数据库正常运行有帮助

4. **test_simplified_setup.py**
   - **功能**：测试简化后的数据库设置流程
   - **特点**：查找Supabase CLI、检查版本、检查Docker容器状态
   - **删除理由**：与test_local_setup.py和test_local_supabase.py功能重叠

5. **test_supabase_cli.py**
   - **功能**：仅测试Supabase CLI是否能被正确检测到
   - **特点**：功能单一，仅检查Supabase CLI的路径
   - **删除理由**：功能已经在其他多个测试脚本中实现，属于冗余

6. **test_supabase_import.py**
   - **功能**：测试Supabase数据导入功能
   - **特点**：创建测试数据文件、测试数据导入
   - **删除理由**：虽然功能独特，但不是项目的核心需求，且与local_setup.py中的数据导入功能可能有重叠

## 整理建议

### 保留的文件
- `test_fixed_db_push.py`：专门用于测试数据库迁移功能
- `test_local_supabase.py`：全面测试本地Supabase数据库功能

### 建议删除的文件
- `test_supabase_cli.py`：功能冗余
- `test_simplified_setup.py`：功能重叠
- `test_local_setup.py`：功能与主设置文件重叠
- `test_supabase_import.py`：非核心需求

## 执行计划

1. 确认保留的两个测试文件功能正常
2. 备份要删除的文件（如需）
3. 删除冗余的测试文件
4. 更新.gitignore文件，考虑是否需要添加测试文件的忽略规则

## 注意事项

- 删除前请确保没有依赖这些测试文件的其他脚本
- 建议在删除前先运行保留的测试文件，确保它们能正常工作
- 未来可以考虑将测试文件统一放到一个`tests`目录下，方便管理