#!/usr/bin/env python3
"""
Configuration Management Script for Drawing Machine
Validates and manages all configuration files
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


class ConfigurationManager:
    """Manages and validates drawing machine configurations"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.path.dirname(__file__))
        self.environments = ["development", "staging", "production"]

    def validate_all_configs(self) -> Dict[str, bool]:
        """Validate all configuration files"""
        results = {}

        # Use Windows-safe characters instead of emojis
        print("Drawing Machine Configuration Validation")
        print("==================================================")

        # Validate YAML files
        yaml_files = [
            "shared/motor/motor_mappings.yaml",
            "shared/blockchain/api_endpoints.yaml",
            "shared/blockchain/service_apis.yaml",
            "shared/logging/logging_config.yaml",
            "shared/monitoring/prometheus_config.yaml",
            "shared/monitoring/alert_rules.yaml",
            "shared/security/security_config.yaml",
        ]

        for yaml_file in yaml_files:
            try:
                result = self._validate_yaml_file(yaml_file)
                results[yaml_file] = result
                status = "Valid YAML" if result else "Invalid YAML"
                print(f"[OK] {yaml_file}: {status}")
            except Exception as e:
                results[yaml_file] = False
                print(f"[ERROR] {yaml_file}: {str(e)}")

        # Validate environment files
        env_files = [
            "development/.env.development",
            "staging/.env.staging",
            "production/.env.production.template",
        ]

        for env_file in env_files:
            try:
                result = self._validate_env_file(env_file)
                results[env_file] = result
                status = (
                    "Valid environment file" if result else "Invalid environment file"
                )
                print(f"[OK] {env_file}: {status}")
            except Exception as e:
                results[env_file] = False
                print(f"[ERROR] {env_file}: {str(e)}")

        # Print summary
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        failed = total - passed

        print("Validation Summary:")
        print("------------------------------")
        print(f"[OK] Passed: {passed}/{total}")
        print(f"[FAIL] Failed: {failed}/{total}")

        if failed == 0:
            print("All configurations are valid!")
            return True
        else:
            print("Some configurations have errors!")
            return False

    def _validate_yaml_file(self, file_path: str) -> bool:
        """Validate a YAML file"""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}")

    def _validate_env_file(self, file_path: str) -> bool:
        """Validate an environment file"""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" not in line:
                        raise ValueError(f"Line {line_num}: Invalid format (missing =)")

            return True
        except Exception as e:
            raise ValueError(f"Environment file validation error: {e}")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        config_manager = ConfigurationManager()
        success = config_manager.validate_all_configs()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python config_manager.py validate")
        sys.exit(1)


if __name__ == "__main__":
    main()
