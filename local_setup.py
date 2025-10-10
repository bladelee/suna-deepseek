import sys
import time
import platform
import subprocess
import re
import json
import secrets
import base64
import argparse
import os
import tempfile

# --- Constants ---
IS_WINDOWS = platform.system() == "Windows"
# 检测Python版本是否支持capture_output参数（Python 3.7+）
PYTHON_VERSION = sys.version_info
SUPPORTS_CAPTURE_OUTPUT = PYTHON_VERSION >= (3, 7)

# --- ANSI Colors ---
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# --- UI Helpers ---
def print_banner():
    """Prints the Suna setup banner."""
    print(
        f"""
{Colors.BLUE}{Colors.BOLD}
   ███████╗██╗   ██╗███╗   ██╗ █████╗ 
   ██╔════╝██║   ██║████╗  ██║██╔══██╗
   ███████╗██║   ██║██╔██╗ ██║███████║
   ╚════██║██║   ██║██║╚██╗██║██╔══██║
   ███████║╚██████╔╝██║ ╚████║██║  ██║
   ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
                                      
   Local Development Setup
{Colors.ENDC}
"""
    )

def print_debug(message):
    """Prints debug information in purple."""
    print(f"{Colors.HEADER}[DEBUG] {message}{Colors.ENDC}")


def print_step(step_num, total_steps, step_name):
    """Prints a formatted step header."""
    print(
        f"\n{Colors.BLUE}{Colors.BOLD}Step {step_num}/{total_steps}: {step_name}{Colors.ENDC}"
    )
    print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}\n")

def print_info(message):
    """Prints an informational message."""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")

def print_success(message):
    """Prints a success message."""
    print(f"{Colors.GREEN}✅  {message}{Colors.ENDC}")

