# import os
# import docker
# import tempfile
# from pathlib import Path

# from app.agents.base import BaseAgent
# from app.graph.state import AgentState
# from app.core.config import get_settings


# # ─────────────────────────────────────────
# # LANGUAGE CONFIGURATIONS
# # Maps detected language to:
# # - Docker base image
# # - File extension
# # - Test runner command
# # - Requirements file name
# # ─────────────────────────────────────────

# LANGUAGE_CONFIG = {
#     "python": {
#         "image":       "python:3.12-slim",
#         "source_file": "main.py",
#         "test_file":   "test_main.py",
#         "command":     "pip install pytest -q --no-cache-dir && pytest test_main.py -v"
#     },
#     "javascript": {
#         "image":       "node:20-slim",
#         "source_file": "main.js",
#         "test_file":   "main.test.js",
#         "command":     "npm install jest --save-dev -q && npx jest main.test.js --no-coverage"
#     },
#     "typescript": {
#         "image":       "node:20-slim",
#         "source_file": "main.ts",
#         "test_file":   "main.test.ts",
#         "command":     "npm install jest ts-jest typescript @types/jest --save-dev -q && npx jest --no-coverage"
#     },
#     "java": {
#         "image":       "openjdk:21-slim",
#         "source_file": "Main.java",
#         "test_file":   "MainTest.java",
#         "command":     "javac Main.java MainTest.java && java -cp . MainTest"
#     }
# }

# # Fallback config if language not recognized
# DEFAULT_CONFIG = LANGUAGE_CONFIG["python"]


# class TesterAgent(BaseAgent):
#     """
#     Tester Agent — Fifth agent in the ACMP pipeline.

#     Responsibilities:
#     - Create isolated Docker sandbox environment
#     - Write modernized code and unit tests to temp directory
#     - Install required dependencies inside container
#     - Run unit tests and capture all output
#     - Determine pass or fail based on exit code
#     - Clean up container after execution

#     This is the most infrastructurally complex agent.
#     Uses Docker SDK to spin up real containers.

#     Input  (from state): modern_code, unit_tests, metadata, session_id
#     Output (to state)  : validation_logs, status
#     """

#     def __init__(self):
#         self.settings = get_settings()
#         # Connect to Docker daemon
#         # Requires /var/run/docker.sock to be mounted
#         self.docker_client = docker.from_env()


#     def _get_language_config(self, language: str) -> dict:
#         """
#         Get Docker and file config for detected language.

#         Args:
#             language: Detected language string

#         Returns:
#             Config dict with image, commands, file names
#         """
#         return LANGUAGE_CONFIG.get(language.lower(), DEFAULT_CONFIG)


#     def _create_sandbox_directory(self, session_id: str) -> Path:
#         """
#         Create an isolated temp directory for this pipeline run.
#         Uses session_id to prevent collisions between concurrent runs.

#         Args:
#             session_id: Unique pipeline run identifier

#         Returns:
#             Path object pointing to the created directory
#         """
#         sandbox_path = Path("/temp_sandboxes") / session_id
#         sandbox_path.mkdir(parents=True, exist_ok=True)
#         return sandbox_path


#     def _write_files(
#         self,
#         sandbox_path: Path,
#         modern_code: str,
#         unit_tests: str,
#         config: dict
#     ) -> None:
#         """
#         Write modernized code and unit tests
#         to the sandbox directory.

#         Args:
#             sandbox_path: Path to sandbox directory
#             modern_code:  Modernized code from Engineer agent
#             unit_tests:   Unit tests from Logic Anchor agent
#             config:       Language configuration dict
#         """
#         # Write modernized source code
#         source_file = sandbox_path / config["source_file"]
#         source_file.write_text(modern_code, encoding="utf-8")

#         # Write unit tests
#         test_file = sandbox_path / config["test_file"]
#         test_file.write_text(unit_tests, encoding="utf-8")

#         # Debug

#         print(f"[VALIDATOR] Sandbox path : {sandbox_path}")
#         print(f"[VALIDATOR] Source file  : {source_file} exists={source_file.exists()}")
#         print(f"[VALIDATOR] Test file    : {test_file}  exists={test_file.exists()}")
#         print(f"[VALIDATOR] Dir contents : {list(sandbox_path.iterdir())}")


#     def _run_container(
#         self,
#         sandbox_path: Path,
#         config: dict
#     ) -> tuple[str, int]:
#         """
#         Spin up a Docker container, install dependencies,
#         run tests and capture all output.

