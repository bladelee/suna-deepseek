import json
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import time
from uuid import uuid4

from agentpress.tool import ToolResult, openapi_schema, usage_example
from agentpress.thread_manager import ThreadManager
from sandbox.tool_base import SandboxToolsBase
from utils.logger import logger


class SandboxWebDevTool(SandboxToolsBase):
    WORKSPACE_PATH = "/workspace"
    TEMPLATE_DIR = "/opt/templates/next-app"
    DEFAULT_TIMEOUT = 60
    BUILD_TIMEOUT = 1800
    INSTALL_TIMEOUT = 900
    DEFAULT_PORT = 3000

    def __init__(self, project_id: str, thread_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.thread_id = thread_id
        self._sessions: Dict[str, str] = {}
        self.workspace_path = self.WORKSPACE_PATH

    async def _ensure_session(self, session_name: str = "default") -> str:
        if session_name not in self._sessions:
            session_id = str(uuid4())
            try:
                await self._ensure_sandbox()
                await self.sandbox.process.create_session(session_id)
                self._sessions[session_name] = session_id
            except Exception as e:
                raise RuntimeError(f"Failed to create session: {str(e)}")
        return self._sessions[session_name]

    async def _execute_command(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        session_id = await self._ensure_session("web_dev_commands")
        from daytona_sdk import SessionExecuteRequest
        
        req = SessionExecuteRequest(
            command=command,
            var_async=False,
            cwd=self.workspace_path
        )
        
        response = await self.sandbox.process.execute_session_command(
            session_id=session_id,
            request=req,
            timeout=timeout
        )
        
        logs = await self.sandbox.process.get_session_command_logs(
            session_id=session_id,
            command_id=response.cmd_id
        )
        
        return {
            "output": logs,
            "exit_code": response.exit_code
        }

    async def _exec_sh(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        await self._ensure_sandbox()
        resp = await self.sandbox.process.exec(f"/bin/sh -c \"{command}\"", timeout=timeout)
        output = getattr(resp, "result", None) or getattr(resp, "output", "") or ""
        return {"exit_code": getattr(resp, "exit_code", 1), "output": output}

    async def _run_in_tmux_background(self, session: str, command: str) -> None:
        await self._ensure_sandbox()
        await self._exec_sh(f"tmux has-session -t {session} 2>/dev/null || tmux new-session -d -s {session}")
        escaped = command.replace('"', '\\"')
        await self._exec_sh(f"tmux send-keys -t {session} \"cd {self.workspace_path} && {escaped}\" C-m")

    def _get_project_path(self, project_name: str) -> str:
        return f"{self.workspace_path}/{project_name}"

    async def _project_exists(self, project_name: str) -> bool:
        check_result = await self._exec_sh(f"test -f {self._get_project_path(project_name)}/package.json && echo OK || echo MISS")
        return "OK" in check_result.get("output", "")

    async def _has_src_directory(self, project_path: str) -> bool:
        src_check = await self._exec_sh(f"test -d {project_path}/src && echo YES || echo NO")
        return "YES" in src_check.get("output", "")

    def _get_package_manager_command(self, package_manager: str, command_type: str, additional_args: str = "") -> str:
        commands = {
            "pnpm": {
                "install": f"pnpm install --prefer-offline {additional_args}",
                "add": f"pnpm add {additional_args}",
                "add_dev": f"pnpm add -D {additional_args}",
                "build": "pnpm run build",
                "dev": "pnpm run dev",
                "start": "pnpm run start"
            },
            "npm": {
                "install": f"npm install --no-audit --no-fund --progress=false {additional_args}",
                "add": f"npm install --save {additional_args}",
                "add_dev": f"npm install --save-dev {additional_args}",
                "build": "npm run build",
                "dev": "npm run dev",
                "start": "npm run start"
            }
        }
        return commands.get(package_manager, commands["npm"]).get(command_type, "")

    async def _has_optimized_template(self) -> bool:
        dir_check = await self._exec_sh(f"test -d {self.TEMPLATE_DIR} && echo EXISTS || echo MISSING")
        if "MISSING" in dir_check.get("output", ""):
            logger.debug(f"Template directory {self.TEMPLATE_DIR} does not exist")
            return False
        
        checks = [
            (f"test -f {self.TEMPLATE_DIR}/package.json", "package.json"),
            (f"test -f {self.TEMPLATE_DIR}/components.json", "components.json"), 
            (f"test -d {self.TEMPLATE_DIR}/src/components/ui", "src/components/ui directory")
        ]
        
        missing_files = []
        for check_cmd, file_desc in checks:
            result = await self._exec_sh(check_cmd)
            if result.get("exit_code") != 0:
                missing_files.append(file_desc)
        
        if missing_files:
            logger.debug(f"Template missing files: {', '.join(missing_files)}")
            ls_result = await self._exec_sh(f"ls -la {self.TEMPLATE_DIR}")
            logger.debug(f"Template directory contents: {ls_result.get('output', 'Could not list')}")
            return False
        
        logger.debug("Optimized template found and validated")
        return True

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Get the file structure of a web project, showing important files and directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Name of the project directory to examine"},
                    "max_depth": {"type": "integer", "description": "Maximum depth to traverse (default: 3)", "default": 3}
                },
                "required": ["project_name"]
            }
        }
    })
    @usage_example('''
        <!-- Get structure of a project -->
        <function_calls>
        <invoke name="get_project_structure">
        <parameter name="project_name">my-app</parameter>
        </invoke>
        </function_calls>
        ''')
    async def get_project_structure(self, project_name: str, max_depth: int = 3) -> ToolResult:
        try:
            await self._ensure_sandbox()
            project_path = self._get_project_path(project_name)
            
            check_cmd = f"test -d {project_path} && echo '__DIR_EXISTS__' || echo '__DIR_MISSING__'"
            check_result = await self._execute_command(check_cmd)
            
            if "__DIR_MISSING__" in check_result.get("output", ""):
                return self.fail_response(f"Project '{project_name}' not found.")

            tree_cmd = (
                f"cd {project_path} && find . -maxdepth {max_depth} -type f -o -type d | "
                "grep -v node_modules | grep -v '\\.next' | grep -v '\\.git' | grep -v 'dist' | sort"
            )
            tree_result = await self._execute_command(tree_cmd)
            
            if tree_result.get("exit_code") != 0:
                return self.fail_response(f"Failed to get project structure: {tree_result.get('output')}")

            structure = tree_result.get("output", "")

            package_info = ""
            package_cmd = f"test -f {project_path}/package.json && cat {project_path}/package.json | grep -E '\"(name|version|scripts)\"' -A 5 | head -20"
            package_result = await self._execute_command(package_cmd)
            
            if package_result.get("exit_code") == 0:
                package_info = f"\n\n📋 Package.json info:\n{package_result.get('output', '')}"

            return self.success_response(f"""
📁 Project structure for '{project_name}':

{structure}
{package_info}

To run this project:
1. Use install_dependencies if needed
2. Use start_server (mode='dev' or 'prod')
3. Use expose_port to make it publicly accessible (start_server returns the preview URL)
""")

        except Exception as e:
            logger.error(f"Error getting project structure: {str(e)}", exc_info=True)
            return self.fail_response(f"Error getting project structure: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "build_project",
            "description": "Run production build for the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "package_manager": {"type": "string", "default": "pnpm"}
                },
                "required": ["project_name"]
            }
        }
    })
    @usage_example('''
        <!-- Build a Next.js project for production -->
        <function_calls>
        <invoke name="build_project">
        <parameter name="project_name">my-app</parameter>
        <parameter name="package_manager">pnpm</parameter>
        </invoke>
        </function_calls>
        ''')
    async def build_project(self, project_name: str, package_manager: str = "pnpm") -> ToolResult:
        try:
            await self._ensure_sandbox()
            
            if not await self._project_exists(project_name):
                return self.fail_response(f"Project '{project_name}' not found")

            proj_dir = self._get_project_path(project_name)
            cmd = self._get_package_manager_command(package_manager, "build")
            
            res = await self._exec_sh(f"cd {proj_dir} && {cmd}", timeout=self.BUILD_TIMEOUT)
            
            if res["exit_code"] != 0:
                return self.fail_response(f"Build failed: {res['output']}")
            
            return self.success_response(f"Build completed for '{project_name}'.")

        except Exception as e:
            logger.error(f"Error building project: {e}", exc_info=True)
            return self.fail_response(f"Error building project: {e}")