def print_warning(message):
    """Prints a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_error(message):
    """Prints an error message."""
    print(f"{Colors.RED}❌  {message}{Colors.ENDC}")

# --- Environment File Parsing ---
def parse_env_file(filepath):
    """Parses a .env file and returns a dictionary of key-value pairs."""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars

    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Handle key=value pairs
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception as e:
        print_warning(f"Could not parse {filepath}: {e}")

    return env_vars

def load_existing_env_vars():
    """Loads existing environment variables from .env files."""
    backend_env = parse_env_file(os.path.join("backend", ".env"))
    frontend_env = parse_env_file(os.path.join("frontend", ".env.local"))

    # Organize the variables by category
    existing_vars = {
        "supabase": {
            "SUPABASE_URL": backend_env.get("SUPABASE_URL", "http://localhost:8000"),
            "SUPABASE_ANON_KEY": backend_env.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"),
            "SUPABASE_SERVICE_ROLE_KEY": backend_env.get(
                "SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
            ),
        },
        "llm": {
            "OPENAI_API_KEY": backend_env.get("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": backend_env.get("ANTHROPIC_API_KEY", ""),
            "OPENROUTER_API_KEY": backend_env.get("OPENROUTER_API_KEY", ""),
            "GEMINI_API_KEY": backend_env.get("GEMINI_API_KEY", ""),
            "DEEPSEEK_API_KEY": backend_env.get("DEEPSEEK_API_KEY", ""),
        },
        "webhook": {
            "WEBHOOK_BASE_URL": backend_env.get("WEBHOOK_BASE_URL", "http://localhost:8000"),
            "TRIGGER_WEBHOOK_SECRET": backend_env.get("TRIGGER_WEBHOOK_SECRET", ""),
        },
        "mcp": {
            "MCP_CREDENTIAL_ENCRYPTION_KEY": backend_env.get(
                "MCP_CREDENTIAL_ENCRYPTION_KEY", ""
            ),
        },
        # 添加搜索和网页抓取API相关配置
        "search": {
            "TAVILY_API_KEY": backend_env.get("TAVILY_API_KEY", ""),
            "FIRECRAWL_API_KEY": backend_env.get("FIRECRAWL_API_KEY", ""),
            "FIRECRAWL_URL": backend_env.get("FIRECRAWL_URL", "https://api.firecrawl.dev"),
        },
        # 添加数据API相关配置
        "data": {
            "RAPID_API_KEY": backend_env.get("RAPID_API_KEY", ""),
        },
    }

    return existing_vars

# --- Validators ---
def validate_url(url, allow_empty=False):
    """Validates a URL format."""
    if allow_empty and not url:
        return True
    pattern = re.compile(
        r"^(?:http|https)://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))

def validate_api_key(api_key, allow_empty=False):
    """Performs a basic validation for an API key."""
    if allow_empty and not api_key:
        return True
    return bool(api_key and len(api_key) >= 10)

def generate_encryption_key():
    """Generates a secure base64-encoded encryption key for MCP credentials."""
    # Generate 32 random bytes (256 bits)
    key_bytes = secrets.token_bytes(32)
    # Encode as base64
    return base64.b64encode(key_bytes).decode("utf-8")

def generate_webhook_secret():
    """Generates a secure shared secret for trigger webhooks."""
    # 32 random bytes as hex (64 hex chars)
    return secrets.token_hex(32)

# --- Main Setup Class ---
class SetupWizard:
    def __init__(self):
        # Load existing environment variables from .env files
        existing_env_vars = load_existing_env_vars()

        # Start with default values and override with existing values
        self.env_vars = {
            "setup_method": "manual",  # Default to manual for local development
            "supabase": {
                "SUPABASE_URL": "http://localhost:8000",
                "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
                "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
            },
            "llm": {
                "OPENAI_API_KEY": "",
                "ANTHROPIC_API_KEY": "",
                "OPENROUTER_API_KEY": "",
                "GEMINI_API_KEY": "",
                "DEEPSEEK_API_KEY": "",
            },
            "webhook": {
                "WEBHOOK_BASE_URL": "http://localhost:8000",
                "TRIGGER_WEBHOOK_SECRET": "",
            },
            "mcp": {
                "MCP_CREDENTIAL_ENCRYPTION_KEY": "",
            },
            "search": {
                "TAVILY_API_KEY": "",
                "FIRECRAWL_API_KEY": "",
                "FIRECRAWL_URL": "https://api.firecrawl.dev",
            },
            "data": {
                "RAPID_API_KEY": "",
            },
        }

        # Override with existing values if present
        for category, vars in existing_env_vars.items():
            if category in self.env_vars:
                for key, value in vars.items():
                    if value and key in self.env_vars[category]:
                        self.env_vars[category][key] = value

        # 直接从backend/.env加载search和data相关的环境变量
        backend_env = parse_env_file(os.path.join("backend", ".env"))
        for key, value in backend_env.items():
            if key == "TAVILY_API_KEY" and value:
                self.env_vars["search"][key] = value
            elif key == "FIRECRAWL_API_KEY" and value:
                self.env_vars["search"][key] = value
            elif key == "FIRECRAWL_URL" and value:
                self.env_vars["search"][key] = value
            elif key == "RAPID_API_KEY" and value:
                self.env_vars["data"][key] = value

        self.total_steps = 6

    def _get_input(self, prompt, validator=None, error_message=None, allow_empty=False, default_value=""):
        """Helper method to get validated input from the user."""
        while True:
            if default_value:
                user_input = input(f"{prompt} [{default_value}]: ").strip()
                if not user_input:
                    return default_value
            else:
                user_input = input(f"{prompt}: ").strip()
                if allow_empty and not user_input:
                    return ""
            
            if not validator or validator(user_input, allow_empty=allow_empty):
                return user_input
            if error_message:
                print_error(error_message)
    
    def collect_supabase_info(self):
        """Collects Supabase configuration."""
        print_step(1, self.total_steps, "Configuring Supabase")
        
        print_info("For local development, we recommend using the default Supabase configuration.")
        print_info("This setup assumes you're running a local Supabase instance.")
        
        # Use default values for local Supabase with kong URL
        self.env_vars["supabase"]["SUPABASE_URL"] = "http://localhost:8000"
        self.env_vars["supabase"]["SUPABASE_ANON_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
        self.env_vars["supabase"]["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        
        print_success("Using default local Supabase configuration with kong URL.")

    def collect_llm_api_keys(self):
        """Collects LLM API keys."""
        print_step(2, self.total_steps, "Configuring LLM Providers")
        
        print_info("Enter your LLM API keys. You can skip any provider you don't want to use.")
        
        # Collect LLM API keys
        self.env_vars["llm"]["OPENAI_API_KEY"] = self._get_input(
            "Enter your OpenAI API key (or press Enter to skip)",
            validate_api_key,
            "Invalid API key format. It should be at least 10 characters long.",
            allow_empty=True,
            default_value=self.env_vars["llm"]["OPENAI_API_KEY"],
        )
        
        self.env_vars["llm"]["ANTHROPIC_API_KEY"] = self._get_input(
            "Enter your Anthropic API key (or press Enter to skip)",
            validate_api_key,
            "Invalid API key format. It should be at least 10 characters long.",
            allow_empty=True,
            default_value=self.env_vars["llm"]["ANTHROPIC_API_KEY"],
        )
        
        self.env_vars["llm"]["DEEPSEEK_API_KEY"] = self._get_input(
            "Enter your DeepSeek API key (or press Enter to skip)",
            validate_api_key,
            "Invalid API key format. It should be at least 10 characters long.",
            allow_empty=True,
            default_value=self.env_vars["llm"]["DEEPSEEK_API_KEY"],
        )
        
        configured_providers = [k.split("_")[0].capitalize() for k, v in self.env_vars["llm"].items() if v]
        if configured_providers:
            print_success(f"Configured LLM providers: {', '.join(configured_providers)}")
        else:
            print_warning("No LLM providers configured. Some features may be limited.")

    def collect_webhook_keys(self):
        """Collects webhook configuration."""
        print_step(3, self.total_steps, "Configuring Webhooks")
        
        print_info("Webhook base URL is required for workflows to receive callbacks.")
        print_info("For local development, we'll use the default http://localhost:8000")
        
        # Use default webhook URL for local development
        self.env_vars["webhook"]["WEBHOOK_BASE_URL"] = "http://localhost:8000"
        
        # Ensure a webhook secret exists; generate a strong default if missing
        if not self.env_vars["webhook"].get("TRIGGER_WEBHOOK_SECRET"):
            print_info("Generating a secure TRIGGER_WEBHOOK_SECRET for webhook authentication...")
            self.env_vars["webhook"]["TRIGGER_WEBHOOK_SECRET"] = generate_webhook_secret()
            print_success("Webhook secret generated.")
        else:
            print_info("Found existing TRIGGER_WEBHOOK_SECRET. Keeping existing value.")
        
        print_success("Webhook configuration saved.")

    def _find_supabase_cli(self):
        """Finds the Supabase CLI in common locations."""
        supabase_cli_path = None
        
        # Try to find Supabase CLI in common locations
        # 1. Check if it's in the PATH
        try:
            # 根据Python版本选择合适的参数
            if SUPPORTS_CAPTURE_OUTPUT:
                subprocess.run(
                    ["supabase", "--version"],
                    check=True,
                    capture_output=True,
                    shell=IS_WINDOWS,
                )
            else:
                subprocess.run(
                    ["supabase", "--version"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=IS_WINDOWS,
                )
            supabase_cli_path = "supabase"
        except (subprocess.SubprocessError, FileNotFoundError):
            # 2. Check if it's in node_modules
            local_supabase_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules", "supabase", "bin", "supabase")
            if os.path.exists(local_supabase_path):
                try:
                    # 根据Python版本选择合适的参数
                    if SUPPORTS_CAPTURE_OUTPUT:
                        subprocess.run(
                            [local_supabase_path, "--version"],
                            check=True,
                            capture_output=True,
                            shell=IS_WINDOWS,
                        )
                    else:
                        subprocess.run(
                            [local_supabase_path, "--version"],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=IS_WINDOWS,
                        )
                    supabase_cli_path = local_supabase_path
                    print_info(f"Found Supabase CLI in node_modules: {supabase_cli_path}")
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
        
        return supabase_cli_path
        
    def collect_mcp_keys(self):
        """Collects or generates MCP encryption key."""
        print_step(4, self.total_steps, "Configuring MCP")
        
        if not self.env_vars["mcp"]["MCP_CREDENTIAL_ENCRYPTION_KEY"]:
            print_info("Generating a secure MCP_CREDENTIAL_ENCRYPTION_KEY for credential encryption...")
            self.env_vars["mcp"]["MCP_CREDENTIAL_ENCRYPTION_KEY"] = generate_encryption_key()
            print_success("MCP encryption key generated.")
        else:
            print_info("Found existing MCP_CREDENTIAL_ENCRYPTION_KEY. Keeping existing value.")

    def configure_env_files(self):
        """Configures and writes the .env files for frontend and backend."""
        print_step(5, self.total_steps, "Configuring Environment Files")

        # --- Backend .env ---
        is_docker = self.env_vars["setup_method"] == "docker"
        redis_host = "redis" if is_docker else "localhost"

        # 创建基础环境变量
        backend_env = {
            "ENV_MODE": "local",
            **self.env_vars["supabase"],
            "REDIS_HOST": redis_host,
            "REDIS_PORT": "6379",
            **self.env_vars["llm"],
            **self.env_vars["webhook"],
            **self.env_vars["mcp"],
            "NEXT_PUBLIC_URL": "http://localhost:3002",
        }

        # 构建backend.env内容
        backend_env_content = f"# Generated by Suna local setup script for '{self.env_vars['setup_method']}' setup\n\n"
        
        # 添加基础环境变量
        for key, value in backend_env.items():
            backend_env_content += f"{key}={value or ''}\n"
        
        # 添加搜索和网页抓取API配置
        backend_env_content += "\n# Search and web scraping APIs\n"
        for key, value in self.env_vars["search"].items():
            if key == "FIRECRAWL_URL":
                # 使用local_dev_key作为测试值
                if not value:
                    value = "https://api.firecrawl.dev"
            elif not value:
                # 对于API密钥，如果没有值，使用local_dev_key作为默认值
                value = "local_dev_key"
            backend_env_content += f"{key}={value}\n"
        
        # 添加数据API配置
        backend_env_content += "\n# DATA APIS\n"
        for key, value in self.env_vars["data"].items():
            if not value:
                # 使用local_dev_key作为默认值
                value = "local_dev_key"
            backend_env_content += f"{key}={value}\n"

        with open(os.path.join("backend", ".env"), "w") as f:
            f.write(backend_env_content)
        print_success("Created backend/.env file with search and data API configurations.")

        # --- Frontend .env.local ---        
        frontend_env = {
            "NEXT_PUBLIC_SUPABASE_URL": self.env_vars["supabase"]["SUPABASE_URL"],
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": self.env_vars["supabase"]["SUPABASE_ANON_KEY"],
            "NEXT_PUBLIC_BACKEND_URL": "http://localhost:8001/api",
            "NEXT_PUBLIC_URL": "http://localhost:3002",
            "NEXT_PUBLIC_ENV_MODE": "LOCAL",
        }

        frontend_env_content = "# Generated by Suna local setup script\n\n"
        for key, value in frontend_env.items():
            frontend_env_content += f"{key}={value or ''}\n"

        with open(os.path.join("frontend", ".env.local"), "w") as f:
            f.write(frontend_env_content)
        print_success("Created frontend/.env.local file.")

    def _execute_sql_command(self, sql_command, description):
        """执行单个SQL命令并返回结果"""
        print_info(f"  执行: {description}")
        
        # 使用 docker exec 执行 psql 命令
        docker_command = [
            "docker", "exec", "-it", "supabase-db", 
            "psql", "-U", "postgres", "-c", sql_command
        ]
        
        try:
            # 根据Python版本选择合适的参数
            if SUPPORTS_CAPTURE_OUTPUT:
                result = subprocess.run(
                    docker_command,
                    capture_output=True,
                    text=True,
                    shell=IS_WINDOWS
                )
            else:
                result = subprocess.run(
                    docker_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=IS_WINDOWS
                )
            
            if result.returncode == 0:
                print_success(f"  ✓ 成功: {description}")
                print_debug(f"  命令输出: {result.stdout.strip()[:100]}...")
                return True
            else:
                print_warning(f"  ⚠️ 警告: 执行 '{description}' 时出现问题")
                print_debug(f"  错误信息: {result.stderr.strip()}")
                return False
        except Exception as e:
            print_warning(f"  ⚠️ 异常: 执行 '{description}' 时出现异常: {str(e)}")
            print_info("  如果您使用的不是Docker环境，请手动执行这些SQL命令。")
            return False
            
    def _prepare_supabase_database(self):
        """准备Supabase数据库，解决已知的迁移问题"""
        print_step(6, self.total_steps, "准备 Supabase 数据库环境")
        
        print_info("在执行迁移前，我们需要先解决已知的 Supabase 迁移问题：")
        
        # 定义需要执行的SQL命令列表和对应的描述
        sql_operations = [
            # 问题1: 安装 pgcrypto 扩展
            ("CREATE EXTENSION IF NOT EXISTS pgcrypto;", "安装 pgcrypto 扩展"),
            
            # 问题2: 创建 extensions 模式并安装 uuid-ossp 扩展
            ("CREATE SCHEMA IF NOT EXISTS extensions; DROP EXTENSION IF EXISTS \"uuid-ossp\"; CREATE EXTENSION \"uuid-ossp\" SCHEMA extensions;", "创建 extensions 模式并安装 uuid-ossp 扩展"),
            
            # 问题3: 修改数据库搜索路径
            ("ALTER DATABASE postgres SET search_path TO public, graphql_public, basejump, extensions;", "修改数据库搜索路径，添加 extensions 模式"),
            
            # 问题4: 创建 storage 模式、表和函数
            ("CREATE SCHEMA IF NOT EXISTS storage; CREATE TABLE IF NOT EXISTS storage.buckets (id TEXT PRIMARY KEY, name TEXT, owner TEXT, public BOOLEAN, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()); ALTER TABLE storage.buckets ADD COLUMN IF NOT EXISTS file_size_limit BIGINT; ALTER TABLE storage.buckets ADD COLUMN IF NOT EXISTS allowed_mime_types TEXT[]; CREATE TABLE IF NOT EXISTS storage.objects (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), bucket_id TEXT REFERENCES storage.buckets(id), name TEXT, owner TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), last_accessed_at TIMESTAMP WITH TIME ZONE, metadata JSONB, path_tokens TEXT[], size BIGINT, mime_type TEXT); CREATE OR REPLACE FUNCTION storage.foldername(name TEXT) RETURNS TEXT[] AS $$ SELECT string_to_array(regexp_replace(name, '^/?|/?$', '', 'g'), '/') $$ LANGUAGE sql IMMUTABLE;", "创建 storage 模式、buckets 和 objects 表及相关函数"),
            
            # 问题6: 创建 supabase_realtime publication
            ("CREATE PUBLICATION supabase_realtime;", "创建 supabase_realtime publication 以支持实时功能"),
        ]
        
        # 执行每个SQL命令
        print_info(f"将执行 {len(sql_operations)} 个数据库准备步骤...")
        success_count = 0
        
        for i, (sql_command, description) in enumerate(sql_operations, 1):
            print_info(f"步骤 {i}/{len(sql_operations)}: {description}")
            if self._execute_sql_command(sql_command, description):
                success_count += 1
            print_info("---")
        
        print_info(f"数据库准备步骤完成: {success_count}/{len(sql_operations)} 个步骤成功执行")
        if success_count < len(sql_operations):
            print_warning("部分数据库准备步骤执行失败，可能会影响后续迁移。请根据警告信息检查问题。")
        else:
            print_success("所有数据库准备步骤已成功执行！")
        
        return success_count >= len(sql_operations)  # 返回是否所有步骤都成功
        
    def setup_supabase_database(self):
        """Pushes database migrations to the local Supabase instance."""
        print_step(6, self.total_steps, "Setting up Supabase Database")

        print_info(
            "This step will push database migrations to your local Supabase instance."
        )
        print_info(
            "Make sure your local Supabase instance is running before proceeding."
        )

        # Find Supabase CLI
        supabase_cli_path = self._find_supabase_cli()
        if not supabase_cli_path:
            print_error(
                "Supabase CLI not found. Install it from: https://supabase.com/docs/guides/cli"
            )
            print_info("You can also install it locally with: npm install supabase")
            print_info("You can also set up the database manually using the Supabase GUI.")
            sys.exit(1)

        try:
            print_info("正在推送数据库迁移...")
            # 直接指定数据库连接URL，明确使用5432端口（用户的PostgreSQL运行端口）
            # 添加sslmode=disable参数以禁用TLS连接
            db_url = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"
            
            # 添加调试打印信息
            print_debug(f"当前执行路径: {os.getcwd()}")
            print_debug(f"后端目录路径: {os.path.abspath('backend')}")
            print_debug(f"Supabase CLI路径: {supabase_cli_path}")
            print_debug(f"使用的数据库连接URL: {db_url}")
            
            # 添加数据库连接测试
            try:
                import psycopg2
                print_debug("尝试直接使用psycopg2连接数据库...")
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print_debug(f"数据库连接成功！PostgreSQL版本: {version[:30]}...")
                cursor.close()
                conn.close()
            except ImportError:
                print_debug("psycopg2模块未安装，跳过直接连接测试")
            except Exception as e:
                print_debug(f"直接连接数据库失败: {str(e)}")
            
            # 在执行迁移前，先解决已知的 Supabase 迁移问题
            print_info("\n=== 开始数据库环境准备 ===")
            self._prepare_supabase_database()
            print_info("=== 数据库环境准备完成 ===\n")
            
            # 添加--debug参数进行详细调试
            command = [supabase_cli_path, "db", "push", "--db-url", db_url, "--debug"]
            print_debug(f"执行的命令: {' '.join(command)}")
            
            # 根据Python版本选择合适的参数
            if SUPPORTS_CAPTURE_OUTPUT:
                push_result = subprocess.run(
                    command,
                    cwd="backend",
                    capture_output=True,
                    text=True,
                    shell=IS_WINDOWS
                )
            else:
                push_result = subprocess.run(
                    command,
                    cwd="backend",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=IS_WINDOWS
                )
                
            # 打印命令的完整输出
            print_debug(f"命令标准输出: {push_result.stdout}")
            print_debug(f"命令标准错误: {push_result.stderr}")
            
            if push_result.returncode == 0:
                print_success("数据库迁移已成功推送到本地Supabase实例。")
            else:
                # 分析错误信息，提供更具体的帮助
                error_msg = push_result.stderr
                print_warning(f"数据库迁移推送过程中遇到问题: {error_msg}")
                
                # 常见错误处理
                if "connection refused" in error_msg.lower():
                    print_info("错误提示: 无法连接到PostgreSQL实例。请确保PostgreSQL服务正在运行。")
                    print_info("你可以使用命令检查服务状态: systemctl status postgresql 或 docker ps")
                    print_info(f"当前配置的连接端口: 5432")
                elif "tls error" in error_msg.lower() or "ssl" in error_msg.lower():
                    print_info("错误提示: TLS/SSL连接被拒绝。")
                    print_info("我们已经在连接URL中添加了sslmode=disable参数，但仍然遇到问题。")
                    print_info("请检查PostgreSQL的ssl配置是否正确。")
                elif "cannot find project ref" in error_msg.lower():
                    print_info("错误提示: 找不到项目引用。这通常表示需要先执行link命令。")
                    print_info("你可以尝试手动执行: supabase link --project-ref your-project-ref")
                else:
                    print_info("请检查错误信息并尝试解决问题。")
                    print_info(f"当前使用的命令: {' '.join(command)}")
                    print_info("建议: 你可以尝试在终端中直接运行上述命令，获取更详细的错误信息。")
                    
            # 即使迁移推送有问题，也继续执行（不退出脚本）
            print_info("数据库设置流程已完成。")
            
        except Exception as e:
            print_error(f"设置本地Supabase数据库时发生错误: {str(e)}")
            print_info("请检查你的本地Supabase实例状态，确保它正在运行。")
            print_info("如果需要，可以手动完成数据库设置步骤。")
            # 不强制退出，让用户决定是否继续

    def install_dependencies(self):
        """Installs frontend and backend dependencies for manual setup."""
        print_info("Installing dependencies...")
        
        try:
            print_info("Installing frontend dependencies with npm...")
            subprocess.run(
                ["npm", "install"], cwd="frontend", check=True, shell=IS_WINDOWS
            )
            print_success("Frontend dependencies installed.")

            print_info("Installing backend dependencies...")
            # Check if uv is available
            try:
                # 根据Python版本选择合适的参数
                if SUPPORTS_CAPTURE_OUTPUT:
                    subprocess.run(
                        ["uv", "--version"],
                        check=True,
                        capture_output=True,
                        shell=IS_WINDOWS,
                    )
                else:
                    subprocess.run(
                        ["uv", "--version"],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=IS_WINDOWS,
                    )
                # Use uv if available
                print_info("Using uv for dependency installation...")
                subprocess.run(
                    ["uv", "pip", "install", "-e", "."],
                    cwd="backend",
                    check=True,
                    shell=IS_WINDOWS,
                )
                print_success("Backend dependencies installed with uv.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pip if uv is not available
                print_info("uv not available, using pip for dependency installation...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", "."],
                    cwd="backend",
                    check=True,
                    shell=IS_WINDOWS,
                )
                print_success("Backend dependencies installed with pip.")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {str(e)}")
            print_info("You may need to install dependencies manually.")
        except Exception as e:
            print_error(f"An error occurred during dependency installation: {str(e)}")


    
    def run(self):
        """Runs the local setup process."""
        print_banner()
        print(
            "This wizard will guide you through setting up Suna for local development with Supabase.\n"
        )

        try:
            # Run essential setup steps
            self.collect_supabase_info()
            self.collect_llm_api_keys()
            self.collect_webhook_keys()
            self.collect_mcp_keys()
            self.configure_env_files()
            self.setup_supabase_database()
            
            # Dependencies installation skipped as requested
            self.final_instructions()

        except KeyboardInterrupt:
            print("\n\nSetup interrupted.")
            sys.exit(1)
        except Exception as e:
            print_error(f"An unexpected error occurred: {e}")
            sys.exit(1)

    def final_instructions(self):
        """Shows final instructions to the user."""
        print(f"\n{Colors.GREEN}{Colors.BOLD}✨ Suna Local Setup Complete! ✨{Colors.ENDC}\n")

        print_info(
            "Suna is configured for local development with your settings."
        )
        
        print_info("To start Suna for local development, run these commands in separate terminals:")
        print(f"\n{Colors.BOLD}1. Start Infrastructure (in project root):{Colors.ENDC}")
        print(f"{Colors.CYAN}   docker compose up redis -d{Colors.ENDC}")

        print(f"\n{Colors.BOLD}2. Start Backend (in a new terminal):{Colors.ENDC}")
        print(f"{Colors.CYAN}   cd backend && python -m uvicorn app.main:app --reload --port 8000{Colors.ENDC}")

        print(f"\n{Colors.BOLD}3. Start Frontend (in a new terminal):{Colors.ENDC}")
        print(f"{Colors.CYAN}   cd frontend && npm run dev{Colors.ENDC}")

        print(f"\n{Colors.BOLD}4. Start Worker (in a new terminal):{Colors.ENDC}")
        print(f"{Colors.CYAN}   cd backend && python -m worker.main{Colors.ENDC}")

        print(f"\n{Colors.BOLD}5. Start Scheduler (in a new terminal):{Colors.ENDC}")
        print(f"{Colors.CYAN}   cd backend && python -m scheduler.main{Colors.ENDC}")

        print(f"\n{Colors.GREEN}Once all services are running, open http://localhost:3000 in your browser to access Suna.{Colors.ENDC}")

# --- Main Function ---

def main():
        """Main entry point for the script."""
        parser = argparse.ArgumentParser(description='Suna Local Development Setup')
        parser.add_argument('--database-only', action='store_true', help='Run only the database setup')
        
        args = parser.parse_args()
        
        wizard = SetupWizard()
        
        if args.database_only:
            # Run only the database setup
            print_banner()
            print("Running database setup only...\n")
            wizard.setup_supabase_database()
            print_success("Database setup completed.")
        else:
            # Run full setup
            wizard.run()

if __name__ == "__main__":
    main()