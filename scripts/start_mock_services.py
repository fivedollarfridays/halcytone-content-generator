#!/usr/bin/env python3
"""
Start Mock Services for Halcytone Content Generator
Cross-platform Python script to start and manage mock services
"""

import os
import sys
import time
import subprocess
import requests
import signal
from pathlib import Path
from typing import Optional, Tuple


class MockServiceManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.compose_file = self.project_root / "docker-compose.mocks.yml"
        self.timeout = 30
        self.compose_cmd = self._detect_compose_command()

    def _detect_compose_command(self) -> str:
        """Detect available docker-compose command"""
        try:
            subprocess.run(["docker-compose", "--version"],
                         check=True, capture_output=True)
            return "docker-compose"
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["docker", "compose", "version"],
                             check=True, capture_output=True)
                return "docker compose"
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("Neither 'docker-compose' nor 'docker compose' is available")

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def _error(self, message: str):
        self._log(message, "ERROR")

    def _success(self, message: str):
        self._log(message, "SUCCESS")

    def _warning(self, message: str):
        self._log(message, "WARNING")

    def check_docker(self) -> bool:
        """Check if Docker is running"""
        try:
            subprocess.run(["docker", "info"],
                         check=True, capture_output=True)
            self._log("Docker is running ✓")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._error("Docker is not running. Please start Docker and try again.")
            return False

    def check_service_health(self, port: int) -> bool:
        """Check if service on given port is healthy"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def are_services_running(self) -> Tuple[bool, bool]:
        """Check if mock services are running"""
        crm_running = self.check_service_health(8001)
        platform_running = self.check_service_health(8002)
        return crm_running, platform_running

    def stop_services(self) -> bool:
        """Stop existing mock services"""
        self._log("Stopping any existing mock services...")
        try:
            # Stop containers gracefully
            cmd = self.compose_cmd.split() + ["-f", str(self.compose_file),
                                              "down", "--remove-orphans"]
            subprocess.run(cmd, check=False, capture_output=True, cwd=self.project_root)

            # Kill any processes on ports (cross-platform approach)
            self._kill_process_on_port(8001)
            self._kill_process_on_port(8002)

            time.sleep(2)
            self._log("Cleanup completed")
            return True
        except Exception as e:
            self._error(f"Failed to stop services: {e}")
            return False

    def _kill_process_on_port(self, port: int):
        """Kill process on specific port (cross-platform)"""
        try:
            if sys.platform == "win32":
                # Windows
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True, check=False
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            self._warning(f"Killing process {pid} on port {port}...")
                            subprocess.run(["taskkill", "/pid", pid, "/f"],
                                         check=False, capture_output=True)
            else:
                # Unix-like systems
                try:
                    result = subprocess.run(
                        ["lsof", "-ti", f":{port}"],
                        capture_output=True, text=True, check=False
                    )
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid:
                                self._warning(f"Killing process {pid} on port {port}...")
                                os.kill(int(pid), signal.SIGTERM)
                except (ValueError, OSError, FileNotFoundError):
                    pass
        except Exception as e:
            self._warning(f"Failed to kill process on port {port}: {e}")

    def build_and_start_services(self) -> bool:
        """Build and start mock services"""
        self._log("Building and starting mock services...")

        try:
            os.chdir(self.project_root)

            # Build images
            self._log("Building Docker images...")
            build_cmd = self.compose_cmd.split() + ["-f", str(self.compose_file),
                                                   "build", "--no-cache"]
            result = subprocess.run(build_cmd, check=True, capture_output=True)

            # Start services
            self._log("Starting services...")
            start_cmd = self.compose_cmd.split() + ["-f", str(self.compose_file), "up", "-d"]
            result = subprocess.run(start_cmd, check=True, capture_output=True)

            self._log("Services started in background")
            return True
        except subprocess.CalledProcessError as e:
            self._error(f"Failed to start services: {e}")
            return False

    def wait_for_services(self) -> bool:
        """Wait for services to become healthy"""
        self._log("Waiting for services to become healthy...")

        max_attempts = self.timeout // 2
        for attempt in range(max_attempts):
            crm_healthy = self.check_service_health(8001)
            platform_healthy = self.check_service_health(8002)

            if crm_healthy and platform_healthy:
                print()  # New line after dots
                self._success("All services are healthy!")
                return True

            print(".", end="", flush=True)
            time.sleep(2)

        print()  # New line after dots
        self._error(f"Services failed to become healthy within {self.timeout} seconds")

        # Show logs for debugging
        try:
            logs_cmd = self.compose_cmd.split() + ["-f", str(self.compose_file),
                                                  "logs", "--tail=20"]
            subprocess.run(logs_cmd, cwd=self.project_root)
        except subprocess.CalledProcessError:
            pass

        return False

    def test_services(self) -> bool:
        """Test services with sample requests"""
        self._log("Testing services with sample requests...")

        # Test CRM service
        try:
            response = requests.get("http://localhost:8001/contacts", timeout=10)
            if response.status_code == 200:
                self._success("CRM service responding ✓")
            else:
                self._error(f"CRM service returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self._error(f"CRM service test failed: {e}")
            return False

        # Test Platform service
        try:
            response = requests.get("http://localhost:8002/content", timeout=10)
            if response.status_code == 200:
                self._success("Platform service responding ✓")
            else:
                self._error(f"Platform service returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self._error(f"Platform service test failed: {e}")
            return False

        self._success("All services tested successfully!")
        return True

    def show_service_info(self):
        """Display service information"""
        self._log("Mock Services Information:")
        print()
        print("🔧 CRM Service:")
        print("   - Health: http://localhost:8001/health")
        print("   - API Docs: http://localhost:8001/docs")
        print("   - OpenAPI: http://localhost:8001/openapi.json")
        print()
        print("🌐 Platform Service:")
        print("   - Health: http://localhost:8002/health")
        print("   - API Docs: http://localhost:8002/docs")
        print("   - OpenAPI: http://localhost:8002/openapi.json")
        print()
        print("📊 Service Status:")
        try:
            status_cmd = self.compose_cmd.split() + ["-f", str(self.compose_file), "ps"]
            subprocess.run(status_cmd, cwd=self.project_root, check=False)
        except subprocess.CalledProcessError:
            pass
        print()
        print(f"📝 View logs: {self.compose_cmd} -f docker-compose.mocks.yml logs -f")
        print(f"🛑 Stop services: {self.compose_cmd} -f docker-compose.mocks.yml down")

    def start(self, force: bool = False) -> bool:
        """Main method to start mock services"""
        self._log("Starting Halcytone Mock Services...")

        # Check Docker
        if not self.check_docker():
            return False

        self._log(f"Docker Compose available: {self.compose_cmd} ✓")

        # Check if services are already running
        crm_running, platform_running = self.are_services_running()

        if crm_running and platform_running:
            self._success("Mock services are already running!")
            self._log("CRM Service: http://localhost:8001/docs")
            self._log("Platform Service: http://localhost:8002/docs")
            if not force:
                return True
            self._log("Force restart requested...")

        # Stop existing services
        if not self.stop_services():
            return False

        # Build and start services
        if not self.build_and_start_services():
            return False

        # Wait for services to be healthy
        if not self.wait_for_services():
            return False

        # Test services
        if not self.test_services():
            return False

        # Show service information
        self.show_service_info()

        self._success("Mock services are ready! 🚀")
        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Start Halcytone Mock Services for development and testing"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force restart even if services are running"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output (for use in pytest fixtures)"
    )

    args = parser.parse_args()

    manager = MockServiceManager()

    if args.quiet:
        # Redirect stdout to minimize noise during testing
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            success = manager.start(force=args.force)
        finally:
            sys.stdout = old_stdout

        if success:
            print("Mock services started successfully")
        else:
            print("Failed to start mock services", file=sys.stderr)
            sys.exit(1)
    else:
        success = manager.start(force=args.force)
        if not success:
            sys.exit(1)


# Function for programmatic use (e.g., from pytest fixtures)
def ensure_mock_services_running(force: bool = False, quiet: bool = True) -> bool:
    """
    Ensure mock services are running. Suitable for use in test fixtures.

    Args:
        force: Force restart even if services are running
        quiet: Minimize output

    Returns:
        True if services are running successfully, False otherwise
    """
    manager = MockServiceManager()

    if quiet:
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            return manager.start(force=force)
        finally:
            sys.stdout = old_stdout
    else:
        return manager.start(force=force)


if __name__ == "__main__":
    main()