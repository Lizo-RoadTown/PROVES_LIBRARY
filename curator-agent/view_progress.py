"""
View Extraction Progress

Displays current status of PROVES Kit documentation extraction.

Usage:
    python view_progress.py
    python view_progress.py --detailed
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_progress():
    """Load progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    if not progress_file.exists():
        return None

    with open(progress_file, 'r') as f:
        return json.load(f)


def display_progress(detailed=False):
    """Display progress summary"""
    progress = load_progress()
    if not progress:
        print("❌ No progress file found. Run daily_extraction.py to initialize.")
        return

    meta = progress['metadata']
    completed = progress.get('completed', [])
    skipped = progress.get('skipped', [])
    failed = progress.get('failed', [])
    next_page = progress.get('next_page', {})

    print()
    print("=" * 80)
    print("PROVES KIT EXTRACTION PROGRESS")
    print("=" * 80)
    print()

    # Summary
    print(f"Phase: {meta.get('current_phase', 'Unknown')}")
    print(f"Total Pages: {meta.get('total_pages', 0)}")
    print(f"Completed: {meta.get('completed_pages', 0)} ✅")
    print(f"Skipped: {meta.get('skipped_pages', 0)} ⏭️")
    print(f"Failed: {meta.get('failed_pages', 0)} ❌")
    print(f"Remaining: {meta.get('total_pages', 0) - meta.get('completed_pages', 0) - meta.get('skipped_pages', 0)}")
    print()

    # Progress bar
    total = meta.get('total_pages', 60)
    done = meta.get('completed_pages', 0)
    progress_pct = (done / total * 100) if total > 0 else 0
    bar_length = 40
    filled = int(bar_length * done / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"Progress: [{bar}] {progress_pct:.1f}%")
    print()

    # Next page
    if next_page:
        print("Next Page:")
        print(f"  Title: {next_page.get('title', 'Unknown')}")
        print(f"  URL: {next_page.get('url', 'Unknown')}")
        print(f"  Reason: {next_page.get('reason', 'N/A')}")
        print()

    # Last updated
    last_updated = meta.get('last_updated', 'Unknown')
    print(f"Last Updated: {last_updated}")
    print()

    # Detailed view
    if detailed:
        print("=" * 80)
        print("DETAILED HISTORY")
        print("=" * 80)
        print()

        if completed:
            print(f"✅ Completed ({len(completed)}):")
            for item in completed[-10:]:  # Show last 10
                title = item.get('title', 'Unknown')
                date = item.get('completed_date', 'Unknown')
                extractions = item.get('extractions_count', 0)
                print(f"  • {title} ({extractions} extractions) - {date}")
            print()

        if failed:
            print(f"❌ Failed ({len(failed)}):")
            for item in failed:
                title = item.get('title', 'Unknown')
                error = item.get('error', 'Unknown error')
                print(f"  • {title}: {error[:60]}...")
            print()

        if skipped:
            print(f"⏭️  Skipped ({len(skipped)}):")
            for item in skipped:
                title = item.get('title', 'Unknown')
                reason = item.get('reason', 'No reason given')
                print(f"  • {title}: {reason}")
            print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    detailed = '--detailed' in sys.argv or '-d' in sys.argv
    display_progress(detailed=detailed)