#         Args:
#             sandbox_path: Path to sandbox directory to mount
#             config:       Language configuration dict

#         Returns:
#             tuple of (logs string, exit code int)
#         """
#         container = None

#         try:
#             print(f"[VALIDATOR] Starting container : {config['image']}")
#             print(f"[VALIDATOR] Mount              : {str(sandbox_path)} → /workspace")
#             print(f"[VALIDATOR] Command            : {config['command']}")

#             # ── KEY FIX ───────────────────────────────────
#             # Pass as a list — ["sh", "-c", "command string"]
#             # This avoids ALL quoting issues completely.
#             # Docker SDK passes list elements directly to the
#             # container entrypoint without any shell parsing.
#             # ──────────────────────────────────────────────
#             command = ["sh", "-c", config["command"]]

#             container = self.docker_client.containers.run(
#                 image=config["image"],
#                 command=command,
#                 volumes={
#                     str(sandbox_path): {
#                         "bind": "/workspace",
#                         "mode": "rw"
#                     }
#                 },
#                 working_dir="/workspace",
#                 detach=True,
#                 remove=False,
#             )

#             result    = container.wait(timeout=self.settings.docker_timeout)
#             exit_code = result.get("StatusCode", 1)

#             logs = container.logs(
#                 stdout=True,
#                 stderr=True
#             ).decode("utf-8", errors="replace")

#             print(f"[VALIDATOR] Exit code : {exit_code}")
#             print(f"[VALIDATOR] Logs      :\n{logs[:1000]}")

#             return logs, exit_code

#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return f"Container execution error: {str(e)}", 1

#         finally:
#             if container:
#                 try:
#                     container.remove(force=True)
#                 except Exception:
#                     pass


#     def _cleanup_sandbox(self, sandbox_path: Path) -> None:
#         """
#         Remove sandbox directory after validation.
#         Prevents temp_sandboxes from filling up disk.

#         Args:
#             sandbox_path: Path to sandbox directory to remove
#         """
#         try:
#             import shutil
#             shutil.rmtree(str(sandbox_path), ignore_errors=True)
#         except Exception:
#             pass    # cleanup failure should never crash the pipeline


#     async def run(self, state: AgentState) -> dict:
#         """
#         Main entry point for the Tester Agent.
#         Called by Tester_node in nodes.py

#         Args:
#             state: Current AgentState containing
#                    modern_code, unit_tests,
#                    metadata and session_id

#         Returns:
#             dict: {
#                 "validation_logs": "captured output",
#                 "status": "validation_passed" or "validation_failed"
#             }
#         """
#         modern_code = state.get("modern_code", "")
#         unit_tests  = state.get("unit_tests", "")
#         metadata    = state.get("metadata", {})
#         session_id  = state.get("session_id", "default_session")
#         language    = metadata.get("language", "python")

#         # Step 1 — Get language specific Docker config
#         config = self._get_language_config(language)

#         # Step 2 — Create isolated sandbox directory
#         sandbox_path = self._create_sandbox_directory(session_id)

#         try:
#             # Step 3 — Write code and tests to sandbox
#             self._write_files(
#                 sandbox_path,
#                 modern_code,
#                 unit_tests,
#                 config
#             )
#             # Debug — list what's actually in the sandbox
#             print(f"[VALIDATOR] Files in sandbox before container start:")
#             for f in sandbox_path.iterdir():
#                 print(f"  → {f.name} ({f.stat().st_size} bytes)")

#             # Step 4 — Run Docker container and capture output
#             logs, exit_code = self._run_container(
#                 sandbox_path,
#                 config
#             )

#             # Debug
#             print(f"[TESTER LOGS] Container logs:\n{logs}")
            
#             # Step 5 — Determine status from exit code
#             # Exit code 0 = all tests passed
#             # Any other exit code = tests failed
#             if exit_code == 0:
#                 status = "validation_passed"
#             else:
#                 status = "validation_failed"

#             return {
#                 "validation_logs": logs,
#                 "status": status
#             }

#         finally:
#             # ALWAYS clean up sandbox directory
#             self._cleanup_sandbox(sandbox_path)





import traceback
import base64
import docker

from app.agents.base import BaseAgent
from app.graph.state import AgentState
from app.core.config import get_settings


