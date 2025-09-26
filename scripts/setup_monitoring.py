#!/usr/bin/env python
"""
Setup monitoring infrastructure for Halcytone Content Generator
"""
import os
import sys
import json
import time
import argparse
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MonitoringSetup:
    """Setup production monitoring stack"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = project_root
        self.monitoring_dir = self.project_root / "monitoring"

    def setup_all(self):
        """Setup complete monitoring stack"""
        print("🚀 Setting up Halcytone monitoring stack...")

        # 1. Create necessary directories
        self.create_directories()

        # 2. Setup environment variables
        self.setup_environment()

        # 3. Start monitoring services
        self.start_monitoring_services()

        # 4. Wait for services to be ready
        self.wait_for_services()

        # 5. Configure Grafana
        self.configure_grafana()

        # 6. Setup Kibana
        self.setup_kibana()

        # 7. Verify setup
        self.verify_setup()

        print("✅ Monitoring setup complete!")

    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating monitoring directories...")

        directories = [
            "monitoring/prometheus/data",
            "monitoring/grafana/data",
            "monitoring/elasticsearch/data",
            "monitoring/kibana/data",
            "logs/application",
            "logs/nginx",
            "logs/system"
        ]

        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   Created: {directory}")

    def setup_environment(self):
        """Setup environment variables"""
        print("🔧 Setting up environment variables...")

        # Load or create .env file for monitoring
        env_file = self.project_root / f".env.monitoring.{self.environment}"

        env_vars = {
            "ENVIRONMENT": self.environment,
            "GRAFANA_ADMIN_USER": "admin",
            "GRAFANA_ADMIN_PASSWORD": "admin123",
            "GRAFANA_SECRET_KEY": "halcytone-grafana-secret-key-32chars",
            "ELASTICSEARCH_HOST": "elasticsearch",
            "ELASTICSEARCH_PORT": "9200",
            "KIBANA_HOST": "kibana",
            "KIBANA_PORT": "5601",
            "PROMETHEUS_HOST": "prometheus",
            "PROMETHEUS_PORT": "9090",
            "JAEGER_AGENT_HOST": "jaeger",
            "JAEGER_AGENT_PORT": "6831",
            "ALERT_EMAIL_FROM": "alerts@halcytone.com",
            "SLACK_WEBHOOK_URL": "",  # Set this in production
            "CRITICAL_ALERT_EMAILS": "ops@halcytone.com",
            "APPLICATION_TEAM_EMAILS": "dev@halcytone.com",
            "PLATFORM_TEAM_EMAILS": "platform@halcytone.com"
        }

        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"   Created: {env_file}")

    def start_monitoring_services(self):
        """Start monitoring services with Docker Compose"""
        print("🐳 Starting monitoring services...")

        compose_file = self.monitoring_dir / "docker-compose.monitoring.yml"
        env_file = self.project_root / f".env.monitoring.{self.environment}"

        cmd = [
            "docker-compose",
            "-f", str(compose_file),
            "--env-file", str(env_file),
            "up", "-d"
        ]

        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error starting services: {result.stderr}")
                return False

            print("   Services started successfully")
            return True

        except subprocess.SubprocessError as e:
            print(f"❌ Failed to start services: {e}")
            return False

    def wait_for_services(self, timeout: int = 300):
        """Wait for services to be ready"""
        print("⏳ Waiting for services to be ready...")

        services = {
            "Prometheus": "http://localhost:9090/-/ready",
            "Grafana": "http://localhost:3000/api/health",
            "Elasticsearch": "http://localhost:9200/_cluster/health",
            "Kibana": "http://localhost:5601/api/status",
            "Jaeger": "http://localhost:16686/"
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            all_ready = True

            for service, url in services.items():
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 404]:  # 404 is OK for some services
                        print(f"   ✅ {service} is ready")
                    else:
                        print(f"   ⏳ {service} not ready (status: {response.status_code})")
                        all_ready = False
                except requests.RequestException:
                    print(f"   ⏳ {service} not ready (connection failed)")
                    all_ready = False

            if all_ready:
                print("   ✅ All services are ready!")
                return True

            time.sleep(10)

        print(f"   ⚠️ Timeout waiting for services after {timeout} seconds")
        return False

    def configure_grafana(self):
        """Configure Grafana dashboards and data sources"""
        print("📊 Configuring Grafana...")

        base_url = "http://localhost:3000"
        auth = ("admin", "admin123")  # Default credentials

        # Wait a bit more for Grafana to be fully ready
        time.sleep(10)

        try:
            # Check if Grafana is responsive
            response = requests.get(f"{base_url}/api/health", auth=auth, timeout=10)
            if response.status_code != 200:
                print(f"   ⚠️ Grafana not ready: {response.status_code}")
                return False

            # Import dashboards (they should be automatically loaded via provisioning)
            dashboards = [
                "halcytone-overview.json",
                "halcytone-performance.json",
                "halcytone-errors.json"
            ]

            for dashboard in dashboards:
                dashboard_path = self.monitoring_dir / "grafana" / "dashboards" / dashboard
                if dashboard_path.exists():
                    print(f"   📊 Dashboard {dashboard} will be auto-loaded")
                else:
                    print(f"   ⚠️ Dashboard {dashboard} not found")

            print("   ✅ Grafana configuration complete")
            return True

        except requests.RequestException as e:
            print(f"   ❌ Failed to configure Grafana: {e}")
            return False

    def setup_kibana(self):
        """Setup Kibana index patterns and dashboards"""
        print("🔍 Setting up Kibana...")

        base_url = "http://localhost:5601"

        try:
            # Wait for Kibana to be ready
            timeout = 120
            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{base_url}/api/status", timeout=10)
                    if response.status_code == 200:
                        break
                except:
                    pass
                time.sleep(5)

            # Create index patterns
            index_patterns = [
                {
                    "id": "halcytone-logs-*",
                    "title": "halcytone-logs-*",
                    "timeFieldName": "@timestamp"
                },
                {
                    "id": "halcytone-errors-*",
                    "title": "halcytone-errors-*",
                    "timeFieldName": "@timestamp"
                }
            ]

            headers = {
                "Content-Type": "application/json",
                "kbn-xsrf": "true"
            }

            for pattern in index_patterns:
                try:
                    response = requests.post(
                        f"{base_url}/api/saved_objects/index-pattern/{pattern['id']}",
                        json={"attributes": pattern},
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code in [200, 409]:  # 409 = already exists
                        print(f"   📋 Index pattern {pattern['id']} created")
                    else:
                        print(f"   ⚠️ Failed to create index pattern {pattern['id']}: {response.status_code}")
                except requests.RequestException as e:
                    print(f"   ⚠️ Error creating index pattern {pattern['id']}: {e}")

            print("   ✅ Kibana setup complete")
            return True

        except Exception as e:
            print(f"   ❌ Failed to setup Kibana: {e}")
            return False

    def verify_setup(self):
        """Verify monitoring setup is working"""
        print("✅ Verifying monitoring setup...")

        checks = {
            "Prometheus": self.check_prometheus,
            "Grafana": self.check_grafana,
            "Elasticsearch": self.check_elasticsearch,
            "Kibana": self.check_kibana,
            "AlertManager": self.check_alertmanager,
            "Jaeger": self.check_jaeger
        }

        results = {}
        for service, check_func in checks.items():
            try:
                result = check_func()
                results[service] = result
                status = "✅" if result else "❌"
                print(f"   {status} {service}")
            except Exception as e:
                results[service] = False
                print(f"   ❌ {service}: {e}")

        # Summary
        working_services = sum(1 for r in results.values() if r)
        total_services = len(results)

        print(f"\n📊 Monitoring Setup Summary:")
        print(f"   Services working: {working_services}/{total_services}")

        if working_services == total_services:
            print("   🎉 All monitoring services are operational!")
        else:
            print("   ⚠️ Some services need attention")

        return working_services, total_services

    def check_prometheus(self) -> bool:
        """Check if Prometheus is working"""
        try:
            response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
            if response.status_code == 200:
                targets = response.json()
                active_targets = sum(1 for target in targets.get("data", {}).get("activeTargets", [])
                                   if target.get("health") == "up")
                print(f"      Active targets: {active_targets}")
                return True
        except:
            pass
        return False

    def check_grafana(self) -> bool:
        """Check if Grafana is working"""
        try:
            response = requests.get("http://localhost:3000/api/datasources",
                                  auth=("admin", "admin123"), timeout=5)
            if response.status_code == 200:
                datasources = response.json()
                print(f"      Datasources: {len(datasources)}")
                return True
        except:
            pass
        return False

    def check_elasticsearch(self) -> bool:
        """Check if Elasticsearch is working"""
        try:
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                status = health.get("status", "unknown")
                print(f"      Cluster status: {status}")
                return status in ["green", "yellow"]
        except:
            pass
        return False

    def check_kibana(self) -> bool:
        """Check if Kibana is working"""
        try:
            response = requests.get("http://localhost:5601/api/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                overall_status = status.get("status", {}).get("overall", {}).get("level")
                print(f"      Status: {overall_status}")
                return overall_status == "available"
        except:
            pass
        return False

    def check_alertmanager(self) -> bool:
        """Check if AlertManager is working"""
        try:
            response = requests.get("http://localhost:9093/api/v1/status", timeout=5)
            return response.status_code == 200
        except:
            pass
        return False

    def check_jaeger(self) -> bool:
        """Check if Jaeger is working"""
        try:
            response = requests.get("http://localhost:16686/", timeout=5)
            return response.status_code == 200
        except:
            pass
        return False

    def create_test_data(self):
        """Create test data for monitoring"""
        print("📋 Creating test data...")

        # Generate some test logs
        test_logs = [
            {"level": "INFO", "message": "Test application startup", "service": "halcytone-content-generator"},
            {"level": "ERROR", "message": "Test error for monitoring", "service": "halcytone-content-generator"},
            {"level": "WARN", "message": "Test warning message", "service": "halcytone-content-generator"}
        ]

        logs_dir = self.project_root / "logs" / "application"
        logs_dir.mkdir(parents=True, exist_ok=True)

        test_log_file = logs_dir / "test.log"
        with open(test_log_file, "w") as f:
            for log in test_logs:
                f.write(json.dumps(log) + "\n")

        print(f"   Created test log file: {test_log_file}")

    def stop_monitoring(self):
        """Stop monitoring services"""
        print("🛑 Stopping monitoring services...")

        compose_file = self.monitoring_dir / "docker-compose.monitoring.yml"

        cmd = ["docker-compose", "-f", str(compose_file), "down"]

        try:
            subprocess.run(cmd, cwd=self.project_root, check=True)
            print("   ✅ Services stopped successfully")
        except subprocess.SubprocessError as e:
            print(f"   ❌ Failed to stop services: {e}")

    def show_urls(self):
        """Show monitoring service URLs"""
        print("🌐 Monitoring Service URLs:")
        print("   Prometheus: http://localhost:9090")
        print("   Grafana: http://localhost:3000 (admin/admin123)")
        print("   Kibana: http://localhost:5601")
        print("   Elasticsearch: http://localhost:9200")
        print("   AlertManager: http://localhost:9093")
        print("   Jaeger: http://localhost:16686")


def main():
    parser = argparse.ArgumentParser(description="Setup Halcytone monitoring stack")
    parser.add_argument("--environment", "-e", default="production",
                       help="Environment (development/staging/production)")
    parser.add_argument("--action", "-a", default="setup",
                       choices=["setup", "stop", "verify", "urls", "test-data"],
                       help="Action to perform")

    args = parser.parse_args()

    setup = MonitoringSetup(args.environment)

    if args.action == "setup":
        setup.setup_all()
        setup.show_urls()
    elif args.action == "stop":
        setup.stop_monitoring()
    elif args.action == "verify":
        setup.verify_setup()
    elif args.action == "urls":
        setup.show_urls()
    elif args.action == "test-data":
        setup.create_test_data()


if __name__ == "__main__":
    main()