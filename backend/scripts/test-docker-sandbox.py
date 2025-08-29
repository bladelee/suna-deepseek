#!/usr/bin/env python3
"""
Test Docker Sandbox functionality.

This script provides a simple way to test the local Docker sandbox implementation.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for testing
os.environ['USE_LOCAL_DOCKER_SANDBOX'] = 'true'
os.environ['SANDBOX_IMAGE_NAME'] = 'kortix/suna:0.1.3.6'

try:
    from sandbox.docker_sandbox import DockerSandboxManager, get_docker_manager
    from utils.logger import logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)


async def test_docker_connection():
    """Test Docker connection."""
    print("🔍 Testing Docker connection...")
    
    try:
        manager = get_docker_manager()
        print("✅ Docker connection successful")
        return manager
    except Exception as e:
        print(f"❌ Docker connection failed: {e}")
        return None


async def test_sandbox_creation(manager):
    """Test sandbox creation."""
    print("🔧 Testing sandbox creation...")
    
    try:
        # Create a test sandbox
        sandbox = await manager.create_sandbox("test123", "test-project")
        print(f"✅ Sandbox created successfully: {sandbox.id}")
        
        # Test sandbox properties
        print(f"   State: {sandbox.state}")
        print(f"   Container ID: {sandbox.container_id}")
        
        return sandbox
    except Exception as e:
        print(f"❌ Sandbox creation failed: {e}")
        return None


async def test_file_operations(sandbox):
    """Test file operations."""
    print("📁 Testing file operations...")
    
    try:
        # Test file upload
        test_content = b"Hello, Docker Sandbox!"
        test_path = "/test_file.txt"
        
        await sandbox.fs.upload_file(test_content, test_path)
        print(f"✅ File uploaded: {test_path}")
        
        # Test file listing
        files = await sandbox.fs.list_files("/")
        print(f"✅ Files listed: {len(files)} files found")
        for file in files:
            print(f"   - {file.name} ({'dir' if file.is_dir else 'file'})")
        
        # Test file download
        downloaded_content = await sandbox.fs.download_file(test_path)
        if downloaded_content == test_content:
            print(f"✅ File download successful: {test_path}")
        else:
            print(f"❌ File download failed: content mismatch")
        
        # Test file deletion
        await sandbox.fs.delete_file(test_path)
        print(f"✅ File deleted: {test_path}")
        
        return True
    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return False


async def test_process_operations(sandbox):
    """Test process operations."""
    print("⚙️  Testing process operations...")
    
    try:
        # Test session creation
        session_id = "test-session"
        await sandbox.process.create_session(session_id)
        print(f"✅ Session created: {session_id}")
        
        # Test command execution
        from sandbox.docker_sandbox import SessionExecuteRequest
        
        request = SessionExecuteRequest("echo 'Hello from Docker sandbox!'")
        result = await sandbox.process.execute_session_command(session_id, request)
        
        if "Hello from Docker sandbox!" in result:
            print(f"✅ Command execution successful")
        else:
            print(f"❌ Command execution failed: unexpected output")
        
        return True
    except Exception as e:
        print(f"❌ Process operations failed: {e}")
        return False


async def test_sandbox_cleanup(sandbox):
    """Test sandbox cleanup."""
    print("🧹 Testing sandbox cleanup...")
    
    try:
        await sandbox.delete()
        print(f"✅ Sandbox cleanup successful")
        return True
    except Exception as e:
        print(f"❌ Sandbox cleanup failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Docker Sandbox Test Suite")
    print("=" * 50)
    
    # Test Docker connection
    manager = await test_docker_connection()
    if not manager:
        print("❌ Cannot proceed without Docker connection")
        return
    
    # Test sandbox creation
    sandbox = await test_sandbox_creation(manager)
    if not sandbox:
        print("❌ Cannot proceed without sandbox")
        return
    
    try:
        # Test file operations
        file_ops_success = await test_file_operations(sandbox)
        
        # Test process operations
        process_ops_success = await test_process_operations(sandbox)
        
        # Test sandbox cleanup
        cleanup_success = await test_sandbox_cleanup(sandbox)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"File Operations: {'✅ PASS' if file_ops_success else '❌ FAIL'}")
        print(f"Process Operations: {'✅ PASS' if process_ops_success else '❌ FAIL'}")
        print(f"Cleanup: {'✅ PASS' if cleanup_success else '❌ FAIL'}")
        
        if all([file_ops_success, process_ops_success, cleanup_success]):
            print("\n🎉 All tests passed! Docker sandbox is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        # Try to cleanup anyway
        try:
            await sandbox.delete()
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