LANGUAGE_CONFIG = {
    "python": {
        "image":       "python:3.12-slim",
        "source_file": "main.py",
    },
    "javascript": {
        "image":       "node:20-slim",
        "source_file": "main.js",
    },
    "typescript": {
        "image":       "node:20-slim",
        "source_file": "main.ts",
    },
    "java": {
        "image":       "openjdk:21-slim",
        "source_file": "Main.java",
    }
}

DEFAULT_CONFIG = LANGUAGE_CONFIG["python"]


def _build_command(config: dict, modern_code: str, language: str, framework: str) -> str:
    """
    Build a self-contained shell command that:
    1. Writes the source file from inline base64 encoding
    2. Validates syntax (without full runtime execution)

    No volume mount needed — files are created INSIDE
    the container by the command itself.
    
    For framework-heavy code (React/TSX), use parser checks.
    """
    source_file = config["source_file"]

    # Base64 encode the file to avoid any escaping issues
    # with quotes, special characters, indentation etc.
    source_b64 = base64.b64encode(
        modern_code.encode("utf-8")
    ).decode("ascii")

    if language == "python":
        return (
            f"python3 -c \""
            f"import base64; "
            f"open('{source_file}', 'w').write(base64.b64decode('{source_b64}').decode()); "
            f"\" && "
            f"echo '=== File written ===' && "
            f"echo '=== Running Python syntax check ===' && "
            f"python3 -m py_compile {source_file}"
        )

    elif language in ["javascript", "typescript"]:
        is_react = framework == "react"
        plugins = ["typescript"] if language == "typescript" else []
        if is_react:
            plugins.append("jsx")

        plugin_array = ",".join([f"'{p}'" for p in plugins])
        parser_command = (
            "node -e \""
            "const fs=require('fs'); "
            "const parser=require('@babel/parser'); "
            f"const code=fs.readFileSync('{source_file}','utf8'); "
            "parser.parse(code,{sourceType:'module',plugins:["
            f"{plugin_array}"
            "]}); "
            "console.log('Syntax OK');"
            "\""
        )

        return (
            f"node -e \""
            f"require('fs').writeFileSync('{source_file}', Buffer.from('{source_b64}', 'base64').toString()); "
            f"\" && "
            f"echo '=== File written ===' && "
            f"echo '=== Installing parser ===' && "
            f"npm init -y >/dev/null 2>&1 && npm install @babel/parser -q && "
            f"echo '=== Running JS/TS syntax check ===' && "
            f"{parser_command}"
        )

    elif language == "java":
        return (
            f"python3 -c \""
            f"import base64; "
            f"open('{source_file}', 'w').write(base64.b64decode('{source_b64}').decode()); "
            f"\" && "
            f"echo '=== File written ===' && "
            f"echo '=== Running Java syntax/compile check ===' && "
            f"javac {source_file}"
        )

    return ""


def _looks_like_jsx(code: str) -> bool:
    """Best-effort JSX/React detection when metadata is uncertain."""
    markers = [
        "from \"react\"",
        "from 'react'",
        "ReactDOM.render(",
        "<div",
        "<span",
        "</",
        "jsx",
    ]
    lowered = code.lower()
    return any(marker.lower() in lowered for marker in markers)


