#!/usr/bin/env python3
import subprocess
import os
import sys
import time

# ANSI Colors
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

IS_WINDOWS = os.name == 'nt'

def print_success(message):
    print(f"{Colors.GREEN}✅  {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}❌  {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def run_command(command, cwd=None, capture_output=True, shell=None):
    """Runs a command and returns the result."""
    if shell is None:
        shell = IS_WINDOWS
    
    print_info(f"Running command: {' '.join(command) if isinstance(command, list) else command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            shell=shell
        )
        return result
    except Exception as e:
        print_error(f"Command execution failed: {str(e)}")
        return None

def find_supabase_cli():
    """Finds the Supabase CLI in common locations."""
    supabase_cli_path = None
    
    # Try to find Supabase CLI in common locations
    # 1. Check if it's in the PATH
    try:
        result = run_command(["which", "supabase"])
        if result and result.returncode == 0:
            supabase_cli_path = "supabase"
            print_success(f"Found Supabase CLI in PATH: {supabase_cli_path}")
            return supabase_cli_path
    except:
        pass
    
    # 2. Check if it's in node_modules
    local_supabase_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules", "supabase", "bin", "supabase")
    if os.path.exists(local_supabase_path):
        try:
            result = run_command([local_supabase_path, "--version"])
            if result and result.returncode == 0:
                supabase_cli_path = local_supabase_path
                print_success(f"Found Supabase CLI in node_modules: {supabase_cli_path}")
                return supabase_cli_path
        except:
            pass
    
    print_error("Supabase CLI not found. Install it from: https://supabase.com/docs/guides/cli")
    return None

def test_supabase_db_commands(supabase_cli_path):
    """Tests various Supabase DB commands against the local deployment."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== Testing Supabase DB Commands ==={Colors.ENDC}")
    
    # Test 1: Check DB status
    print("\n1. Checking DB status...")
    result = run_command([supabase_cli_path, "db", "status"])
    if result and result.returncode == 0:
        print_success("DB status check succeeded.")
        print(f"Output: {result.stdout}")
    else:
        print_error("DB status check failed.")
        if result:
            print(f"Error: {result.stderr}")
    
    # Test 2: Try to push migrations without linking
    print("\n2. Testing db push command without linking...")
    result = run_command([supabase_cli_path, "db", "push"], cwd="backend")
    if result and result.returncode == 0:
        print_success("DB push succeeded without linking.")
    else:
        print_error("DB push failed without linking.")
        if result:
            print(f"Error: {result.stderr}")
    
    # Test 3: Try to reset the database (with caution)
    print("\n3. Testing db reset command (this will clear your database!)...")
    confirm = input("Are you sure you want to reset the database? (y/N): ").lower().strip()
    if confirm == 'y':
        result = run_command([supabase_cli_path, "db", "reset"], cwd="backend")
        if result and result.returncode == 0:
            print_success("DB reset succeeded.")
        else:
            print_error("DB reset failed.")
            if result:
                print(f"Error: {result.stderr}")
    else:
        print_info("DB reset skipped.")
    
    # Test 4: Try to list migrations
    print("\n4. Listing database migrations...")
    result = run_command([supabase_cli_path, "db", "migrations", "list"], cwd="backend")
    if result and result.returncode == 0:
        print_success("Migrations listed successfully.")
        print(f"Migrations: {result.stdout}")
    else:
        print_error("Failed to list migrations.")
        if result:
            print(f"Error: {result.stderr}")

def main():
    """Main function to test Supabase CLI commands with local deployment."""
    print(f"{Colors.HEADER}{Colors.BOLD}=== Supabase Local Deployment Test ==={Colors.ENDC}")
    
    # 1. Find Supabase CLI
    supabase_cli_path = find_supabase_cli()
    if not supabase_cli_path:
        sys.exit(1)
    
    # 2. Get CLI version
    print("\nGetting Supabase CLI version...")
    result = run_command([supabase_cli_path, "--version"])
    if result and result.returncode == 0:
        print_success(f"Supabase CLI version: {result.stdout.strip()}")
    
    # 3. Test DB commands
    test_supabase_db_commands(supabase_cli_path)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}=== Test Completed ==={Colors.ENDC}")

if __name__ == "__main__":
    main()