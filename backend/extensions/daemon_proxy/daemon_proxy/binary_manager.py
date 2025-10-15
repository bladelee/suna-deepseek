"""
二进制文件管理模块
"""

import os
import shutil
import logging
import platform
from typing import Optional
from pathlib import Path


class UnsupportedArchitectureError(Exception):
    """不支持的架构异常"""
    pass


class BinaryManager:
    """二进制文件管理器"""
    
    def __init__(self, temp_dir: str = ".tmp/binaries"):
        self.temp_dir = Path(temp_dir)
        self.binary_path: Optional[Path] = None
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Binary temp directory: {self.temp_dir}")
    
    def _validate_architecture(self):
        """验证当前架构是否支持"""
        machine = platform.machine()
        if machine not in ['x86_64', 'AMD64']:
            raise UnsupportedArchitectureError(
                f"Only amd64 is supported, got {machine}"
            )
        logging.debug(f"Architecture validation passed: {machine}")
    
    def _validate_binary_file(self, source_path: str) -> Path:
        """验证源二进制文件"""
        source = Path(source_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Binary file not found: {source_path}")
        
        if not source.is_file():
            raise ValueError(f"Path is not a file: {source_path}")
        
        # 检查文件是否可读
        if not os.access(source, os.R_OK):
            raise PermissionError(f"Cannot read binary file: {source_path}")
        
        logging.debug(f"Binary file validation passed: {source_path}")
        return source
    
    def prepare_binary(self, source_path: str) -> str:
        """
        准备二进制文件
        
        Args:
            source_path: 源二进制文件路径
            
        Returns:
            准备好的二进制文件路径
            
        Raises:
            UnsupportedArchitectureError: 不支持的架构
            FileNotFoundError: 源文件不存在
            PermissionError: 权限不足
        """
        # 验证架构
        self._validate_architecture()
        
        # 验证源文件
        source = self._validate_binary_file(source_path)
        
        # 生成目标路径
        target_name = "daemon-amd64"
        target_path = self.temp_dir / target_name
        
        # 如果目标文件已存在且与源文件相同，直接返回
        if target_path.exists():
            if self._files_are_same(source, target_path):
                logging.debug(f"Binary file already prepared: {target_path}")
                self.binary_path = target_path
                return str(target_path)
            else:
                # 删除旧文件
                target_path.unlink()
                logging.debug(f"Removed outdated binary: {target_path}")
        
        try:
            # 复制文件
            shutil.copy2(source, target_path)
            logging.info(f"Copied binary from {source} to {target_path}")
            
            # 设置执行权限
            os.chmod(target_path, 0o755)
            logging.debug(f"Set executable permissions on {target_path}")
            
            # 验证目标文件
            if not os.access(target_path, os.X_OK):
                raise PermissionError(f"Cannot execute binary file: {target_path}")
            
            self.binary_path = target_path
            return str(target_path)
            
        except Exception as e:
            # 清理失败的文件
            if target_path.exists():
                target_path.unlink()
            raise Exception(f"Failed to prepare binary: {e}")
    
    def _files_are_same(self, file1: Path, file2: Path) -> bool:
        """检查两个文件是否相同"""
        try:
            return file1.stat().st_mtime == file2.stat().st_mtime and \
                   file1.stat().st_size == file2.stat().st_size
        except OSError:
            return False
    
    def get_binary_path(self) -> Optional[str]:
        """获取准备好的二进制文件路径"""
        return str(self.binary_path) if self.binary_path else None
    
    def cleanup(self):
        """清理临时文件"""
        if self.binary_path and self.binary_path.exists():
            try:
                self.binary_path.unlink()
                logging.info(f"Cleaned up binary file: {self.binary_path}")
            except Exception as e:
                logging.warning(f"Failed to cleanup binary file {self.binary_path}: {e}")
        
        # 清理临时目录（如果为空）
        try:
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                logging.debug(f"Removed empty temp directory: {self.temp_dir}")
        except Exception as e:
            logging.warning(f"Failed to cleanup temp directory {self.temp_dir}: {e}")
        
        self.binary_path = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
    
    def __del__(self):
        """析构函数"""
        self.cleanup()
