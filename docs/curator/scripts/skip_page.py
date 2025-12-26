"""
Skip Current Page

Marks the current page as skipped and moves to next page.
Use when a page is irrelevant or broken.

Usage:
    python skip_page.py "Reason for skipping"
    python skip_page.py "Page is tutorial, not architecture docs"
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone


def load_progress():
    """Load progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    if not progress_file.exists():
        print("❌ No progress file found")
        return None

    with open(progress_file, 'r') as f:
        return json.load(f)


def save_progress(progress):
    """Save progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    progress['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def skip_current_page(reason):
    """Skip the current page and move to next"""
    progress = load_progress()
    if not progress:
        return False

    current_page = progress.get('next_page')
    if not current_page:
        print("❌ No current page to skip")
        return False

    # Add to skipped list
    progress['skipped'].append({
        "title": current_page.get('title'),
        "url": current_page.get('url'),
        "phase": current_page.get('phase'),
        "reason": reason,
        "skipped_date": datetime.now(timezone.utc).isoformat()
    })

    progress['metadata']['skipped_pages'] += 1

    # Add to history
    progress['extraction_history'].append({
        "page": current_page.get('title'),
        "status": "skipped",
        "date": datetime.now(timezone.utc).isoformat(),
        "extractions": 0,
        "reason": reason
    })

    # Move to next page (import from daily_extraction)
    from daily_extraction import determine_next_page
    progress['next_page'] = determine_next_page(progress)

    save_progress(progress)

    print()
    print("=" * 80)
    print("PAGE SKIPPED")
    print("=" * 80)
    print()
    print(f"Skipped: {current_page.get('title')}")
    print(f"Reason: {reason}")
    print()

    if progress['next_page']:
        print(f"Next: {progress['next_page'].get('title')}")
        print(f"URL: {progress['next_page'].get('url')}")
    else:
        print("No more pages in queue")

    print()
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skip_page.py \"Reason for skipping\"")
        print()
        print("Example:")
        print('  python skip_page.py "Page is tutorial, not architecture"')
        sys.exit(1)

    reason = " ".join(sys.argv[1:])
    success = skip_current_page(reason)
    sys.exit(0 if success else 1)
