#!/usr/bin/env python3
"""
E2E Test Runner with Dynamic Port Assignment and Parallel Execution

This script automatically:
1. Finds an available port
2. Starts the server on that port
3. Runs the e2e tests against the server (in parallel by default)
4. Cleans up the server process

Usage:
  python scripts/run_e2e_tests.py                    # Parallel execution (auto workers) - DEFAULT
  python scripts/run_e2e_tests.py --serial           # Sequential execution
  python scripts/run_e2e_tests.py -n 4               # Parallel execution (4 workers)
"""

import argparse
import io
import json
import multiprocessing
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from queue import Queue
from typing import IO

from dotenv import load_dotenv

# Port allocation strategy for E2E test isolation
# Each test run gets its own port range to avoid conflicts
BASE_PORT = 55000  # Start of E2E port range (away from default Supabase ports)
PORTS_PER_INSTANCE = 10  # Each Supabase instance needs ~10 ports
MAX_INSTANCES = 10  # Support up to 10 parallel test runs


class QuietSetup:
    """Context manager to suppress setup output unless there's a failure."""

    def __init__(self) -> None:
        self.output_buffer = io.StringIO()
        self.failed_stage = None
        self._lock = threading.Lock()

    def capture_print(self, message: str) -> None:
        """Capture a print message to the buffer (thread-safe)."""
        with self._lock:
            self.output_buffer.write(message + "\n")

    def fail(self, stage_name: str) -> None:
        """Mark this setup stage as failed and prepare to show output (thread-safe)."""
        with self._lock:
            self.failed_stage = stage_name

    def show_if_failed(self) -> bool:
        """Show captured output if any stage failed (thread-safe)."""
        with self._lock:
            if self.failed_stage:
                print(f"❌ Setup failed during: {self.failed_stage}\n")
                print(self.output_buffer.getvalue())
                return True
            return False


