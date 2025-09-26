#!/usr/bin/env python
"""
Simple test to verify health endpoints are working
"""
import requests
import json
import sys


def test_health_endpoints(base_url="http://localhost:8000"):
    """Test all health endpoints"""

    print("Testing Health Endpoints")
    print("=" * 50)

    # Test basic health
    print("\n1. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 503]:
            data = response.json()
            print(f"   Health Status: {data.get('status', 'unknown')}")
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Environment: {data.get('environment', 'unknown')}")
        else:
            print(f"   Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test detailed health
    print("\n2. Testing /health/detailed endpoint...")
    try:
        response = requests.get(f"{base_url}/health/detailed")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 503]:
            data = response.json()
            print(f"   Overall Status: {data.get('status', 'unknown')}")
            print(f"   Checks Passed: {data.get('checks_passed', 0)}")
            print(f"   Checks Failed: {data.get('checks_failed', 0)}")
            components = data.get('components', {})
            if components:
                print("   Components:")
                for name, info in components.items():
                    print(f"      - {name}: {info.get('status', 'unknown')}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test readiness
    print("\n3. Testing /ready endpoint...")
    try:
        response = requests.get(f"{base_url}/ready")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 503]:
            data = response.json()
            print(f"   Ready: {data.get('ready', False)}")
            print(f"   Passed Checks: {data.get('passed_checks', 0)}")
            print(f"   Failed Checks: {data.get('failed_checks', 0)}")
            checks = data.get('checks', [])
            if checks:
                print("   Checks:")
                for check in checks:
                    status = "✅" if check.get('ready') else "❌"
                    print(f"      {status} {check.get('name', 'unknown')}: {check.get('message', '')}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test liveness
    print("\n4. Testing /live endpoint...")
    try:
        response = requests.get(f"{base_url}/live")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Alive: {data.get('alive', False)}")
            print(f"   PID: {data.get('pid', 'unknown')}")
            print(f"   Memory Usage: {data.get('memory_usage_mb', 0):.1f} MB")
            print(f"   CPU Percent: {data.get('cpu_percent', 0):.1f}%")
    except Exception as e:
        print(f"   Error: {e}")

    # Test startup
    print("\n5. Testing /startup endpoint...")
    try:
        response = requests.get(f"{base_url}/startup")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Started: {data.get('started', False)}")
        print(f"   Uptime: {data.get('uptime_seconds', 0):.1f} seconds")
        print(f"   Message: {data.get('message', '')}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test metrics
    print("\n6. Testing /metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            content = response.text[:200]  # Show first 200 chars
            print(f"   Content Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Sample Output:\n{content}...")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 50)
    print("Health Endpoint Testing Complete!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test health endpoints")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL of the service")
    args = parser.parse_args()

    test_health_endpoints(args.url)