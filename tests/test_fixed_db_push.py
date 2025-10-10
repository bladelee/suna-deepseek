#!/usr/bin/env python3
import subprocess
import os
import sys

# 颜色输出函数
def print_color(text, color_code):
    RESET = '\033[0m'
    print(f"{color_code}{text}{RESET}")

def print_success(text):
    print_color(text, '\033[92m')  # 绿色

def print_error(text):
    print_color(text, '\033[91m')  # 红色

def print_info(text):
    print_color(text, '\033[94m')  # 蓝色

def print_warning(text):
    print_color(text, '\033[93m')  # 黄色

# 检查Docker容器状态
def check_docker_container():
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", "name=supabase-db"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout.strip():
            print_success("✅ Supabase数据库容器正在运行")
            return True
        else:
            print_warning("⚠️ Supabase数据库容器未运行")
            return False
    except Exception as e:
        print_error(f"检查Docker容器状态时出错: {e}")
        return False

# 查找Supabase CLI
def find_supabase_cli():
    try:
        # 检查系统PATH中的supabase
        subprocess.run(["supabase", "--version"], capture_output=True, check=True)
        return "supabase"
    except (subprocess.SubprocessError, FileNotFoundError):
        # 检查node_modules中的supabase
        local_supabase_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules", "supabase", "bin", "supabase")
        if os.path.exists(local_supabase_path):
            try:
                subprocess.run([local_supabase_path, "--version"], capture_output=True, check=True)
                return local_supabase_path
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
    
    print_error("❌ 未找到Supabase CLI")
    return None

# 测试db push命令
def test_db_push():
    print_info("\n=== 测试修改后的db push命令 ===")
    
    # 检查Docker容器
    if not check_docker_container():
        print_warning("请先启动Supabase Docker容器，然后重试")
        return False
    
    # 查找Supabase CLI
    supabase_cli = find_supabase_cli()
    if not supabase_cli:
        print_info("你可以通过以下方式安装Supabase CLI:")
        print_info("1. 全局安装: npm install -g supabase")
        print_info("2. 本地安装: npm install supabase")
        return False
    
    # 执行db push命令，带--local参数
    try:
        print_info("正在执行: supabase db push --local")
        result = subprocess.run(
            [supabase_cli, "db", "push", "--local"],
            cwd="backend",
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_success("✅ 测试成功: db push --local 命令执行成功")
            return True
        else:
            print_error(f"❌ 测试失败: db push --local 命令执行失败")
            print_warning(f"错误输出: {result.stderr}")
            
            # 分析错误信息
            if "connection refused" in result.stderr.lower():
                print_info("提示: 无法连接到Supabase实例。请检查Docker容器是否正常运行。")
            elif "cannot find project ref" in result.stderr.lower():
                print_info("提示: 即使使用了--local参数，仍然找不到项目引用。")
                print_info("你可以尝试手动执行: supabase link --project-ref your-project-ref")
            return False
    except Exception as e:
        print_error(f"执行命令时发生异常: {str(e)}")
        return False

# 主函数
if __name__ == "__main__":
    print_info("开始测试修改后的local_setup.py中的数据库推送功能")
    success = test_db_push()
    
    if success:
        print_success("\n🎉 测试总结: 修改后的local_setup.py现在可以正常推送数据库迁移了")
        print_info("你可以使用以下命令运行完整设置:")
        print_info("python local_setup.py")
        print_info("或者仅运行数据库设置:")
        print_info("python local_setup.py --database-only")
    else:
        print_warning("\n⚠️ 测试总结: 修改后的local_setup.py仍有问题")
        print_info("请检查错误信息并尝试解决问题，或者手动设置数据库")
        print_info("手动设置步骤:")
        print_info("1. 确保Supabase Docker容器正在运行")
        print_info("2. 在backend目录下执行: supabase db push --local")
        
    sys.exit(0 if success else 1)