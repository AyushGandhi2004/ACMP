import os
import docker
import tempfile
from pathlib import Path

from app.agents.base import BaseAgent
from app.graph.state import AgentState
from app.core.config import get_settings


# ─────────────────────────────────────────
# LANGUAGE CONFIGURATIONS
# Maps detected language to:
# - Docker base image
# - File extension
# - Test runner command
# - Requirements file name
# ─────────────────────────────────────────

LANGUAGE_CONFIG = {
    "python": {
        "image":        "python:3.12-slim",
        "extension":    ".py",
        "test_file":    "test_main.py",
        "source_file":  "main.py",
        "install_cmd":  "pip install pytest -q",
        "test_cmd":     "pytest test_main.py -v"
    },
    "javascript": {
        "image":        "node:20-slim",
        "extension":    ".js",
        "test_file":    "main.test.js",
        "source_file":  "main.js",
        "install_cmd":  "npm install jest --save-dev -q",
        "test_cmd":     "npx jest main.test.js --no-coverage"
    },
    "typescript": {
        "image":        "node:20-slim",
        "extension":    ".ts",
        "test_file":    "main.test.ts",
        "source_file":  "main.ts",
        "install_cmd":  "npm install jest ts-jest typescript --save-dev -q",
        "test_cmd":     "npx jest main.test.ts --no-coverage"
    },
    "java": {
        "image":        "openjdk:21-slim",
        "extension":    ".java",
        "test_file":    "MainTest.java",
        "source_file":  "Main.java",
        "install_cmd":  "apt-get install -y junit5 -q",
        "test_cmd":     "javac Main.java MainTest.java && java -jar junit-platform-console-standalone.jar --select-class=MainTest"
    }
}

# Fallback config if language not recognized
DEFAULT_CONFIG = LANGUAGE_CONFIG["python"]


class ValidatorAgent(BaseAgent):
    """
    Validator Agent — Fifth agent in the ACMP pipeline.

    Responsibilities:
    - Create isolated Docker sandbox environment
    - Write modernized code and unit tests to temp directory
    - Install required dependencies inside container
    - Run unit tests and capture all output
    - Determine pass or fail based on exit code
    - Clean up container after execution

    This is the most infrastructurally complex agent.
    Uses Docker SDK to spin up real containers.

    Input  (from state): modern_code, unit_tests, metadata, session_id
    Output (to state)  : validation_logs, status
    """

    def __init__(self):
        self.settings = get_settings()
        # Connect to Docker daemon
        # Requires /var/run/docker.sock to be mounted
        self.docker_client = docker.from_env()


    def _get_language_config(self, language: str) -> dict:
        """
        Get Docker and file config for detected language.

        Args:
            language: Detected language string

        Returns:
            Config dict with image, commands, file names
        """
        return LANGUAGE_CONFIG.get(language.lower(), DEFAULT_CONFIG)


    def _create_sandbox_directory(self, session_id: str) -> Path:
        """
        Create an isolated temp directory for this pipeline run.
        Uses session_id to prevent collisions between concurrent runs.

        Args:
            session_id: Unique pipeline run identifier

        Returns:
            Path object pointing to the created directory
        """
        sandbox_path = Path("/temp_sandboxes") / session_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        return sandbox_path


    def _write_files(
        self,
        sandbox_path: Path,
        modern_code: str,
        unit_tests: str,
        config: dict
    ) -> None:
        """
        Write modernized code and unit tests
        to the sandbox directory.

        Args:
            sandbox_path: Path to sandbox directory
            modern_code:  Modernized code from Engineer agent
            unit_tests:   Unit tests from Logic Anchor agent
            config:       Language configuration dict
        """
        # Write modernized source code
        source_file = sandbox_path / config["source_file"]
        source_file.write_text(modern_code, encoding="utf-8")

        # Write unit tests
        test_file = sandbox_path / config["test_file"]
        test_file.write_text(unit_tests, encoding="utf-8")


    def _run_container(
        self,
        sandbox_path: Path,
        config: dict
    ) -> tuple[str, int]:
        """
        Spin up a Docker container, install dependencies,
        run tests and capture all output.

        Args:
            sandbox_path: Path to sandbox directory to mount
            config:       Language configuration dict

        Returns:
            tuple of (logs string, exit code int)
        """
        container = None

        try:
            # Build the full command:
            # install dependencies first, then run tests
            full_command = (
                f"sh -c '{config['install_cmd']} && {config['test_cmd']}'"
            )

            # Run container with:
            # - correct base image for detected language
            # - sandbox directory mounted as /workspace
            # - working directory set to /workspace
            # - timeout to prevent infinite hangs
            container = self.docker_client.containers.run(
                image=config["image"],
                command=full_command,
                volumes={
                    str(sandbox_path): {
                        "bind": "/workspace",
                        "mode": "rw"
                    }
                },
                working_dir="/workspace",
                detach=True,            # run in background
                remove=False,           # we remove manually in finally
            )

            # Wait for container to finish with timeout
            result = container.wait(
                timeout=self.settings.docker_timeout
            )
            exit_code = result.get("StatusCode", 1)

            # Capture all logs (stdout + stderr combined)
            logs = container.logs(
                stdout=True,
                stderr=True
            ).decode("utf-8")

            return logs, exit_code

        except Exception as e:
            # Container timed out or Docker error
            return f"Container execution error: {str(e)}", 1

        finally:
            # ALWAYS clean up container — success or failure
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass    # container already removed — ignore


    def _cleanup_sandbox(self, sandbox_path: Path) -> None:
        """
        Remove sandbox directory after validation.
        Prevents temp_sandboxes from filling up disk.

        Args:
            sandbox_path: Path to sandbox directory to remove
        """
        try:
            import shutil
            shutil.rmtree(str(sandbox_path), ignore_errors=True)
        except Exception:
            pass    # cleanup failure should never crash the pipeline


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Validator Agent.
        Called by validator_node in nodes.py

        Args:
            state: Current AgentState containing
                   modern_code, unit_tests,
                   metadata and session_id

        Returns:
            dict: {
                "validation_logs": "captured output",
                "status": "validation_passed" or "validation_failed"
            }
        """
        modern_code = state.get("modern_code", "")
        unit_tests  = state.get("unit_tests", "")
        metadata    = state.get("metadata", {})
        session_id  = state.get("session_id", "default_session")
        language    = metadata.get("language", "python")

        # Step 1 — Get language specific Docker config
        config = self._get_language_config(language)

        # Step 2 — Create isolated sandbox directory
        sandbox_path = self._create_sandbox_directory(session_id)

        try:
            # Step 3 — Write code and tests to sandbox
            self._write_files(
                sandbox_path,
                modern_code,
                unit_tests,
                config
            )

            # Step 4 — Run Docker container and capture output
            logs, exit_code = self._run_container(
                sandbox_path,
                config
            )

            # Step 5 — Determine status from exit code
            # Exit code 0 = all tests passed
            # Any other exit code = tests failed
            if exit_code == 0:
                status = "validation_passed"
            else:
                status = "validation_failed"

            return {
                "validation_logs": logs,
                "status": status
            }

        finally:
            # ALWAYS clean up sandbox directory
            self._cleanup_sandbox(sandbox_path)