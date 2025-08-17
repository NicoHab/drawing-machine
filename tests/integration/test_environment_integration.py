# tests/integration/test_environment_integration.py
"""
Comprehensive integration test for Drawing Machine development environment.
Tests all services, configurations, and dependencies.
"""
import asyncio
import json
import socket
import subprocess
import time
from pathlib import Path
import requests
import yaml
import psycopg2
import redis
from typing import Dict, List, Tuple


class EnvironmentValidator:
    def __init__(self):
        self.results = {}
        self.project_root = Path(__file__).parent.parent.parent

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result with status and details."""
        self.results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": time.time(),
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   📄 Details: {details}")

    def test_docker_services(self) -> bool:
        """Test all Docker services are running."""
        try:
            # Get actual container names
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
                shell=True,
            )

            # Use the actual container names from docker ps output
            required_services = [
                "drawing_dev_postgres",
                "drawing_redis",
                "drawing_prometheus",
                "drawing_grafana",
            ]

            running_services = result.stdout
            missing_services = []
            found_services = []

            for service in required_services:
                if service in running_services:
                    found_services.append(service)
                else:
                    missing_services.append(service)

            if missing_services:
                self.log_test(
                    "Docker Services",
                    "FAIL",
                    f"Missing services: {', '.join(missing_services)}",
                )
                return False

            self.log_test(
                "Docker Services",
                "PASS",
                f"All 4 services running: {', '.join(found_services)}",
            )
            return True

        except Exception as e:
            self.log_test("Docker Services", "FAIL", str(e))
            return False

    def test_database_connectivity(self) -> bool:
        """Test PostgreSQL database connectivity."""
        try:
            # Test development database
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="drawing_machine_dev",
                user="dev_user",
                password="dev_password",
            )

            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.log_test(
                "PostgreSQL Connectivity", "PASS", f"Connected: {version[:50]}..."
            )
            return True

        except Exception as e:
            self.log_test("PostgreSQL Connectivity", "FAIL", str(e))
            return False

    def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity."""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            info = r.info("server")

            self.log_test(
                "Redis Connectivity",
                "PASS",
                f"Redis {info['redis_version']} responding",
            )
            return True

        except Exception as e:
            self.log_test("Redis Connectivity", "FAIL", str(e))
            return False

    def test_tcp_motor_controller(self) -> bool:
        """Test TCP motor controller simulation."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("localhost", 8765))

            if result == 0:
                # Send test command
                test_command = {
                    "timestamp": time.time(),
                    "epoch": 1,
                    "duration": 3.4,
                    "motors": {
                        "canvas": {"rpm": 10.0, "dir": "CW"},
                        "pb": {"rpm": 15.0, "dir": "CW"},
                        "pcd": {"rpm": 12.0, "dir": "CCW"},
                        "pe": {"rpm": 18.0, "dir": "CW"},
                    },
                }

                message = json.dumps(test_command) + "\n"
                sock.sendall(message.encode())

                response = sock.recv(1024).decode().strip()
                sock.close()

                if "ACK" in response:
                    self.log_test(
                        "TCP Motor Controller",
                        "PASS",
                        f"Responded with: {response[:50]}...",
                    )
                    return True
                else:
                    self.log_test(
                        "TCP Motor Controller",
                        "FAIL",
                        f"Unexpected response: {response}",
                    )
                    return False
            else:
                self.log_test(
                    "TCP Motor Controller",
                    "FAIL",
                    "Connection refused on localhost:8765",
                )
                return False

        except Exception as e:
            self.log_test("TCP Motor Controller", "FAIL", str(e))
            return False

    def test_monitoring_services(self) -> bool:
        """Test Prometheus and Grafana accessibility."""
        services = [
            ("Prometheus", "http://localhost:9090/api/v1/status/config"),
            ("Grafana", "http://localhost:3000/api/health"),
        ]

        all_passed = True

        for service_name, url in services:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_test(
                        f"{service_name} API", "PASS", f"Status: {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"{service_name} API", "FAIL", f"Status: {response.status_code}"
                    )
                    all_passed = False
            except Exception as e:
                self.log_test(f"{service_name} API", "FAIL", str(e))
                all_passed = False

        return all_passed

    def test_configuration_files(self) -> bool:
        """Test all configuration files are valid."""
        config_files = [
            "config/shared/motor/motor_mappings.yaml",
            "config/shared/blockchain/api_endpoints.yaml",
            "config/shared/blockchain/service_apis.yaml",
            "config/shared/logging/logging_config.yaml",
            "config/shared/monitoring/prometheus_config.yaml",
            "config/shared/security/security_config.yaml",
        ]

        all_valid = True

        for config_file in config_files:
            file_path = self.project_root / config_file
            try:
                with open(file_path, "r") as f:
                    yaml.safe_load(f)
                self.log_test(f"Config: {Path(config_file).name}", "PASS")
            except Exception as e:
                self.log_test(f"Config: {Path(config_file).name}", "FAIL", str(e))
                all_valid = False

        return all_valid

    def test_python_environment(self) -> bool:
        """Test Python environment and dependencies."""
        try:
            import fastapi
            import uvicorn
            import sqlalchemy
            import pydantic
            import aiohttp
            import prometheus_client

            # Some packages might not have __version__, so handle gracefully
            def get_version(module):
                return getattr(module, "__version__", "installed")

            dependencies = {
                "FastAPI": get_version(fastapi),
                "Uvicorn": get_version(uvicorn),
                "SQLAlchemy": get_version(sqlalchemy),
                "Pydantic": get_version(pydantic),
                "Prometheus Client": get_version(prometheus_client),
            }

            self.log_test(
                "Python Dependencies",
                "PASS",
                f"All key packages available: {', '.join(dependencies.keys())}",
            )
            return True

        except ImportError as e:
            self.log_test("Python Dependencies", "FAIL", f"Missing package: {str(e)}")
            return False
        except Exception as e:
            self.log_test("Python Dependencies", "FAIL", f"Error: {str(e)}")
            return False

    def test_nodejs_environment(self) -> bool:
        """Test Node.js and Vue.js environment."""
        try:
            # Check Node.js version
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                check=True,
                shell=True,
            )
            node_version = node_result.stdout.strip()

            # Check if Vue.js project exists and can build
            frontend_path = self.project_root / "frontend"
            if frontend_path.exists():
                # Check package.json exists
                package_json = frontend_path / "package.json"
                if package_json.exists():
                    self.log_test(
                        "Node.js Environment",
                        "PASS",
                        f"Node {node_version}, Vue.js project ready",
                    )
                    return True
                else:
                    self.log_test(
                        "Node.js Environment",
                        "FAIL",
                        "package.json not found in frontend/",
                    )
                    return False
            else:
                self.log_test(
                    "Node.js Environment", "FAIL", "frontend/ directory not found"
                )
                return False

        except Exception as e:
            self.log_test("Node.js Environment", "FAIL", str(e))
            return False

    def test_vscode_workspace(self) -> bool:
        """Test VS Code workspace configuration."""
        workspace_file = self.project_root / "drawing-machine.code-workspace"
        vscode_dir = self.project_root / ".vscode"

        if not workspace_file.exists():
            self.log_test("VS Code Workspace", "FAIL", "Workspace file missing")
            return False

        if not vscode_dir.exists():
            self.log_test("VS Code Workspace", "FAIL", ".vscode directory missing")
            return False

        required_files = ["settings.json", "launch.json", "tasks.json"]
        for file_name in required_files:
            if not (vscode_dir / file_name).exists():
                self.log_test("VS Code Workspace", "FAIL", f"{file_name} missing")
                return False

        self.log_test("VS Code Workspace", "PASS", "All configuration files present")
        return True

    async def run_all_tests(self) -> Dict:
        """Run all validation tests."""
        print("🚀 Starting Drawing Machine Environment Final Validation")
        print("=" * 70)

        tests = [
            ("Docker Services", self.test_docker_services),
            ("Database Connectivity", self.test_database_connectivity),
            ("Redis Connectivity", self.test_redis_connectivity),
            ("TCP Motor Controller", self.test_tcp_motor_controller),
            ("Monitoring Services", self.test_monitoring_services),
            ("Configuration Files", self.test_configuration_files),
            ("Python Environment", self.test_python_environment),
            ("Node.js Environment", self.test_nodejs_environment),
            ("VS Code Workspace", self.test_vscode_workspace),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Exception: {str(e)}")

        print("\n" + "=" * 70)
        print(f"🎯 FINAL VALIDATION RESULTS: {passed}/{total} TESTS PASSED")

        if passed == total:
            print("🎉 ENVIRONMENT VALIDATION: ALL TESTS PASSED")
            print("✅ Development environment is READY FOR IMPLEMENTATION!")
        else:
            print("⚠️  ENVIRONMENT VALIDATION: SOME TESTS FAILED")
            print("❌ Please resolve failing tests before implementation")

        return {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total) * 100,
            "ready_for_implementation": passed == total,
            "detailed_results": self.results,
        }


async def main():
    validator = EnvironmentValidator()
    results = await validator.run_all_tests()
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    print(f"\nValidation complete. Success rate: {results['success_rate']:.1f}%")
