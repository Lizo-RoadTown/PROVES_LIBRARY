#!/usr/bin/env python3
"""
PROVES Library Setup Script

Automates environment setup:
1. Checks Python version
2. Installs dependencies
3. Configures environment variables
4. Sets up database (Supabase or Docker)
5. Runs migrations
6. Verifies installation
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

class SetupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'
        self.env_example = self.project_root / '.env.example'

    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70 + "\n")

    def print_step(self, step_num: int, text: str):
        """Print step header"""
        print(f"\n[Step {step_num}] {text}")
        print("-" * 70)

    def run_command(self, cmd: list, description: str) -> bool:
        """Run a command and return success status"""
        print(f"Running: {description}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[OK] {description}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {description} failed:")
            print(e.stderr)
            return False

    def check_python_version(self) -> bool:
        """Check if Python version is 3.11+"""
        self.print_step(1, "Checking Python version")
        version = sys.version_info
        print(f"Python version: {version.major}.{version.minor}.{version.micro}")

        if version.major >= 3 and version.minor >= 11:
            print("[OK] Python 3.11+ detected")
            return True
        else:
            print("[ERROR] Python 3.11+ required")
            print("Please install Python 3.11 or higher from https://www.python.org/downloads/")
            return False

    def install_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt"""
        self.print_step(2, "Installing Python dependencies")

        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            print("[ERROR] requirements.txt not found")
            return False

        return self.run_command(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
            "pip install -r requirements.txt"
        )

    def setup_env_file(self) -> bool:
        """Set up .env file with user input"""
        self.print_step(3, "Configuring environment variables")

        if self.env_file.exists():
            print(f"[WARNING] .env file already exists at {self.env_file}")
            overwrite = input("Overwrite existing .env file? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("[SKIPPED] Using existing .env file")
                return True

        # Copy .env.example to .env
        if not self.env_example.exists():
            print("[ERROR] .env.example not found")
            return False

        env_content = self.env_example.read_text()

        print("\nConfigure your environment variables:")
        print("(Press Enter to skip optional values)\n")

        # Get Anthropic API key (required)
        print("REQUIRED: Anthropic API key")
        print("Get yours at: https://console.anthropic.com/settings/keys")
        anthropic_key = input("Enter your ANTHROPIC_API_KEY: ").strip()
        if not anthropic_key:
            print("[ERROR] Anthropic API key is required")
            return False
        env_content = env_content.replace('sk-ant-api03-your_anthropic_api_key_here', anthropic_key)

        # Ask about database choice
        print("\nDatabase setup:")
        print("  1. Supabase (cloud, recommended)")
        print("  2. Local PostgreSQL (Docker, for development)")
        db_choice = input("Choose option (1 or 2): ").strip()

        if db_choice == '1':
            print("\nSupabase setup:")
            print("1. Sign up at https://supabase.com (free tier available)")
            print("2. Create a new project")
            print("3. Go to Settings > Database > Connection string")
            print("4. Copy the 'Direct connection' URL (port 5432)")
            db_url = input("Enter your DATABASE_URL: ").strip()
            if db_url:
                env_content = env_content.replace(
                    'postgresql://user:password@host:5432/postgres',
                    db_url
                )
            else:
                print("[WARNING] Using placeholder database URL")
        elif db_choice == '2':
            print("\n[INFO] Using local PostgreSQL via Docker")
            print("[INFO] Connection string: postgresql://proves_user:proves_password@localhost:5432/proves")
            env_content = env_content.replace(
                'postgresql://user:password@host:5432/postgres',
                'postgresql://proves_user:proves_password@localhost:5432/proves'
            )
        else:
            print("[WARNING] Invalid choice, using placeholder database URL")

        # Optional: LangSmith
        print("\nOPTIONAL: LangSmith (for tracing and observability)")
        setup_langsmith = input("Configure LangSmith? (y/N): ").strip().lower()
        if setup_langsmith == 'y':
            print("Get your API key at: https://smith.langchain.com/settings")
            langsmith_key = input("Enter your LANGSMITH_API_KEY: ").strip()
            if langsmith_key:
                env_content = env_content.replace('lsv2_sk_your_langsmith_api_key_here', langsmith_key)

        # Note: Notion integration has been deprecated in favor of the Curation Dashboard

        # Write .env file
        self.env_file.write_text(env_content)
        print(f"\n[OK] Environment file created at {self.env_file}")
        return True

    def setup_database(self) -> bool:
        """Set up database (Docker or verify Neon connection)"""
        self.print_step(4, "Setting up database")

        # Load .env to check database choice
        env_vars = {}
        if self.env_file.exists():
            for line in self.env_file.read_text().split('\n'):
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        db_url = env_vars.get('DATABASE_URL', '') or env_vars.get('PROVES_DATABASE_URL', '')

        if 'localhost' in db_url or '127.0.0.1' in db_url:
            # Local Docker setup
            print("Starting local PostgreSQL with Docker Compose...")
            docker_compose = self.project_root / 'docker-compose.yml'

            if not docker_compose.exists():
                print("[ERROR] docker-compose.yml not found")
                return False

            # Check if Docker is installed
            try:
                subprocess.run(['docker', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("[ERROR] Docker not found. Please install Docker Desktop:")
                print("  https://www.docker.com/products/docker-desktop/")
                return False

            # Start Docker Compose
            result = self.run_command(
                ['docker-compose', 'up', '-d'],
                "docker-compose up -d"
            )

            if result:
                print("\n[OK] Local PostgreSQL started")
                print("Waiting for database to be ready...")
                import time
                time.sleep(5)  # Wait for PostgreSQL to initialize
                return True
            else:
                return False
        else:
            # Supabase/cloud setup - just verify URL is set
            if 'your_' in db_url or not db_url:
                print("[WARNING] Database URL not configured properly")
                print("Please update DATABASE_URL in .env file")
                return False
            else:
                print("[OK] Using cloud database (Supabase)")
                return True

    def run_migrations(self) -> bool:
        """Run database migrations"""
        self.print_step(5, "Running database migrations")

        print("[INFO] Migrations should be applied via Supabase CLI or Dashboard")
        print("       See: supabase/migrations/ folder for migration files")
        print("       Run: supabase db push (if using Supabase CLI)")
        return True

    def verify_setup(self) -> bool:
        """Verify installation by testing database connection"""
        self.print_step(6, "Verifying installation")

        db_connector = self.project_root / 'production' / 'core' / 'db_connector.py'

        if not db_connector.exists():
            print("[ERROR] db_connector.py not found")
            return False

        print("Testing database connection...")
        return self.run_command(
            [sys.executable, str(db_connector)],
            "Database connection test"
        )

    def print_next_steps(self):
        """Print next steps after successful setup"""
        self.print_header("Setup Complete!")

        print("Next steps:\n")
        print("1. Find documentation sources:")
        print("   python production/scripts/find_good_urls.py --fprime --proveskit --max-pages 50\n")
        print("2. Run extractions:")
        print("   python production/scripts/process_extractions.py --limit 10\n")
        print("3. Generate progress report:")
        print("   python testing/scripts/generate_progress_report.py\n")
        print("4. Analyze extraction quality:")
        print("   python production/scripts/improvement_analyzer.py\n")

        print("Documentation:")
        print("  - README.md - Project overview")
        print("  - production/README.md - How to run the curator")
        print("  - docs/MCP_INTEGRATION.md - Natural language queries")
        print("  - production/docs/NOTION_INTEGRATION_GUIDE.md - Human verification\n")

    def run_setup(self):
        """Run complete setup process"""
        self.print_header("PROVES Library Setup")

        steps = [
            self.check_python_version,
            self.install_dependencies,
            self.setup_env_file,
            self.setup_database,
            self.run_migrations,
            self.verify_setup,
        ]

        for step in steps:
            if not step():
                print("\n" + "=" * 70)
                print("  [FAILED] Setup failed at step above")
                print("=" * 70)
                sys.exit(1)

        self.print_next_steps()


if __name__ == '__main__':
    setup = SetupManager()
    setup.run_setup()
