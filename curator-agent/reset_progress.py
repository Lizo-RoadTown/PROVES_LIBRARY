"""
Reset Extraction Progress

Resets the progress tracker to start over.
Creates backup of old progress before resetting.

Usage:
    python reset_progress.py
    python reset_progress.py --confirm  # Skip confirmation prompt
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone


def backup_progress():
    """Create backup of current progress"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    if not progress_file.exists():
        return None

    # Create backup with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = Path(__file__).parent / f'extraction_progress_backup_{timestamp}.json'

    shutil.copy(progress_file, backup_file)
    return backup_file


def reset_progress():
    """Reset progress tracker to initial state"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'

    # Initial state
    progress = {
        "metadata": {
            "created": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_pages": 60,
            "completed_pages": 0,
            "skipped_pages": 0,
            "failed_pages": 0,
            "current_phase": "Phase 1: Hardware Foundation"
        },
        "completed": [],
        "skipped": [],
        "failed": [],
        "next_page": {
            "url": "https://docs.proveskit.space/en/latest/core_documentation/hardware/index.md",
            "title": "Hardware Overview",
            "phase": "Phase 1: Hardware Foundation",
            "priority": 1,
            "reason": "Start with hardware overview to get component list"
        },
        "extraction_history": []
    }

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

    return True


def main():
    """Main function"""
    auto_confirm = '--confirm' in sys.argv

    print()
    print("=" * 80)
    print("RESET EXTRACTION PROGRESS")
    print("=" * 80)
    print()
    print("⚠️  WARNING: This will reset ALL extraction progress!")
    print("   A backup will be created before resetting.")
    print()

    if not auto_confirm:
        response = input("Are you sure you want to reset? [yes/no]: ").strip().lower()
        if response != 'yes':
            print("Cancelled.")
            return 0

    # Backup current progress
    print()
    print("Creating backup...")
    backup_file = backup_progress()

    if backup_file:
        print(f"✅ Backup saved to: {backup_file}")
    else:
        print("⚠️  No existing progress to backup")

    # Reset
    print()
    print("Resetting progress...")
    reset_progress()
    print("✅ Progress reset to initial state")

    print()
    print("=" * 80)
    print("RESET COMPLETE")
    print("=" * 80)
    print()
    print("Next page: Hardware Overview")
    print("Run: python daily_extraction.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
