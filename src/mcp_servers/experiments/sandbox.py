"""
Code sandbox for safe experiment execution.

Provides isolated Python code execution with resource limits.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""

    success: bool
    stdout: str
    stderr: str
    return_value: Any
    execution_time_ms: float
    error: str | None = None


class CodeSandbox:
    """
    Sandboxed Python code execution environment.

    Provides safe execution of Python code with resource limits
    and restricted imports.
    """

    # Allowed imports for scientific computing
    ALLOWED_MODULES = {
        "numpy",
        "np",
        "pandas",
        "pd",
        "matplotlib",
        "plt",
        "scipy",
        "sklearn",
        "math",
        "statistics",
        "random",
        "json",
        "csv",
        "datetime",
        "collections",
        "itertools",
        "functools",
    }

    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize code sandbox.

        Args:
            timeout_seconds: Maximum execution time
        """
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger(__name__)

    async def execute(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute
            globals_dict: Optional global variables

        Returns:
            Execution result
        """
        start_time = datetime.utcnow()

        self.logger.info("executing_code", code_length=len(code))

        # Validate code for security
        try:
            self._validate_code(code)
        except ValueError as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_value=None,
                execution_time_ms=0,
                error=f"Code validation failed: {str(e)}",
            )

        # Prepare execution environment
        if globals_dict is None:
            globals_dict = {}

        # Add safe built-ins
        safe_globals = {
            "__builtins__": self._get_safe_builtins(),
            **globals_dict,
        }

        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Execute code
            exec(code, safe_globals)

            # Get return value if any
            return_value = safe_globals.get("__result__", None)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            result = ExecutionResult(
                success=True,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                return_value=return_value,
                execution_time_ms=execution_time,
            )

            self.logger.info(
                "code_executed_successfully",
                execution_time_ms=execution_time,
            )

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.logger.error("code_execution_failed", error=str(e))

            return ExecutionResult(
                success=False,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                return_value=None,
                execution_time_ms=execution_time,
                error=str(e),
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _validate_code(self, code: str) -> None:
        """
        Validate code for dangerous operations.

        Args:
            code: Code to validate

        Raises:
            ValueError: If code contains disallowed operations
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error: {str(e)}")

        # Check for dangerous operations
        for node in ast.walk(tree):
            # Block file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("open", "exec", "eval", "compile", "__import__"):
                        raise ValueError(f"Disallowed function: {node.func.id}")

            # Block imports of system modules
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._is_allowed_module(alias.name):
                        raise ValueError(f"Disallowed import: {alias.name}")

            if isinstance(node, ast.ImportFrom):
                if node.module and not self._is_allowed_module(node.module):
                    raise ValueError(f"Disallowed import: {node.module}")

    def _is_allowed_module(self, module_name: str) -> bool:
        """Check if module is allowed."""
        base_module = module_name.split(".")[0]
        return base_module in self.ALLOWED_MODULES

    def _get_safe_builtins(self) -> dict[str, Any]:
        """Get safe subset of built-in functions."""
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }
        return safe_builtins


# Convenience function
async def execute_python_code(
    code: str,
    timeout_seconds: int = 300,
) -> ExecutionResult:
    """
    Execute Python code in sandbox.

    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time

    Returns:
        Execution result
    """
    sandbox = CodeSandbox(timeout_seconds=timeout_seconds)
    return await sandbox.execute(code)
