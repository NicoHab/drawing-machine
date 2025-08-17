#!/usr/bin/env python3
"""
Development Environment Test Script
Tests all components of the drawing machine development environment.
"""

import json
import socket
import time

import psycopg2
import redis
import requests


class DevEnvironmentTester:
    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []

    def log_test(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.results.append((test_name, success, message))

    def test_docker_containers(self) -> bool:
        """Test that all expected Docker containers are running"""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"],
                capture_output=True,
                text=True,
                check=True,
            )

            expected_containers = [
                "drawing_prometheus",
                "drawing_grafana",
                "drawing_dev_postgres",
                "drawing_redis",
            ]

            running_containers = result.stdout
            missing = []

            for container in expected_containers:
                if container not in running_containers:
                    missing.append(container)

            if missing:
                self.log_test(
                    "Docker Containers", False, f"Missing containers: {missing}"
                )
                return False
            else:
                self.log_test(
                    "Docker Containers", True, "All expected containers running"
                )
                return True

        except Exception as e:
            self.log_test("Docker Containers", False, f"Error checking containers: {e}")
            return False

    def test_postgres_connectivity(self) -> bool:
        """Test PostgreSQL development database connectivity"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5433",
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
                "PostgreSQL Dev DB", True, f"Connected successfully - {version[:50]}..."
            )
            return True

        except Exception as e:
            self.log_test("PostgreSQL Dev DB", False, f"Connection failed: {e}")
            return False

    def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity"""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)

            # Test ping
            pong = r.ping()
            if not pong:
                raise Exception("Redis ping failed")

            # Test set/get
            test_key = "dev_test_key"
            test_value = "development_environment_test"
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved = r.get(test_key)

            if retrieved != test_value:
                raise Exception("Redis set/get test failed")

            # Clean up
            r.delete(test_key)

            self.log_test("Redis", True, "Connected and tested successfully")
            return True

        except Exception as e:
            self.log_test("Redis", False, f"Connection/test failed: {e}")
            return False

    def test_tcp_motor_controller(self) -> bool:
        """Test TCP motor controller connectivity"""
        try:
            # Test if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(("localhost", 8765))
            sock.close()

            if result != 0:
                self.log_test("TCP Motor Controller", False, "Port 8765 not accessible")
                return False

            # Test actual communication
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("localhost", 8765))

            # Send test command
            test_command = {
                "timestamp": time.time(),
                "epoch": 1,
                "duration": 3.4,
                "motors": {
                    "canvas": {"rpm": 10.0, "dir": "CW"},
                    "pb": {"rpm": 15.0, "dir": "CCW"},
                    "pcd": {"rpm": 12.0, "dir": "CW"},
                    "pe": {"rpm": 18.0, "dir": "CW"},
                },
            }

            message = json.dumps(test_command) + "\n"
            sock.send(message.encode())

            # Wait for response
            response = sock.recv(1024).decode().strip()
            sock.close()

            if "ACK" in response:
                self.log_test("TCP Motor Controller", True, "Communication successful")
                return True
            else:
                self.log_test(
                    "TCP Motor Controller", False, f"Unexpected response: {response}"
                )
                return False

        except Exception as e:
            self.log_test("TCP Motor Controller", False, f"Communication failed: {e}")
            return False

    def test_monitoring_services(self) -> bool:
        """Test Prometheus and Grafana accessibility"""
        success = True

        # Test Prometheus
        try:
            response = requests.get("http://localhost:9090/-/healthy", timeout=10)
            if response.status_code == 200:
                self.log_test("Prometheus", True, "Health check passed")
            else:
                self.log_test(
                    "Prometheus", False, f"Health check failed: {response.status_code}"
                )
                success = False
        except Exception as e:
            self.log_test("Prometheus", False, f"Connection failed: {e}")
            success = False

        # Test Grafana
        try:
            response = requests.get("http://localhost:3000/api/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Grafana", True, "Health check passed")
            else:
                self.log_test(
                    "Grafana", False, f"Health check failed: {response.status_code}"
                )
                success = False
        except Exception as e:
            self.log_test("Grafana", False, f"Connection failed: {e}")
            success = False

        return success

    def test_network_connectivity(self) -> bool:
        """Test Docker network connectivity"""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "network", "inspect", "drawing-machine_default"],
                capture_output=True,
                text=True,
                check=True,
            )

            if "drawing-machine_default" in result.stdout:
                self.log_test(
                    "Docker Network", True, "drawing-machine_default network exists"
                )
                return True
            else:
                self.log_test(
                    "Docker Network", False, "drawing-machine_default network not found"
                )
                return False

        except Exception as e:
            self.log_test("Docker Network", False, f"Network check failed: {e}")
            return False

    def run_all_tests(self) -> dict[str, any]:
        """Run all tests and return summary"""
        print("🚀 Starting Development Environment Tests...\n")

        # Run all tests
        tests = [
            self.test_docker_containers,
            self.test_postgres_connectivity,
            self.test_redis_connectivity,
            self.test_tcp_motor_controller,
            self.test_monitoring_services,
            self.test_network_connectivity,
        ]

        for test in tests:
            test()
            print()  # Add spacing between tests

        # Summary
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        success_rate = (passed / total) * 100

        print("=" * 50)
        print("📊 TEST SUMMARY")
        print(f"Passed: {passed}/{total} ({success_rate:.1f}%)")
        print("=" * 50)

        if passed == total:
            print("🎉 ALL TESTS PASSED! Development environment is ready!")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")

        return {
            "total_tests": total,
            "passed": passed,
            "success_rate": success_rate,
            "all_passed": passed == total,
            "results": self.results,
        }


if __name__ == "__main__":
    tester = DevEnvironmentTester()
    summary = tester.run_all_tests()

    # Exit with error code if tests failed
    exit(0 if summary["all_passed"] else 1)