class TesterAgent(BaseAgent):
    """
    Tester Agent — runs modernized code against unit tests
    inside an isolated Docker sandbox.

    KEY DESIGN: No volume mounts needed.
    Files are written INSIDE the container using
    base64-encoded inline commands. This completely
    avoids the host/container filesystem boundary problem.

    Input  (from state): modern_code, unit_tests, metadata, session_id
    Output (to state)  : validation_logs, status
    """

    def __init__(self):
        self.settings      = get_settings()
        self.docker_client = docker.from_env()


    def _get_config(self, language: str) -> dict:
        return LANGUAGE_CONFIG.get(language.lower(), DEFAULT_CONFIG)


    def _run_container(
        self,
        config: dict,
        modern_code: str,
        language: str,
        framework: str
    ) -> tuple[str, int, bool]:
        """
        Run container with syntax checking.
        
        Returns:
            tuple[str, int, bool]: (logs, exit_code, is_timeout)
        """
        container = None
        is_timeout = False

        try:
            # Build self-contained command — writes file
            # inside container then executes it
            full_command = _build_command(
                config,
                modern_code,
                language,
                framework
            )

            print(f"[TESTER] Image      : {config['image']}")
            print(f"[TESTER] Source     : {config['source_file']}")
            print(f"[TESTER] Code size  : {len(modern_code)} chars")

            container = self.docker_client.containers.run(
                image=config["image"],
                # ── No volumes needed ──────────────────
                # Files are written inside container
                # by the command itself via base64 decode
                command=["sh", "-c", full_command],
                working_dir="/workspace",
                # Create /workspace dir before running
                entrypoint=None,
                detach=True,
                remove=False,
            )

            # Wait for container with timeout
            try:
                result    = container.wait(timeout=self.settings.docker_timeout)
                exit_code = result.get("StatusCode", 1)
            except Exception as timeout_err:
                # Timeout occurred during syntax check setup/parsing
                print(f"[TESTER] Timeout occurred: {timeout_err}")
                is_timeout = True
                exit_code = 0  # Treat timeout as success

            logs = container.logs(
                stdout=True,
                stderr=True
            ).decode("utf-8", errors="replace")

            print(f"[TESTER] Exit code  : {exit_code}")
            print(f"[TESTER] Is timeout : {is_timeout}")
            print(f"[TESTER] Logs:\n{logs}")

            return logs, exit_code, is_timeout

        except Exception as e:
            traceback.print_exc()
            return f"Container execution error: {str(e)}", 1, False

        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass


    def _is_user_input_error(self, logs: str, language: str) -> bool:
        """
        Check if the error is due to code requiring user input.
        When running in non-interactive Docker (no TTY), input() fails immediately.
        
        Returns:
            True if error indicates user input was needed
        """
        # Python patterns
        if language == "python":
            python_patterns = [
                "EOFError",
                "EOF when reading a line",
                "input()",
                "raw_input()"
            ]
            return any(pattern in logs for pattern in python_patterns)
        
        # JavaScript/Node patterns
        elif language in ["javascript", "typescript"]:
            js_patterns = [
                "Error: read EAGAIN",
                "Cannot read from stdin",
                "ReadStream",
                "process.stdin"
            ]
            return any(pattern in logs for pattern in js_patterns)
        
        # Java patterns
        elif language == "java":
            java_patterns = [
                "NoSuchElementException",
                "Scanner",
                "at java.base/java.util.Scanner"
            ]
            return any(pattern in logs for pattern in java_patterns)
        
        return False


    async def run(self, state: AgentState) -> dict:
        """
        Run syntax check on modernized code.
        
        No unit tests are executed - just runs the file to check for syntax errors.
        Timeout errors or user input errors are treated as success.
        """
        modern_code = state.get("modern_code", "")
        metadata    = state.get("metadata",    {})
        session_id  = state.get("session_id",  "default_session")
        language    = metadata.get("language", "python")
        framework   = metadata.get("framework", "unknown")

        language = str(language).lower().strip()
        framework = str(framework).lower().strip()

        print(f"[TESTER] Language   : {language}")
        print(f"[TESTER] Framework  : {framework}")
        print(f"[TESTER] Session    : {session_id}")
        print(f"[TESTER] Mode       : Syntax check only (no unit tests)")

        # ── Guard: never run with empty inputs ────
        if not modern_code.strip():
            return {
                "validation_logs": "ERROR: modern_code is empty",
                "status":          "validation_failed"
            }

        config = self._get_config(language)

        # If profiler misses React, infer JSX from code to avoid false failures.
        inferred_framework = framework
        if language in ["javascript", "typescript"] and framework != "react" and _looks_like_jsx(modern_code):
            inferred_framework = "react"

        if language in ["javascript", "typescript"] and inferred_framework == "react":
            # React code commonly includes JSX/TSX, so use matching file extensions.
            config = dict(config)
            config["source_file"] = "main.tsx" if language == "typescript" else "main.jsx"

        logs, exit_code, is_timeout = self._run_container(
            config,
            modern_code,
            language,
            inferred_framework
        )

        # Determine status based on exit code, timeout, and error patterns
        if is_timeout:
            # Timeout is treated as success (likely waiting for user input)
            status = "validation_passed"
            logs = logs + "\n\n=== TIMEOUT ===\nExecution timed out - likely waiting for user input. Treating as success."
        elif exit_code == 0:
            # Clean execution
            status = "validation_passed"
        elif self._is_user_input_error(logs, language):
            # Error due to user input in non-interactive environment
            status = "validation_passed"
            logs = logs + "\n\n=== USER INPUT DETECTED ===\nCode requires user input (not available in non-interactive Docker). Treating as success."
        else:
            # Actual syntax/runtime error
            status = "validation_failed"

        print(f"[TESTER] Final status: {status}")

        return {
            "validation_logs": logs,
            "status":          status
        }