"""
Environment Health Check Script

Verifies all required components are ready for curator extraction:
- Database connectivity (Neon)
- API keys (Anthropic, LangSmith)
- Python environment and dependencies
- Disk space

Usage:
    python check_environment.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv


def check_python_version():
    """Check Python version is 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        return False, f"Python {version.major}.{version.minor} (need 3.9+)"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_environment_file():
    """Check .env file exists and is readable"""
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        return False, f"Not found at {env_path}"

    load_dotenv(env_path)
    return True, f"Found at {env_path}"


def check_api_keys():
    """Check required API keys are set"""
    results = {}

    # Anthropic API key
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_key:
        results['Anthropic'] = (True, f"Set ({anthropic_key[:8]}...)")
    else:
        results['Anthropic'] = (False, "Missing ANTHROPIC_API_KEY")

    # LangSmith (optional but recommended)
    langsmith_key = os.environ.get('LANGSMITH_API_KEY')
    if langsmith_key:
        results['LangSmith'] = (True, f"Set ({langsmith_key[:8]}...)")
    else:
        results['LangSmith'] = (True, "Not set (optional)")

    return results


def check_database_connection():
    """Test database connectivity to Neon"""
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        return False, "NEON_DATABASE_URL not set"

    try:
        import psycopg
        conn = psycopg.connect(db_url, connect_timeout=5)

        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM staging_extractions")
            count = cur.fetchone()[0]

        conn.close()
        return True, f"Connected (staging_extractions: {count} rows)"

    except ImportError:
        return False, "psycopg not installed (pip install psycopg[binary])"
    except Exception as e:
        return False, f"Connection failed: {str(e)[:100]}"


def check_required_packages():
    """Check required Python packages are installed"""
    packages = {
        'langchain_anthropic': 'LangChain Anthropic',
        'langgraph': 'LangGraph',
        'psycopg': 'PostgreSQL driver',
        'dotenv': 'Python dotenv',
    }

    results = {}
    for module, name in packages.items():
        try:
            __import__(module)
            results[name] = (True, "Installed")
        except ImportError:
            results[name] = (False, "Missing")

    return results


def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.getcwd())
        free_gb = free // (2**30)

        if free_gb < 1:
            return False, f"{free_gb}GB free (need at least 1GB)"
        return True, f"{free_gb}GB free"

    except Exception as e:
        return True, f"Could not check: {e}"


def check_ontology_file():
    """Check ONTOLOGY.md exists (needed for extraction)"""
    ontology_path = Path(__file__).parent.parent / 'ONTOLOGY.md'
    if not ontology_path.exists():
        return False, f"Not found at {ontology_path}"
    return True, f"Found ({ontology_path.stat().st_size} bytes)"


def check_docs_map():
    """Check PROVESKIT_DOCS_MAP.md exists"""
    docs_map_path = Path(__file__).parent / 'PROVESKIT_DOCS_MAP.md'
    if not docs_map_path.exists():
        return False, f"Not found at {docs_map_path}"
    return True, f"Found ({docs_map_path.stat().st_size} bytes)"


def run_health_check(verbose=True):
    """
    Run all health checks and return overall status.

    Returns:
        tuple: (all_passed: bool, results: dict)
    """
    results = {}
    all_passed = True

    # Python version
    passed, msg = check_python_version()
    results['Python Version'] = (passed, msg)
    all_passed = all_passed and passed

    # Environment file
    passed, msg = check_environment_file()
    results['Environment File'] = (passed, msg)
    all_passed = all_passed and passed

    if passed:  # Only check API keys if .env loaded
        # API keys
        api_results = check_api_keys()
        for key, (passed, msg) in api_results.items():
            results[f'API Key ({key})'] = (passed, msg)
            all_passed = all_passed and passed

        # Database
        passed, msg = check_database_connection()
        results['Database (Neon)'] = (passed, msg)
        all_passed = all_passed and passed

    # Required packages
    package_results = check_required_packages()
    for name, (passed, msg) in package_results.items():
        results[f'Package ({name})'] = (passed, msg)
        all_passed = all_passed and passed

    # Disk space
    passed, msg = check_disk_space()
    results['Disk Space'] = (passed, msg)
    all_passed = all_passed and passed

    # Required files
    passed, msg = check_ontology_file()
    results['ONTOLOGY.md'] = (passed, msg)
    all_passed = all_passed and passed

    passed, msg = check_docs_map()
    results['PROVESKIT_DOCS_MAP.md'] = (passed, msg)
    all_passed = all_passed and passed

    if verbose:
        print()
        print("=" * 80)
        print("ENVIRONMENT HEALTH CHECK")
        print("=" * 80)
        print()

        for check_name, (passed, message) in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")

        print()
        print("=" * 80)
        if all_passed:
            print("✅ ALL CHECKS PASSED - Ready for extraction")
        else:
            print("❌ SOME CHECKS FAILED - Fix issues before proceeding")
        print("=" * 80)
        print()

    return all_passed, results


if __name__ == "__main__":
    all_passed, results = run_health_check(verbose=True)
    sys.exit(0 if all_passed else 1)