def find_free_port() -> int:
    """Find an available port using Python's socket library."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Bind to any available port
        s.listen(1)
        port = s.getsockname()[1]
    return port


def find_available_port_range() -> dict[str, int] | None:
    """
    Find an available port range for Supabase E2E instance.

    Tries each range sequentially (55000-55009, 55010-55019, etc.)
    by checking if ALL ports in each range are available.

    Returns:
        dict with port mappings if range found, None if all ranges busy
    """
    for instance_num in range(MAX_INSTANCES):
        base_port = BASE_PORT + (instance_num * PORTS_PER_INSTANCE)

        # Check if ALL ports in this range are available
        all_ports_available = True
        for port_offset in range(PORTS_PER_INSTANCE):
            port = base_port + port_offset
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    # Port is available, continue checking
            except OSError:
                # This port is in use, try next range
                all_ports_available = False
                break

        if all_ports_available:
            # All ports in this range are available!
            port_mapping = {
                "api": base_port,
                "db": base_port + 1,
                "db_shadow": base_port + 2,
                "db_pooler": base_port + 3,
                "studio": base_port + 4,
                "analytics": base_port + 5,
                "analytics_vector": base_port + 6,
                "inbucket": base_port + 7,
                "inbucket_smtp": base_port + 8,
                "inbucket_pop3": base_port + 9,
            }
            return port_mapping

    # All ranges are busy
    return None


def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for server to be ready by attempting to connect."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("localhost", port))
                if result == 0:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def stream_reader(
    stream: IO[bytes],
    queue: Queue[tuple[str, str]],
    prefix: str,
    console: IO[str] | None = None,
) -> None:
    """
    Read from a stream with immediate console output and line-buffered queue output.

    Reads in small chunks (1024 bytes) to minimize latency while maintaining efficiency.
    Writes immediately to console (for real-time dots/output) but only queues complete
    lines for the log file.

    Args:
        stream: Binary stream to read from (stdout/stderr pipe)
        queue: Queue to send complete lines to for log file writing
        prefix: Prefix label for queued lines (e.g., "STDOUT", "STDERR")
        console: Optional text stream for immediate output (e.g., sys.stdout)
    """
    try:
        # Line buffer for reconstituting complete lines
        line_buffer = b""

        # Read in small chunks for responsiveness
        # 1024 bytes balances latency vs syscall overhead
        while True:
            chunk = stream.read(1024)

            # EOF detection
            if not chunk:
                break

            # Write to console immediately for real-time output (dots, progress)
            if console:
                # Decode chunk for console output
                # Use 'replace' to handle partial UTF-8 sequences gracefully
                decoded_chunk = chunk.decode("utf-8", errors="replace")
                console.write(decoded_chunk)
                console.flush()

            # Accumulate in line buffer for reconstitution
            line_buffer += chunk

            # Extract and queue complete lines
            while b"\n" in line_buffer:
                # Split on first newline
                line, line_buffer = line_buffer.split(b"\n", 1)

                # Decode complete line and queue for log file
                decoded_line = line.decode("utf-8", errors="replace").rstrip()
                if decoded_line:  # Skip empty lines
                    queue.put((prefix, decoded_line))

        # Handle any remaining data without trailing newline (EOF flush)
        if line_buffer:
            decoded_line = line_buffer.decode("utf-8", errors="replace").rstrip()
            if decoded_line:
                queue.put((prefix, decoded_line))

    except Exception:
        # Silently fail - stream closed or other error
        # Thread will exit gracefully
        pass


def analyze_server_logs(
    log_lines: list[tuple[str, str]], expected_errors: list[tuple[str, str, int]]
) -> dict[str, list]:
    """Analyze server logs for errors and return error summary.

    Args:
        log_lines: List of (prefix, line) tuples from server logs
        expected_errors: List of (method, path, status) tuples for expected HTTP errors
    """
    http_errors = []
    python_errors = []
    stderr_lines = []

    # Patterns to detect errors
    http_error_pattern = re.compile(r'"\w+\s+[^"]+"\s+(4\d{2}|5\d{2})')  # HTTP 4xx/5xx
    error_log_pattern = re.compile(r"\bERROR\b|\bException\b|\bTraceback\b")

    for prefix, line in log_lines:
        # Track stderr output
        if prefix == "STDERR":
            stderr_lines.append(line)

        # Check for HTTP errors in access logs
        if http_error_pattern.search(line):
            # Check if this is an expected error
            is_expected = False
            for method, path, status in expected_errors:
                # Construct pattern: "METHOD path..." status
                pattern = rf'"{method} {path}[^"]*" {status}'
                if re.search(pattern, line):
                    is_expected = True
                    break

            if not is_expected:
                http_errors.append(line)

        # Check for Python errors/exceptions
        if error_log_pattern.search(line):
            python_errors.append(line)

    return {
        "http_errors": http_errors,
        "python_errors": python_errors,
        "stderr_lines": stderr_lines,
    }


def create_temp_supabase_dir(port_mapping: dict[str, int]) -> Path:
    """
    Create a temporary directory with Supabase configuration.

    Args:
        port_mapping: Dictionary of service names to port numbers

    Returns:
        Path to temporary directory
    """
    # Create unique temp directory name
    timestamp = int(time.time())
    random_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
    temp_name = f"e2e-{timestamp}-{random_id}"

    # Create temp directory
    temp_base = Path(tempfile.gettempdir()) / "supabase-e2e"
    temp_base.mkdir(exist_ok=True)
    temp_dir = temp_base / temp_name

    # Copy supabase/ directory to temp location (for migrations, seeds, etc.)
    project_root = Path(__file__).parent.parent
    supabase_src = project_root / "supabase"

    shutil.copytree(supabase_src, temp_dir / "supabase")

    # Generate a fresh config.toml using supabase init (like init.sh does)
    # This ensures we get a clean default config without duplicates
    config_path = temp_dir / "supabase" / "config.toml"
    init_temp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(
            ["supabase", "init", "--force"],
            cwd=init_temp,
            capture_output=True,
            check=True,
        )
        shutil.copy(init_temp / "supabase" / "config.toml", config_path)
    finally:
        shutil.rmtree(init_temp, ignore_errors=True)

    # Patch ports in the config (similar to init.sh sed commands)
    with open(config_path) as f:
        config_content = f.read()

    # Use unique project_id per run to ensure fresh Docker volumes
    # This prevents stale schema issues when migrations change
    unique_project_id = f"e2e-{timestamp}-{random_id}"
    config_replacements = [
        (r"^project_id = .*$", f'project_id = "{unique_project_id}"'),
        (r"^port = 54321$", f'port = {port_mapping["api"]}'),
        (r"^port = 54322$", f'port = {port_mapping["db"]}'),
        (r"^shadow_port = 54320$", f'shadow_port = {port_mapping["db_shadow"]}'),
        (r"^port = 54329$", f'port = {port_mapping["db_pooler"]}'),
        (r"^port = 54324$", f'port = {port_mapping["inbucket"]}'),
    ]
    for pattern, replacement in config_replacements:
        config_content = re.sub(
            pattern, replacement, config_content, flags=re.MULTILINE
        )

    with open(config_path, "w") as f:
        f.write(config_content)

    # Append storage bucket configuration from shared file
    storage_buckets_path = project_root / "supabase" / "storage-buckets.toml"
    if storage_buckets_path.exists():
        with open(storage_buckets_path) as f:
            storage_config = f.read()
        with open(config_path, "a") as f:
            f.write("\n")
            f.write(storage_config)

    return temp_dir


def start_supabase_instance(
    workdir: Path, quiet_setup: QuietSetup | None = None
) -> Path:
    """Start Supabase in the specified workdir."""

    def log(msg: str) -> None:
        if quiet_setup:
            quiet_setup.capture_print(msg)
        else:
            print(msg)

    log(f"🚀 Starting isolated Supabase instance in {workdir}")
    log("   (This may take several minutes if Supabase needs to update...)")

    # Exclude services not needed for e2e tests to speed up startup
    # Keep: postgres, gotrue, postgrest, kong, storage-api, mailpit
    # Skip: studio, edge-runtime, logflare, vector, imgproxy, realtime
    excluded_services = [
        "studio",  # Supabase web UI - not used in e2e tests
        "edge-runtime",  # Edge Functions - not used
        "logflare",  # Analytics - not needed
        "vector",  # Vector DB - not used
        "imgproxy",  # Image processing - not used
        "realtime",  # Websockets - not used in current tests
    ]

    # Build command with excluded services
    cmd = ["supabase", "start", "--workdir", str(workdir)]
    for service in excluded_services:
        cmd.extend(["--exclude", service])

    log(f"   Excluding services: {', '.join(excluded_services)}")

    # Run with output streaming so we can see what's happening
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=bool(quiet_setup),  # Capture output in quiet mode
        timeout=900,  # 15 minute timeout for startup (allows for Docker image updates)
    )

    if result.returncode != 0:
        if quiet_setup:
            quiet_setup.capture_print(
                f"❌ Failed to start Supabase (exit code: {result.returncode})"
            )
            if result.stdout:
                quiet_setup.capture_print(result.stdout)
            if result.stderr:
                quiet_setup.capture_print(result.stderr)
        else:
            print(f"❌ Failed to start Supabase (exit code: {result.returncode})")
        raise RuntimeError("Supabase failed to start")

    log("✅ Supabase instance started successfully")
    return workdir


def extract_supabase_env(
    workdir: Path, quiet_setup: QuietSetup | None = None
) -> dict[str, str]:
    """Extract environment variables from Supabase instance."""

    def log(msg: str) -> None:
        if quiet_setup:
            quiet_setup.capture_print(msg)
        else:
            print(msg)

    log("🔍 Extracting environment variables from Supabase instance")

    result = subprocess.run(
        ["supabase", "status", "--workdir", str(workdir), "-o", "env"],
        capture_output=True,  # Keep this one quiet, we only need the env vars
        text=True,
    )

    if result.returncode != 0:
        log("❌ Failed to get Supabase status")
        log(f"Stderr: {result.stderr}")
        raise RuntimeError("Failed to extract Supabase environment")

    # Parse environment variables from output
    # Format: KEY="value"
    env_vars = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("Using workdir"):
            key, value = line.split("=", 1)
            # Remove quotes
            value = value.strip('"')
            env_vars[key] = value

    # Map Supabase env vars to our application's expected names
    app_env = {}

    if "API_URL" in env_vars:
        app_env["SUPABASE_URL"] = env_vars["API_URL"]

    if "ANON_KEY" in env_vars:
        app_env["SUPABASE_ANON_KEY"] = env_vars["ANON_KEY"]

    if "SERVICE_ROLE_KEY" in env_vars:
        app_env["SUPABASE_SERVICE_KEY"] = env_vars["SERVICE_ROLE_KEY"]

    if "DB_URL" in env_vars:
        app_env["DATABASE_URL"] = env_vars["DB_URL"]

    if "JWT_SECRET" in env_vars:
        app_env["JWT_SECRET_KEY"] = env_vars["JWT_SECRET"]

    # Validate all required vars were extracted
    required = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        "DATABASE_URL",
        "JWT_SECRET_KEY",
    ]
    missing = [var for var in required if var not in app_env]

    if missing:
        log(f"❌ Missing required environment variables: {missing}")
        log(f"Raw Supabase output:\n{result.stdout}")
        raise RuntimeError("Failed to extract all required environment variables")

    log("✅ Successfully extracted environment variables")
    return app_env


def cleanup_supabase_instance(
    workdir: Path, quiet_setup: QuietSetup | None = None
) -> None:
    """Stop Supabase and cleanup temporary directory."""

    def log(msg: str) -> None:
        if quiet_setup:
            quiet_setup.capture_print(msg)
        else:
            print(msg)

    log(f"🧹 Cleaning up Supabase instance in {workdir}")

    try:
        # Stop Supabase
        subprocess.run(
            ["supabase", "stop", "--workdir", str(workdir)],
            capture_output=True,
            timeout=30,
        )
        log("✅ Supabase stopped")
    except Exception as e:
        log(f"⚠️  Warning: Failed to stop Supabase cleanly: {e}")

    try:
        # Remove temporary directory
        shutil.rmtree(workdir)
        log("✅ Temporary directory removed")
    except Exception as e:
        log(f"⚠️  Warning: Failed to remove temp directory: {e}")


def main() -> int:  # type: ignore[bad-return] - all paths return but pyrefly can't trace nested try/except/finally
    """Main e2e test runner."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run E2E tests with automatic server management (parallel by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Parallel execution (auto workers) - DEFAULT
  %(prog)s --serial                 # Sequential execution
  %(prog)s -n 4                     # Parallel execution (4 workers)
  %(prog)s tests/e2e/test_specific.py  # Run specific test file in parallel
        """.strip(),
    )

    # Parallel execution options
    parallel_group = parser.add_mutually_exclusive_group()
    parallel_group.add_argument(
        "--serial",
        action="store_true",
        help="Run tests sequentially (default is parallel with auto workers)",
    )
    parallel_group.add_argument(
        "-n",
        "--numprocesses",
        metavar="NUM",
        help="Number of parallel workers (e.g., '4')",
    )

    # Pytest passthrough arguments
    parser.add_argument(
        "pytest_args", nargs="*", help="Additional arguments to pass to pytest"
    )

    args, unknown_args = parser.parse_known_args()

    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Load environment variables from .env file
    load_dotenv()

    # Build parallel execution arguments
    # Default to parallel execution with auto workers unless --serial is specified
    parallel_args = []
    if args.serial:
        # Sequential execution - no parallel args
        parallel_args = []
    elif args.numprocesses:
        # Explicit worker count
        parallel_args = ["-n", args.numprocesses]
    else:
        # Default: parallel with auto workers
        parallel_args = ["-n", "auto"]

    # Determine worker count for uvicorn to match pytest workers
    worker_count = None
    if not args.serial:
        if args.numprocesses:
            try:
                worker_count = int(args.numprocesses)
            except ValueError:
                # If it's not a number (could be "auto" though we removed that option),
                # default to cpu count
                worker_count = multiprocessing.cpu_count()
        else:
            # Default parallel mode uses cpu count
            worker_count = multiprocessing.cpu_count()

    # Combine pytest_args with unknown_args (for passthrough arguments like --headed)
    pytest_args = args.pytest_args + unknown_args

    # Set default test path if none provided
    if not pytest_args or not any(arg.startswith("tests/") for arg in pytest_args):
        pytest_args.append("tests/e2e/")

    # Create quiet setup to suppress setup output unless there's a failure
    quiet = QuietSetup()
    print("⚙️  Setting up e2e test environment...", flush=True)

    # Create teardown handler (used later)
    teardown = QuietSetup()

    # Find available port
    port = find_free_port()
    base_url = f"http://localhost:{port}"

    quiet.capture_print(f"🔍 Found available port: {port}")
    quiet.capture_print(f"🌐 Server will run at: {base_url}")

    # Set environment variables for tests
    env = os.environ.copy()
    env["TEST_BASE_URL"] = base_url
    env["PORT"] = str(port)
    env["ENVIRONMENT"] = (
        "e2e"  # Enable e2e mode with stub AI services and built frontend
    )
    env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output for real-time pytest dots

    # Find an available port range for Supabase
    quiet.capture_print("🔍 Finding available port range for Supabase...")
    port_mapping = find_available_port_range()

    if port_mapping is None:
        quiet.fail("Port allocation")
        quiet.capture_print(
            f"❌ No available port ranges (tried {MAX_INSTANCES} ranges)"
        )
        quiet.capture_print(
            f"   All ports from {BASE_PORT} to {BASE_PORT + (MAX_INSTANCES * PORTS_PER_INSTANCE) - 1} are busy"
        )
        quiet.capture_print(
            "   Please wait for other E2E test runs to complete or stop them manually"
        )
        quiet.show_if_failed()
        return 1

    quiet.capture_print(
        f"✅ Allocated port range: {port_mapping['api']}-{port_mapping['inbucket_pop3']}"
    )

    # Create isolated Supabase instance for this test run
    temp_supabase_dir = None
    try:
        # Create temporary Supabase directory with custom port configuration
        temp_supabase_dir = create_temp_supabase_dir(port_mapping)

        # Define tasks to run in parallel
        def start_supabase_task() -> None:
            """Start Supabase instance."""
            assert temp_supabase_dir is not None
            start_supabase_instance(temp_supabase_dir, quiet_setup=quiet)

        def build_frontend_task() -> None:
            """Build frontend assets."""
            quiet.capture_print("🔨 Building frontend assets...")
            build_result = subprocess.run(
                ["npm", "run", "build"], capture_output=True, text=True, env=env
            )
            if build_result.returncode != 0:
                quiet.fail("Frontend build")
                quiet.capture_print("❌ Frontend build failed")
                quiet.capture_print(f"STDOUT:\n{build_result.stdout}")
                quiet.capture_print(f"STDERR:\n{build_result.stderr}")
                raise RuntimeError("Frontend build failed")
            quiet.capture_print("✅ Frontend build completed successfully")

        # Run Supabase startup and frontend build in parallel
        quiet.capture_print("🚀 Starting Supabase and building frontend in parallel...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            supabase_future = executor.submit(start_supabase_task)
            build_future = executor.submit(build_frontend_task)

            # Wait for both tasks to complete
            wait([supabase_future, build_future])

            # Check for exceptions
            supabase_future.result()  # Raises exception if Supabase failed
            build_future.result()  # Raises exception if build failed

        # Extract environment variables from the isolated instance
        supabase_env = extract_supabase_env(temp_supabase_dir, quiet_setup=quiet)

        # Add Supabase env vars to test environment
        env.update(supabase_env)

        quiet.capture_print("✅ Using isolated Supabase instance")
        quiet.capture_print(f"   API URL: {supabase_env['SUPABASE_URL']}")
        quiet.capture_print(f"   DB URL: {supabase_env['DATABASE_URL']}")

    except Exception as e:
        quiet.fail("Parallel setup")
        quiet.capture_print(f"❌ Failed during parallel setup: {e}")
        quiet.show_if_failed()
        if temp_supabase_dir:
            cleanup_supabase_instance(temp_supabase_dir)
        return 1

    server_process: subprocess.Popen[bytes] | None = None
    try:
        quiet.capture_print("🚀 Starting server processes with concurrently...")

        # Use concurrently to start both server processes with visible output
        # This matches the pattern in package.json but with dynamic port
        if worker_count:
            server_cmd = f"uv run uvicorn main:app --host 0.0.0.0 --port {port} --workers {worker_count}"
            quiet.capture_print(
                f"   Using {worker_count} uvicorn workers to match test parallelism"
            )
        else:
            server_cmd = f"uv run uvicorn main:app --host 0.0.0.0 --port {port}"
        worker_cmd = "uv run python worker.py"

        # Start servers using concurrently and capture output for error detection
        server_process = subprocess.Popen(
            [
                "npx",
                "concurrently",
                "-n",
                "web,worker",
                "--kill-others-on-fail",
                server_cmd,
                worker_cmd,
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Start threads to capture server output
        server_queue = Queue()
        server_stdout_thread = threading.Thread(
            target=stream_reader, args=(server_process.stdout, server_queue, "STDOUT")
        )
        server_stderr_thread = threading.Thread(
            target=stream_reader, args=(server_process.stderr, server_queue, "STDERR")
        )
        server_stdout_thread.daemon = True
        server_stderr_thread.daemon = True
        server_stdout_thread.start()
        server_stderr_thread.start()

        quiet.capture_print("⏳ Waiting for server to be ready...")
        if not wait_for_server(port):
            quiet.fail("Server startup")
            quiet.capture_print("❌ Server failed to start within timeout period")
            quiet.show_if_failed()
            server_process.terminate()
            return 1

        quiet.capture_print("✅ Server is ready!")

        # Setup completed successfully
        print("✅ Ready\n", flush=True)

        # Create timestamp for log files
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")

        # Run e2e tests with provided arguments
        if parallel_args:
            print(
                f"🧪 Running e2e tests in parallel with {' '.join(parallel_args)}: {' '.join(pytest_args)}",
                flush=True,
            )
        else:
            print(
                f"🧪 Running e2e tests sequentially: {' '.join(pytest_args)}",
                flush=True,
            )

        # Save pytest output to temp file
        pytest_log_filename = f"e2e_pytest_{timestamp_str}.txt"
        pytest_log_path = Path(tempfile.gettempdir()) / pytest_log_filename

        test_cmd = ["uv", "run", "pytest", *parallel_args, *pytest_args]

        # Run pytest with streaming output to console and queued for log file
        pytest_process = subprocess.Popen(
            test_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,  # Unbuffered binary I/O for immediate output
        )

        # Start threads to capture pytest output in real-time
        pytest_queue = Queue()
        pytest_stdout_thread = threading.Thread(
            target=stream_reader,
            args=(pytest_process.stdout, pytest_queue, "STDOUT", sys.stdout),
        )
        pytest_stderr_thread = threading.Thread(
            target=stream_reader,
            args=(pytest_process.stderr, pytest_queue, "STDERR", sys.stderr),
        )
        pytest_stdout_thread.daemon = True
        pytest_stderr_thread.daemon = True
        pytest_stdout_thread.start()
        pytest_stderr_thread.start()

        # Wait for pytest to complete
        pytest_stdout_thread.join()
        pytest_stderr_thread.join()
        test_result_returncode = pytest_process.wait()

        # Write queued output to log file with prefixes
        with open(pytest_log_path, "w") as log_file:
            # Write metadata header
            log_file.write(f"E2E Pytest Run - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Command: {' '.join(test_cmd)}\n")
            log_file.write(
                f"Result: {'PASSED' if test_result_returncode == 0 else 'FAILED'}\n"
            )
            log_file.write(f"{'='*80}\n\n")

            # Write all log lines with prefixes
            while not pytest_queue.empty():
                prefix, line = pytest_queue.get()
                log_file.write(f"[{prefix}] {line}\n")

        # Start teardown with quiet mode
        print("\n🧹 Cleaning up...", flush=True)

        # Collect all server logs
        teardown.capture_print("📋 Analyzing server logs for errors...")
        log_lines = []
        while not server_queue.empty():
            log_lines.append(server_queue.get())

        # Read expected errors from file written by tests
        expected_errors = []
        expected_errors_file = Path(tempfile.gettempdir()) / "e2e_expected_errors.txt"
        if expected_errors_file.exists():
            with open(expected_errors_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            error_data = json.loads(line)
                            expected_errors.append(
                                (
                                    error_data["method"],
                                    error_data["path"],
                                    error_data["status"],
                                )
                            )
                        except (json.JSONDecodeError, KeyError):
                            pass  # Skip malformed lines

        # Analyze logs for errors
        errors = analyze_server_logs(log_lines, expected_errors)

        # Save server logs to temp file
        log_filename = f"e2e_server_{timestamp_str}.txt"
        log_file_path = Path(tempfile.gettempdir()) / log_filename

        try:
            with open(log_file_path, "w") as f:
                # Write metadata header
                f.write(f"E2E Test Run - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Port: {port}\n")
                f.write(
                    f"Test Result: {'PASSED' if test_result_returncode == 0 else 'FAILED'}\n"
                )
                f.write(f"{'='*80}\n\n")

                # Write all log lines with prefixes
                for prefix, line in log_lines:
                    f.write(f"[{prefix}] {line}\n")

            # Always show log file paths for debugging (not suppressed)
            print(f"\n📁 Pytest output saved to: {pytest_log_path}", flush=True)
            print(f"📁 Server logs saved to: {log_file_path}", flush=True)
        except Exception as e:
            # Always show warnings and paths (not suppressed)
            print(
                f"\n⚠️  Warning: Failed to save server logs to {log_file_path}: {e}",
                flush=True,
            )
            print(f"📁 Pytest output saved to: {pytest_log_path}", flush=True)

        # Report any server errors found
        has_errors = False
        if errors["http_errors"]:
            has_errors = True
            teardown.capture_print("\n❌ HTTP Error Responses detected in server logs:")
            for error in errors["http_errors"][:10]:  # Show first 10
                teardown.capture_print(f"  • {error}")
            if len(errors["http_errors"]) > 10:
                teardown.capture_print(
                    f"  ... and {len(errors['http_errors']) - 10} more"
                )

        if errors["python_errors"]:
            has_errors = True
            teardown.capture_print(
                "\n❌ Python Errors/Exceptions detected in server logs:"
            )
            for error in errors["python_errors"][:10]:  # Show first 10
                teardown.capture_print(f"  • {error}")
            if len(errors["python_errors"]) > 10:
                teardown.capture_print(
                    f"  ... and {len(errors['python_errors']) - 10} more"
                )

        if errors["stderr_lines"]:
            # Filter out common non-error stderr output
            real_errors = [
                line
                for line in errors["stderr_lines"]
                if not any(
                    ignore in line
                    for ignore in ["DEBUG", "INFO", "Resolved", "Installed"]
                )
            ]
            if real_errors:
                has_errors = True
                teardown.capture_print("\n❌ Stderr output detected from server:")
                for error in real_errors[:10]:  # Show first 10
                    teardown.capture_print(f"  • {error}")
                if len(real_errors) > 10:
                    teardown.capture_print(f"  ... and {len(real_errors) - 10} more")

        if has_errors:
            teardown.fail("Server errors")
            teardown.capture_print("\n❌ Server errors detected - failing test suite")
            teardown.show_if_failed()
            return 1

        if test_result_returncode == 0:
            teardown.capture_print("✅ No server errors detected")

        return test_result_returncode

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running e2e tests: {e}")
        return 1
    finally:
        # Clean up server process (concurrently handles both web and worker)
        teardown.capture_print("🧹 Cleaning up server processes...")
        if server_process is not None:
            try:
                # Terminate concurrently (which will terminate both web and worker)
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    server_process.kill()
                    server_process.wait()
            except Exception as e:
                teardown.capture_print(
                    f"Warning: Failed to clean up server process: {e}"
                )

        # Clean up Supabase instance
        if temp_supabase_dir:
            cleanup_supabase_instance(temp_supabase_dir, quiet_setup=teardown)

        # Show teardown output only if there were errors, otherwise just show success
        if not teardown.show_if_failed():
            print("✅ Done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
