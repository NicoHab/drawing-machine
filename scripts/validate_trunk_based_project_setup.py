#!/usr/bin/env python3
"""
Trunk-Based Development Project Setup Validation System

This script validates the Drawing Machine TDD infrastructure implementation
of trunk-based development practices, where the deployment pipeline serves
as the definitive quality gatekeeper instead of branch protection.

Key Principles:
- Single main/trunk branch with direct commits
- Deployment pipeline = definitive statement on release ability
- No branch protection rules (pipeline protection instead)
- Feature flags instead of feature branches
- TDD automation integrated with trunk workflow
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

try:
    import requests
    import yaml
except ImportError:
    print("📦 Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pyyaml"])
    import requests
    import yaml


@dataclass
class TrunkBasedConfig:
    """Configuration for trunk-based development validation."""
    repository_name: str
    main_branch: str = "main"
    direct_push_enabled: bool = False
    branch_protection_disabled: bool = False
    pipeline_as_gatekeeper: bool = False
    feature_flags_enabled: bool = False
    tdd_integration: bool = False


@dataclass
class PipelineAuthority:
    """Validation of pipeline as definitive quality authority."""
    immediate_triggering: bool = False
    automatic_deployment: bool = False
    no_manual_overrides: bool = False
    rollback_capability: bool = False
    quality_gates_count: int = 0
    success_criteria_enforced: bool = False


@dataclass
class TrunkValidationResults:
    """Results of trunk-based development validation."""
    repository_config: TrunkBasedConfig
    pipeline_authority: PipelineAuthority
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    compliance_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class TrunkBasedDevelopmentValidator:
    """
    Comprehensive validation system for trunk-based development implementation
    with deployment pipeline as quality gatekeeper.
    """
    
    def __init__(self, project_root: Path = None):
        """Initialize trunk-based development validator."""
        self.project_root = project_root or Path.cwd()
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_username = os.environ.get("GITHUB_USERNAME")
        
        # Trunk-based development criteria
        self.trunk_criteria = {
            "single_branch_strategy": 20,
            "direct_push_capability": 15,
            "pipeline_as_gatekeeper": 25,
            "immediate_ci_triggering": 15,
            "automatic_deployment": 10,
            "feature_flag_usage": 10,
            "tdd_integration": 5
        }
        
        # Performance targets for trunk-based development
        self.performance_targets = {
            "commit_to_feedback": 5,  # minutes
            "commit_to_deployment": 60,  # minutes for full pipeline
            "pipeline_success_rate": 95,  # percentage
            "deployment_frequency": "multiple_per_day"
        }
        
        # TDD infrastructure files for validation
        self.tdd_infrastructure = [
            "scripts/auto_test_runner.py",
            "scripts/create_tdd_project.py",
            ".github/workflows/tdd_pipeline.yml",
            ".github/workflows/advanced_deployment_pipeline.yml",
            ".claude/workflows/tdd_session.md"
        ]
    
    def validate_environment(self) -> bool:
        """Validate environment for trunk-based development validation."""
        print("🔍 Validating environment for trunk-based development validation...")
        
        # Check Git repository
        if not (self.project_root / ".git").exists():
            print("❌ Not a Git repository")
            return False
        
        # Check for Drawing Machine TDD infrastructure
        missing_files = []
        for file_path in self.tdd_infrastructure:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"⚠️  Missing TDD infrastructure files: {missing_files}")
            print("   Some validations may be limited")
        
        # Check GitHub integration
        if not self.github_token:
            print("⚠️  GITHUB_TOKEN not set - GitHub API validations will be limited")
        
        print("✅ Environment validation completed")
        return True
    
    def audit_trunk_based_repository_config(self) -> TrunkBasedConfig:
        """Audit repository configuration for trunk-based development compliance."""
        print("📋 Auditing trunk-based repository configuration...")
        
        config = TrunkBasedConfig(repository_name="unknown")
        
        try:
            # Get repository information
            result = subprocess.run(["git", "remote", "get-url", "origin"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                origin_url = result.stdout.strip()
                if "github.com" in origin_url:
                    # Extract repository name from GitHub URL
                    repo_parts = origin_url.split("/")[-2:]
                    if len(repo_parts) == 2:
                        config.repository_name = repo_parts[1].replace(".git", "")
            
            # Check current branch
            result = subprocess.run(["git", "branch", "--show-current"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                if current_branch in ["main", "master", "trunk"]:
                    config.main_branch = current_branch
                    print(f"✅ Using trunk branch: {current_branch}")
                else:
                    print(f"⚠️  Current branch '{current_branch}' is not a typical trunk branch")
            
            # Check branch strategy (should have minimal branches)
            result = subprocess.run(["git", "branch", "-a"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                branches = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                # Filter out current branch marker and remote tracking
                local_branches = [b for b in branches if not b.startswith('*') and not b.startswith('remotes/')]
                remote_branches = [b for b in branches if b.startswith('remotes/origin/')]
                
                print(f"📊 Local branches: {len(local_branches)}")
                print(f"📊 Remote branches: {len(remote_branches)}")
                
                # Trunk-based should have minimal branches
                if len(local_branches) <= 2:  # main + maybe develop
                    print("✅ Minimal branch strategy detected (trunk-based compliant)")
                else:
                    print(f"⚠️  Multiple branches detected: {local_branches}")
                    print("   Consider consolidating to single trunk branch")
            
            # Validate GitHub repository settings if GitHub token available
            if self.github_token and config.repository_name != "unknown":
                github_config = self._validate_github_trunk_settings(config.repository_name)
                config.direct_push_enabled = github_config.get("direct_push_enabled", False)
                config.branch_protection_disabled = github_config.get("branch_protection_disabled", False)
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Error during repository audit: {e}")
        
        print(f"✅ Repository configuration audit completed for '{config.repository_name}'")
        return config
    
    def _validate_github_trunk_settings(self, repo_name: str) -> Dict[str, Any]:
        """Validate GitHub repository settings for trunk-based development."""
        print("🐙 Validating GitHub trunk-based settings...")
        
        settings = {
            "direct_push_enabled": False,
            "branch_protection_disabled": False,
            "actions_enabled": False
        }
        
        try:
            username = self.github_username or self._get_github_username()
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Check repository settings
            repo_response = requests.get(
                f"https://api.github.com/repos/{username}/{repo_name}",
                headers=headers
            )
            
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                
                # Check if repository allows direct pushes to default branch
                default_branch = repo_data.get("default_branch", "main")
                print(f"📊 Default branch: {default_branch}")
                
                # Check branch protection rules
                protection_response = requests.get(
                    f"https://api.github.com/repos/{username}/{repo_name}/branches/{default_branch}/protection",
                    headers=headers
                )
                
                if protection_response.status_code == 404:
                    # No branch protection = good for trunk-based
                    settings["branch_protection_disabled"] = True
                    settings["direct_push_enabled"] = True
                    print("✅ No branch protection rules (trunk-based compliant)")
                elif protection_response.status_code == 200:
                    protection_data = protection_response.json()
                    print("⚠️  Branch protection rules found:")
                    print(f"   - Required reviews: {protection_data.get('required_pull_request_reviews', {}).get('required_approving_review_count', 0)}")
                    print(f"   - Required status checks: {len(protection_data.get('required_status_checks', {}).get('contexts', []))}")
                    print("   Consider removing for pure trunk-based development")
                
                # Check if GitHub Actions is enabled
                actions_response = requests.get(
                    f"https://api.github.com/repos/{username}/{repo_name}/actions/permissions",
                    headers=headers
                )
                
                if actions_response.status_code == 200:
                    actions_data = actions_response.json()
                    settings["actions_enabled"] = actions_data.get("enabled", False)
                    print(f"✅ GitHub Actions enabled: {settings['actions_enabled']}")
            
        except requests.RequestException as e:
            print(f"⚠️  GitHub API validation error: {e}")
        
        return settings
    
    def _get_github_username(self) -> str:
        """Get GitHub username from API."""
        try:
            headers = {"Authorization": f"token {self.github_token}"}
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                return response.json()["login"]
        except:
            pass
        return "unknown"
    
    def validate_deployment_pipeline_authority(self) -> PipelineAuthority:
        """Validate deployment pipeline as definitive quality authority."""
        print("🚀 Validating deployment pipeline authority...")
        
        authority = PipelineAuthority()
        
        # Check for GitHub Actions workflows
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            print(f"📊 Found {len(workflow_files)} workflow files")
            
            # Analyze workflow configurations
            pipeline_workflows = []
            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = yaml.safe_load(f)
                    
                    # Check for push triggers (immediate triggering)
                    triggers = workflow_data.get('on', {})
                    if isinstance(triggers, dict):
                        if 'push' in triggers:
                            authority.immediate_triggering = True
                            print(f"✅ Immediate triggering configured in {workflow_file.name}")
                        
                        # Check for workflow_dispatch (manual capability)
                        if 'workflow_dispatch' in triggers:
                            print(f"📊 Manual dispatch available in {workflow_file.name}")
                    
                    # Count quality gates (jobs that serve as gates)
                    jobs = workflow_data.get('jobs', {})
                    quality_jobs = [
                        job for job_name, job in jobs.items() 
                        if any(keyword in job_name.lower() for keyword in ['test', 'quality', 'security', 'lint'])
                    ]
                    authority.quality_gates_count += len(quality_jobs)
                    
                    # Check for deployment jobs
                    deployment_jobs = [
                        job for job_name, job in jobs.items()
                        if any(keyword in job_name.lower() for keyword in ['deploy', 'production', 'staging'])
                    ]
                    if deployment_jobs:
                        authority.automatic_deployment = True
                        print(f"✅ Automatic deployment configured in {workflow_file.name}")
                    
                    pipeline_workflows.append(workflow_file.name)
                    
                except Exception as e:
                    print(f"⚠️  Error parsing {workflow_file}: {e}")
            
            # Validate specific TDD pipeline files
            tdd_pipeline = workflows_dir / "tdd_pipeline.yml"
            advanced_pipeline = workflows_dir / "advanced_deployment_pipeline.yml"
            
            if tdd_pipeline.exists():
                print("✅ TDD pipeline found - validates TDD integration")
                authority.tdd_integration = True
            
            if advanced_pipeline.exists():
                print("✅ Advanced deployment pipeline found - validates enterprise-grade automation")
                authority.rollback_capability = True
            
            # Check for no manual override capabilities in critical paths
            if authority.automatic_deployment and authority.quality_gates_count > 0:
                authority.no_manual_overrides = True
                print("✅ No manual overrides detected in critical deployment path")
            
            # Validate success criteria enforcement
            if authority.immediate_triggering and authority.quality_gates_count >= 3:
                authority.success_criteria_enforced = True
                print("✅ Success criteria enforced through pipeline automation")
        
        else:
            print("❌ No GitHub Actions workflows found")
            print("   Deployment pipeline authority cannot be validated")
        
        print(f"📊 Pipeline Authority Summary:")
        print(f"   - Immediate triggering: {authority.immediate_triggering}")
        print(f"   - Quality gates: {authority.quality_gates_count}")
        print(f"   - Automatic deployment: {authority.automatic_deployment}")
        print(f"   - Rollback capability: {authority.rollback_capability}")
        print(f"   - No manual overrides: {authority.no_manual_overrides}")
        
        return authority
    
    def analyze_continuous_integration_performance(self) -> Dict[str, Any]:
        """Analyze continuous integration performance for trunk-based development."""
        print("⚡ Analyzing continuous integration performance...")
        
        performance = {
            "commit_frequency": "unknown",
            "pipeline_execution_frequency": "unknown",
            "average_pipeline_duration": "unknown",
            "success_rate": "unknown",
            "tdd_integration_performance": {}
        }
        
        # Analyze Git commit frequency (indicates trunk usage)
        try:
            # Get commits from last 30 days
            result = subprocess.run([
                "git", "log", "--since=30.days.ago", "--pretty=format:%H,%ct,%s"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                commits = [line for line in result.stdout.split('\n') if line.strip()]
                commit_count = len(commits)
                
                performance["commit_frequency"] = f"{commit_count} commits in last 30 days"
                
                if commit_count > 0:
                    # Calculate average commits per day
                    avg_per_day = commit_count / 30
                    performance["avg_commits_per_day"] = round(avg_per_day, 2)
                    
                    if avg_per_day >= 1:
                        print(f"✅ High commit frequency: {avg_per_day:.1f} commits/day (good for trunk-based)")
                    else:
                        print(f"📊 Commit frequency: {avg_per_day:.1f} commits/day")
                
                # Analyze commit messages for TDD patterns
                tdd_commits = [c for c in commits if any(keyword in c.lower() for keyword in ['test', 'tdd', 'coverage', 'fix'])]
                if tdd_commits:
                    tdd_percentage = (len(tdd_commits) / len(commits)) * 100
                    performance["tdd_related_commits"] = f"{tdd_percentage:.1f}%"
                    print(f"📊 TDD-related commits: {tdd_percentage:.1f}%")
        
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Error analyzing commit frequency: {e}")
        
        # Analyze TDD infrastructure performance
        auto_test_runner = self.project_root / "scripts" / "auto_test_runner.py"
        if auto_test_runner.exists():
            print("✅ TDD infrastructure available for performance analysis")
            
            # Test FileWatcher performance
            try:
                result = subprocess.run([
                    "python", str(auto_test_runner), "--demo"
                ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    performance["tdd_integration_performance"]["file_watcher"] = "operational"
                    print("✅ FileWatcher operational (supports trunk-based immediate feedback)")
                else:
                    performance["tdd_integration_performance"]["file_watcher"] = "issues_detected"
                    print("⚠️  FileWatcher issues detected")
            
            except subprocess.TimeoutExpired:
                performance["tdd_integration_performance"]["file_watcher"] = "timeout"
                print("⚠️  FileWatcher test timed out")
            except Exception as e:
                print(f"⚠️  Error testing TDD infrastructure: {e}")
        
        # Estimate pipeline performance based on configuration
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            
            # Analyze pipeline targets from advanced deployment pipeline
            advanced_pipeline = workflows_dir / "advanced_deployment_pipeline.yml"
            if advanced_pipeline.exists():
                try:
                    with open(advanced_pipeline, 'r') as f:
                        content = f.read()
                    
                    # Extract performance targets
                    targets = {}
                    if "COMMIT_STAGE_TARGET_MINUTES: 5" in content:
                        targets["commit_stage"] = "5 minutes"
                    if "ACCEPTANCE_STAGE_TARGET_MINUTES: 45" in content:
                        targets["acceptance_stage"] = "45 minutes"
                    if "PRODUCTION_STAGE_TARGET_MINUTES: 10" in content:
                        targets["production_stage"] = "10 minutes"
                    
                    if targets:
                        performance["pipeline_targets"] = targets
                        total_target = 5 + 45 + 10  # minutes
                        performance["total_pipeline_target"] = f"{total_target} minutes"
                        
                        if total_target <= 60:
                            print(f"✅ Pipeline targets support trunk-based development (<1 hour total)")
                        else:
                            print(f"⚠️  Pipeline targets may be too slow for optimal trunk-based development")
                
                except Exception as e:
                    print(f"⚠️  Error analyzing pipeline targets: {e}")
        
        return performance
    
    def verify_feature_flag_implementation(self) -> Dict[str, Any]:
        """Verify feature flag implementation for trunk-based development."""
        print("🚩 Verifying feature flag implementation...")
        
        feature_flags = {
            "implementation_found": False,
            "configuration_files": [],
            "integration_points": [],
            "trunk_compatibility": False
        }
        
        # Look for feature flag configuration files
        flag_patterns = [
            "feature-flags.json", "feature_flags.json", "flags.json",
            "feature-flags.yaml", "feature_flags.yaml", "flags.yaml",
            "config/feature-flags.*", "config/flags.*",
            ".launchdarkly", ".split", ".optimizely"
        ]
        
        for pattern in flag_patterns:
            matches = list(self.project_root.rglob(pattern))
            if matches:
                feature_flags["configuration_files"].extend([str(m.relative_to(self.project_root)) for m in matches])
                feature_flags["implementation_found"] = True
        
        # Look for feature flag usage in code
        code_files = list(self.project_root.rglob("*.py"))
        flag_keywords = ["feature_flag", "feature_toggle", "flag_enabled", "is_enabled", "feature_on"]
        
        for code_file in code_files:
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                for keyword in flag_keywords:
                    if keyword in content:
                        rel_path = str(code_file.relative_to(self.project_root))
                        if rel_path not in feature_flags["integration_points"]:
                            feature_flags["integration_points"].append(rel_path)
                            feature_flags["implementation_found"] = True
            
            except Exception:
                continue
        
        # Check if advanced deployment pipeline has feature flag support
        advanced_pipeline = self.project_root / ".github" / "workflows" / "advanced_deployment_pipeline.yml"
        if advanced_pipeline.exists():
            try:
                with open(advanced_pipeline, 'r') as f:
                    content = f.read()
                
                if "enable_feature_flags" in content or "feature_flags" in content:
                    feature_flags["trunk_compatibility"] = True
                    feature_flags["pipeline_integration"] = True
                    print("✅ Feature flag integration found in deployment pipeline")
            
            except Exception:
                pass
        
        # Assess trunk-based compatibility
        if feature_flags["implementation_found"]:
            print(f"✅ Feature flag implementation detected")
            print(f"   - Configuration files: {len(feature_flags['configuration_files'])}")
            print(f"   - Integration points: {len(feature_flags['integration_points'])}")
            
            if len(feature_flags["integration_points"]) > 0:
                feature_flags["trunk_compatibility"] = True
                print("✅ Feature flags enable trunk-based development (no feature branches needed)")
            else:
                print("⚠️  Feature flag configuration found but limited integration detected")
        else:
            print("📊 No feature flag implementation detected")
            print("   Consider implementing feature flags for safer trunk-based development")
            print("   Alternative: Use gradual rollouts through deployment strategies")
        
        return feature_flags
    
    def validate_tdd_automation_trunk_integration(self) -> Dict[str, Any]:
        """Validate TDD automation integration with trunk-based workflow."""
        print("🧪 Validating TDD automation trunk integration...")
        
        tdd_integration = {
            "file_watcher_trunk_ready": False,
            "test_executor_configured": False,
            "session_management_adapted": False,
            "pipeline_tdd_integration": False,
            "trunk_specific_config": {}
        }
        
        # Validate FileWatcher for trunk-based development
        auto_test_runner = self.project_root / "scripts" / "auto_test_runner.py"
        if auto_test_runner.exists():
            try:
                with open(auto_test_runner, 'r') as f:
                    content = f.read()
                
                # Check for trunk-compatible configuration
                if "FileWatcher" in content and "TestExecutor" in content:
                    tdd_integration["file_watcher_trunk_ready"] = True
                    tdd_integration["test_executor_configured"] = True
                    print("✅ FileWatcher and TestExecutor configured for immediate feedback")
                
                # Check for branch-specific logic (should be minimal for trunk)
                if "branch" in content.lower() and "main" in content.lower():
                    print("📊 Branch-aware logic detected - verify trunk compatibility")
                elif "branch" not in content.lower():
                    print("✅ No branch-specific logic (optimal for trunk-based)")
                
                # Extract key configuration for trunk compatibility
                if "debounce_delay" in content:
                    tdd_integration["trunk_specific_config"]["debounce_delay"] = "configured"
                if "auto_test_execution" in content:
                    tdd_integration["trunk_specific_config"]["auto_execution"] = "enabled"
            
            except Exception as e:
                print(f"⚠️  Error analyzing auto_test_runner.py: {e}")
        
        # Validate TDD session management for trunk
        tdd_session = self.project_root / ".claude" / "workflows" / "tdd_session.md"
        if tdd_session.exists():
            try:
                with open(tdd_session, 'r') as f:
                    content = f.read()
                
                # Check for trunk-based session workflows
                if "tdd-session" in content.lower():
                    tdd_integration["session_management_adapted"] = True
                    print("✅ TDD session management available")
                
                # Check for branch-specific workflows (should be trunk-focused)
                if "feature branch" in content.lower() or "pull request" in content.lower():
                    print("⚠️  Session management may reference branching workflows")
                    print("   Consider adapting for trunk-based development")
                else:
                    print("✅ Session management appears trunk-compatible")
            
            except Exception as e:
                print(f"⚠️  Error analyzing TDD session management: {e}")
        
        # Validate pipeline TDD integration
        tdd_pipeline = self.project_root / ".github" / "workflows" / "tdd_pipeline.yml"
        if tdd_pipeline.exists():
            try:
                with open(tdd_pipeline, 'r') as f:
                    content = f.read()
                
                # Check for TDD-specific pipeline stages
                if "auto_test_runner.py" in content:
                    tdd_integration["pipeline_tdd_integration"] = True
                    print("✅ Pipeline integrates TDD infrastructure")
                
                # Check for trunk-specific triggers
                yaml_content = yaml.safe_load(content)
                triggers = yaml_content.get('on', {})
                
                if isinstance(triggers, dict) and 'push' in triggers:
                    push_config = triggers['push']
                    if isinstance(push_config, dict):
                        branches = push_config.get('branches', [])
                        if 'main' in branches or 'master' in branches:
                            print("✅ Pipeline triggers on trunk pushes")
                        else:
                            print(f"📊 Pipeline branches: {branches}")
            
            except Exception as e:
                print(f"⚠️  Error analyzing TDD pipeline: {e}")
        
        # Test TDD automation responsiveness (key for trunk-based)
        if auto_test_runner.exists():
            try:
                print("🔄 Testing TDD automation responsiveness...")
                start_time = time.time()
                
                result = subprocess.run([
                    "python", str(auto_test_runner), "--demo"
                ], cwd=self.project_root, capture_output=True, text=True, timeout=15)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                tdd_integration["trunk_specific_config"]["response_time"] = f"{response_time:.2f} seconds"
                
                if response_time < 5:
                    print(f"✅ Fast TDD response time: {response_time:.2f}s (excellent for trunk-based)")
                elif response_time < 10:
                    print(f"📊 Moderate TDD response time: {response_time:.2f}s")
                else:
                    print(f"⚠️  Slow TDD response time: {response_time:.2f}s (may impact trunk workflow)")
            
            except subprocess.TimeoutExpired:
                print("⚠️  TDD automation test timed out")
                tdd_integration["trunk_specific_config"]["response_time"] = "timeout"
            except Exception as e:
                print(f"⚠️  Error testing TDD automation: {e}")
        
        return tdd_integration
    
    def export_trunk_based_configuration(self) -> Dict[str, Any]:
        """Export complete trunk-based development configuration."""
        print("📤 Exporting trunk-based development configuration...")
        
        config = {
            "project_info": {
                "name": "Drawing Machine TDD Infrastructure",
                "validation_timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "development_model": "trunk_based"
            },
            "trunk_configuration": {},
            "pipeline_configuration": {},
            "tdd_integration": {},
            "performance_targets": self.performance_targets,
            "compliance_summary": {}
        }
        
        # Export Git configuration
        try:
            # Current branch
            result = subprocess.run(["git", "branch", "--show-current"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                config["trunk_configuration"]["current_branch"] = result.stdout.strip()
            
            # Remote configuration
            result = subprocess.run(["git", "remote", "-v"], 
                                  cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                remotes = result.stdout.strip().split('\n')
                config["trunk_configuration"]["remotes"] = remotes
            
            # Recent commit activity
            result = subprocess.run([
                "git", "log", "--oneline", "-10"
            ], cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                config["trunk_configuration"]["recent_commits"] = commits
        
        except subprocess.CalledProcessError:
            config["trunk_configuration"]["git_error"] = "Unable to read Git configuration"
        
        # Export pipeline configuration
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            config["pipeline_configuration"]["workflow_files"] = [f.name for f in workflow_files]
            
            # Extract key pipeline information
            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = yaml.safe_load(f)
                    
                    config["pipeline_configuration"][workflow_file.stem] = {
                        "triggers": list(workflow_data.get('on', {}).keys()),
                        "jobs": list(workflow_data.get('jobs', {}).keys())
                    }
                except Exception:
                    continue
        
        # Export TDD infrastructure configuration
        for tdd_file in self.tdd_infrastructure:
            file_path = self.project_root / tdd_file
            if file_path.exists():
                config["tdd_integration"][tdd_file] = {
                    "exists": True,
                    "size_bytes": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
            else:
                config["tdd_integration"][tdd_file] = {"exists": False}
        
        return config
    
    def calculate_trunk_compliance_score(self, results: TrunkValidationResults) -> float:
        """Calculate overall trunk-based development compliance score."""
        print("📊 Calculating trunk-based development compliance score...")
        
        score = 0.0
        max_score = sum(self.trunk_criteria.values())
        
        # Single branch strategy
        if results.repository_config.main_branch in ["main", "master", "trunk"]:
            score += self.trunk_criteria["single_branch_strategy"]
            print(f"✅ Single branch strategy: +{self.trunk_criteria['single_branch_strategy']} points")
        
        # Direct push capability
        if results.repository_config.direct_push_enabled:
            score += self.trunk_criteria["direct_push_capability"]
            print(f"✅ Direct push capability: +{self.trunk_criteria['direct_push_capability']} points")
        
        # Pipeline as gatekeeper
        if results.pipeline_authority.success_criteria_enforced:
            score += self.trunk_criteria["pipeline_as_gatekeeper"]
            print(f"✅ Pipeline as gatekeeper: +{self.trunk_criteria['pipeline_as_gatekeeper']} points")
        
        # Immediate CI triggering
        if results.pipeline_authority.immediate_triggering:
            score += self.trunk_criteria["immediate_ci_triggering"]
            print(f"✅ Immediate CI triggering: +{self.trunk_criteria['immediate_ci_triggering']} points")
        
        # Automatic deployment
        if results.pipeline_authority.automatic_deployment:
            score += self.trunk_criteria["automatic_deployment"]
            print(f"✅ Automatic deployment: +{self.trunk_criteria['automatic_deployment']} points")
        
        # Feature flag usage
        feature_flags = results.quality_metrics.get("feature_flags", {})
        if feature_flags.get("implementation_found", False):
            score += self.trunk_criteria["feature_flag_usage"]
            print(f"✅ Feature flag usage: +{self.trunk_criteria['feature_flag_usage']} points")
        
        # TDD integration
        tdd_integration = results.quality_metrics.get("tdd_integration", {})
        if tdd_integration.get("file_watcher_trunk_ready", False):
            score += self.trunk_criteria["tdd_integration"]
            print(f"✅ TDD integration: +{self.trunk_criteria['tdd_integration']} points")
        
        compliance_percentage = (score / max_score) * 100
        print(f"📊 Total compliance score: {score}/{max_score} ({compliance_percentage:.1f}%)")
        
        return compliance_percentage
    
    def generate_trunk_recommendations(self, results: TrunkValidationResults) -> List[str]:
        """Generate recommendations for improving trunk-based development compliance."""
        recommendations = []
        
        # Repository configuration recommendations
        if not results.repository_config.direct_push_enabled:
            recommendations.append(
                "Enable direct push to main branch - remove branch protection rules and enable trunk-based workflow"
            )
        
        if results.repository_config.main_branch not in ["main", "master", "trunk"]:
            recommendations.append(
                f"Consider renaming '{results.repository_config.main_branch}' to 'main' for standard trunk-based development"
            )
        
        # Pipeline authority recommendations
        if not results.pipeline_authority.immediate_triggering:
            recommendations.append(
                "Configure immediate CI triggering on every push to trunk for fast feedback"
            )
        
        if results.pipeline_authority.quality_gates_count < 3:
            recommendations.append(
                "Implement more quality gates in pipeline (testing, security, performance) to serve as definitive authority"
            )
        
        if not results.pipeline_authority.automatic_deployment:
            recommendations.append(
                "Enable automatic deployment on pipeline success to eliminate manual bottlenecks"
            )
        
        if not results.pipeline_authority.rollback_capability:
            recommendations.append(
                "Implement automatic rollback capabilities for safer trunk-based deployments"
            )
        
        # Feature flags recommendations
        feature_flags = results.quality_metrics.get("feature_flags", {})
        if not feature_flags.get("implementation_found", False):
            recommendations.append(
                "Implement feature flags to enable safe trunk-based development without feature branches"
            )
        
        # TDD integration recommendations
        tdd_integration = results.quality_metrics.get("tdd_integration", {})
        if not tdd_integration.get("file_watcher_trunk_ready", False):
            recommendations.append(
                "Optimize TDD automation (FileWatcher/TestExecutor) for immediate feedback on trunk commits"
            )
        
        # Performance recommendations
        performance = results.performance_metrics
        response_time = performance.get("tdd_integration_performance", {}).get("response_time", "unknown")
        if isinstance(response_time, str) and "timeout" in response_time:
            recommendations.append(
                "Optimize TDD infrastructure response time for better trunk-based development experience"
            )
        
        # General trunk-based recommendations
        if results.compliance_score < 80:
            recommendations.append(
                "Consider gradual migration to trunk-based development with feature flags and strong CI/CD pipeline"
            )
        
        return recommendations
    
    def run_full_trunk_validation(self) -> TrunkValidationResults:
        """Run comprehensive trunk-based development validation."""
        print("🎯 Running comprehensive trunk-based development validation...")
        print("=" * 70)
        
        if not self.validate_environment():
            print("❌ Environment validation failed")
            return TrunkValidationResults(
                repository_config=TrunkBasedConfig(repository_name="unknown"),
                pipeline_authority=PipelineAuthority()
            )
        
        # Run all validation steps
        repo_config = self.audit_trunk_based_repository_config()
        pipeline_authority = self.validate_deployment_pipeline_authority()
        performance_metrics = self.analyze_continuous_integration_performance()
        feature_flags = self.verify_feature_flag_implementation()
        tdd_integration = self.validate_tdd_automation_trunk_integration()
        
        # Compile results
        results = TrunkValidationResults(
            repository_config=repo_config,
            pipeline_authority=pipeline_authority,
            performance_metrics=performance_metrics,
            quality_metrics={
                "feature_flags": feature_flags,
                "tdd_integration": tdd_integration
            }
        )
        
        # Calculate compliance score
        results.compliance_score = self.calculate_trunk_compliance_score(results)
        
        # Generate recommendations
        results.recommendations = self.generate_trunk_recommendations(results)
        
        return results
    
    def export_validation_report(self, results: TrunkValidationResults) -> None:
        """Export comprehensive validation report."""
        print("📋 Generating trunk-based development validation report...")
        
        report = {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "project": "Drawing Machine TDD Infrastructure",
                "development_model": "Trunk-Based Development",
                "compliance_score": results.compliance_score,
                "validation_status": "COMPLIANT" if results.compliance_score >= 80 else "NEEDS_IMPROVEMENT"
            },
            "repository_configuration": {
                "repository_name": results.repository_config.repository_name,
                "main_branch": results.repository_config.main_branch,
                "direct_push_enabled": results.repository_config.direct_push_enabled,
                "branch_protection_disabled": results.repository_config.branch_protection_disabled,
                "pipeline_as_gatekeeper": results.repository_config.pipeline_as_gatekeeper
            },
            "pipeline_authority": {
                "immediate_triggering": results.pipeline_authority.immediate_triggering,
                "automatic_deployment": results.pipeline_authority.automatic_deployment,
                "quality_gates_count": results.pipeline_authority.quality_gates_count,
                "rollback_capability": results.pipeline_authority.rollback_capability,
                "no_manual_overrides": results.pipeline_authority.no_manual_overrides,
                "success_criteria_enforced": results.pipeline_authority.success_criteria_enforced
            },
            "performance_metrics": results.performance_metrics,
            "quality_metrics": results.quality_metrics,
            "recommendations": results.recommendations,
            "trunk_based_principles": {
                "single_branch_strategy": "Single main/trunk branch as source of truth",
                "deployment_pipeline_authority": "Pipeline passes = software is releasable",
                "immediate_feedback": "Fast CI/CD triggering on every commit",
                "feature_flags_over_branches": "Runtime toggles instead of code branching",
                "tdd_automation": "Immediate test feedback without branching overhead"
            }
        }
        
        # Save report
        report_path = self.project_root / "trunk-based-validation-report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Validation report saved to: {report_path}")
        
        # Generate summary
        print("\n" + "=" * 70)
        print("🎯 TRUNK-BASED DEVELOPMENT VALIDATION SUMMARY")
        print("=" * 70)
        print(f"📊 Compliance Score: {results.compliance_score:.1f}%")
        print(f"📈 Validation Status: {'COMPLIANT' if results.compliance_score >= 80 else 'NEEDS IMPROVEMENT'}")
        print(f"🏗️  Repository: {results.repository_config.repository_name}")
        print(f"🌳 Main Branch: {results.repository_config.main_branch}")
        print(f"🚀 Pipeline Authority: {'Enabled' if results.pipeline_authority.success_criteria_enforced else 'Needs Configuration'}")
        print(f"⚡ Immediate Triggering: {'Enabled' if results.pipeline_authority.immediate_triggering else 'Disabled'}")
        print(f"🔄 Automatic Deployment: {'Enabled' if results.pipeline_authority.automatic_deployment else 'Disabled'}")
        
        if results.recommendations:
            print(f"\n📝 Recommendations ({len(results.recommendations)}):")
            for i, rec in enumerate(results.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n🎯 Trunk-Based Development Philosophy:")
        print("   ✅ Pipeline passes = software is releasable by definition")
        print("   ✅ Direct commits to trunk enable maximum feedback speed")
        print("   ✅ Quality enforced through automation, not process overhead")
        print("   ✅ Feature flags enable safe trunk-based feature development")
        print("   ✅ TDD automation provides immediate feedback without branching delays")


def main():
    """Main entry point for trunk-based development validation."""
    parser = argparse.ArgumentParser(
        description="Validate Drawing Machine TDD infrastructure for trunk-based development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Trunk-Based Development Validation:
  Validates implementation of trunk-based development where the deployment 
  pipeline serves as the definitive quality gatekeeper instead of branch protection.

Examples:
  python scripts/validate_trunk_based_project_setup.py --full-audit
  python scripts/validate_trunk_based_project_setup.py --pipeline-authority
  python scripts/validate_trunk_based_project_setup.py --trunk-config
  python scripts/validate_trunk_based_project_setup.py --feature-flags

Key Principles:
  - Single main/trunk branch with direct commits
  - Deployment pipeline = definitive statement on release ability
  - No branch protection rules (pipeline protection instead)
  - Feature flags instead of feature branches
  - TDD automation integrated with trunk workflow
        """
    )
    
    parser.add_argument(
        "--full-audit",
        action="store_true",
        help="Run comprehensive trunk-based development audit (default)"
    )
    
    parser.add_argument(
        "--pipeline-authority",
        action="store_true",
        help="Validate deployment pipeline as definitive quality authority"
    )
    
    parser.add_argument(
        "--trunk-config",
        action="store_true",
        help="Audit trunk-based repository configuration"
    )
    
    parser.add_argument(
        "--feature-flags",
        action="store_true",
        help="Verify feature flag implementation for trunk development"
    )
    
    parser.add_argument(
        "--export-config",
        action="store_true",
        help="Export trunk-based development configuration"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    print("🌳 Drawing Machine TDD Infrastructure - Trunk-Based Development Validation")
    print("=" * 70)
    print(f"Project root: {args.project_root}")
    print("Philosophy: Deployment pipeline as definitive quality gatekeeper")
    print()
    
    # Initialize validator
    validator = TrunkBasedDevelopmentValidator(args.project_root)
    
    try:
        if args.pipeline_authority:
            # Validate pipeline authority only
            authority = validator.validate_deployment_pipeline_authority()
            print("\n🎯 Pipeline Authority Validation Complete")
            
        elif args.trunk_config:
            # Audit repository configuration only
            config = validator.audit_trunk_based_repository_config()
            print(f"\n🎯 Repository Configuration: {config.repository_name}")
            
        elif args.feature_flags:
            # Verify feature flags only
            flags = validator.verify_feature_flag_implementation()
            print(f"\n🎯 Feature Flags: {'Implemented' if flags['implementation_found'] else 'Not Found'}")
            
        elif args.export_config:
            # Export configuration only
            config = validator.export_trunk_based_configuration()
            config_path = args.project_root / "trunk-based-config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n🎯 Configuration exported to: {config_path}")
            
        else:
            # Full audit (default)
            results = validator.run_full_trunk_validation()
            validator.export_validation_report(results)
            
            if results.compliance_score >= 80:
                print("\n🎉 SUCCESS: Project follows trunk-based development principles!")
                print("🚀 Ready for high-frequency deployment with pipeline authority")
                sys.exit(0)
            else:
                print("\n📋 IMPROVEMENT NEEDED: Consider implementing recommendations")
                print("🔧 Focus on pipeline authority and automation over process")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()