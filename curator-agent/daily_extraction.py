"""
Daily Extraction Workflow

Orchestrates daily PROVES Kit documentation extraction:
1. Runs environment health check
2. Loads progress tracker
3. Determines next page to extract
4. Launches curator agent with that page
5. Updates progress after completion

Usage:
    python daily_extraction.py
    python daily_extraction.py --auto  # Skip confirmation prompt
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import health check
from check_environment import run_health_check


def load_progress():
    """Load progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    if not progress_file.exists():
        print("❌ Progress file not found. Creating new one...")
        initialize_progress()

    with open(progress_file, 'r') as f:
        return json.load(f)


def save_progress(progress):
    """Save progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    progress['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()

    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def initialize_progress():
    """Initialize new progress tracker from docs map"""
    # Read PROVESKIT_DOCS_MAP.md to build page list
    docs_map_path = Path(__file__).parent / 'PROVESKIT_DOCS_MAP.md'

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

    save_progress(progress)
    return progress


def get_next_page(progress):
    """Determine next page to extract based on priority order"""
    next_page = progress.get('next_page')
    if not next_page:
        print("❌ No next page defined in progress tracker")
        return None

    return next_page


def update_progress_after_extraction(progress, page, status, extraction_count=0, error=None, snapshot_ids=None):
    """
    Update progress tracker after extraction attempt.

    Args:
        progress: Progress dict
        page: Page dict that was attempted
        status: 'completed', 'failed', 'skipped'
        extraction_count: Number of extractions made
        error: Error message if failed
        snapshot_ids: List of snapshot IDs created
    """
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "title": page.get('title'),
        "url": page.get('url'),
        "phase": page.get('phase'),
        "date": now,
    }

    if status == 'completed':
        record['extractions_count'] = extraction_count
        record['snapshot_ids'] = snapshot_ids or []
        record['completed_date'] = now
        progress['completed'].append(record)
        progress['metadata']['completed_pages'] += 1

    elif status == 'failed':
        record['error'] = error
        record['failed_date'] = now
        progress['failed'].append(record)
        progress['metadata']['failed_pages'] += 1

    elif status == 'skipped':
        record['reason'] = error or "User skipped"
        record['skipped_date'] = now
        progress['skipped'].append(record)
        progress['metadata']['skipped_pages'] += 1

    # Add to history
    progress['extraction_history'].append({
        "page": page.get('title'),
        "status": status,
        "date": now,
        "extractions": extraction_count if status == 'completed' else 0
    })

    # Update next page (simplified - just move to next in sequence)
    # TODO: Implement smarter next-page selection based on PROVESKIT_DOCS_MAP.md
    progress['next_page'] = determine_next_page(progress)

    save_progress(progress)


def determine_next_page(progress):
    """
    Determine the next page to extract based on:
    - Priority order from PROVESKIT_DOCS_MAP.md
    - What's already completed
    - Current phase

    For now, returns a placeholder. TODO: Parse PROVESKIT_DOCS_MAP.md
    """
    # Simplified: Just provide placeholder
    # In full implementation, would parse PROVESKIT_DOCS_MAP.md and follow priority order

    completed_count = progress['metadata']['completed_pages']

    # Phase 1: Hardware Foundation (pages 1-4)
    hardware_pages = [
        {
            "url": "https://docs.proveskit.space/en/latest/core_documentation/hardware/index.md",
            "title": "Hardware Overview",
            "phase": "Phase 1: Hardware Foundation",
            "priority": 1,
            "reason": "Start with hardware overview to get component list"
        },
        {
            "url": "https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/",
            "title": "PROVES Prime",
            "phase": "Phase 1: Hardware Foundation",
            "priority": 2,
            "reason": "Main board - central component"
        },
        {
            "url": "https://docs.proveskit.space/en/latest/core_documentation/hardware/FC_board/",
            "title": "Flight Control Board",
            "phase": "Phase 1: Hardware Foundation",
            "priority": 3,
            "reason": "F' Prime integration likely documented here"
        },
        {
            "url": "https://docs.proveskit.space/en/latest/core_documentation/hardware/battery_board/",
            "title": "Battery Board",
            "phase": "Phase 1: Hardware Foundation",
            "priority": 4,
            "reason": "Power management architecture"
        },
    ]

    # Return next page based on completed count
    if completed_count < len(hardware_pages):
        return hardware_pages[completed_count]

    # Phase 2: F' Prime Integration
    if completed_count == 4:
        return {
            "url": "https://docs.proveskit.space/en/latest/quick_start/fprime-proves_tutorial/",
            "title": "F' Prime Tutorial",
            "phase": "Phase 2: F' Prime Integration",
            "priority": 5,
            "reason": "Understand F' Prime usage patterns"
        }

    # No more pages defined
    return None


def run_extraction(page, auto=False):
    """
    Launch curator agent to extract from specified page.

    Args:
        page: Page dict with url, title, phase
        auto: If True, skip confirmation prompt

    Returns:
        tuple: (status, extraction_count, snapshot_ids, error)
    """
    from run_proveskit_incremental import run_curator_with_approval

    # Build task for curator
    task = f"""
You are the curator agent for the PROVES Library.

YOUR MISSION: Extract architecture from ONE PAGE of PROVES Kit documentation.

TARGET PAGE:
- URL: {page['url']}
- Title: {page['title']}
- Phase: {page['phase']}
- Why: {page.get('reason', 'Next in sequence')}

EXTRACTION METHODOLOGY (from ONTOLOGY.md - already loaded in your extraction prompt):
Using FRAMES vocabulary, capture:
- COMPONENTS: Hardware/software modules (sensors, boards, F' components)
- INTERFACES: Connection points (I2C, SPI, UART buses, ports)
- FLOWS: What moves through interfaces (data, commands, power, signals)
- MECHANISMS: What maintains connections (drivers, protocols, documentation)

WORKFLOW:
- Extract from THIS PAGE ONLY
- Capture ALL relevant architecture data
- Stage everything for human verification
- Cite source URL for every extraction
- STOP after completing this page

REMEMBER:
- Do NOT assign criticality (humans decide mission impact)
- Do NOT filter based on importance (capture ALL structure)
- You are building institutional memory for student teams
- Stage ALL findings for human verification
"""

    # Generate unique thread ID
    thread_id = f"daily-extraction-{uuid.uuid4().hex[:8]}"

    print()
    print("=" * 80)
    print("DAILY EXTRACTION")
    print("=" * 80)
    print()
    print(f"Page: {page['title']}")
    print(f"URL: {page['url']}")
    print(f"Phase: {page['phase']}")
    print(f"Thread ID: {thread_id}")
    print()
    print("=" * 80)
    print()

    if not auto:
        response = input("Launch extraction? [y/n]: ").strip().lower()
        if response not in ['y', 'yes']:
            return 'skipped', 0, [], "User cancelled"

    try:
        # Run extraction
        result = run_curator_with_approval(task, thread_id=thread_id)

        # TODO: Parse result to get extraction count and snapshot IDs
        # For now, return placeholder
        return 'completed', 0, [], None

    except Exception as e:
        return 'failed', 0, [], str(e)


def main():
    """Main workflow"""
    auto = '--auto' in sys.argv

    print()
    print("=" * 80)
    print("DAILY EXTRACTION WORKFLOW")
    print("=" * 80)
    print()

    # Step 1: Health check
    print("Step 1: Running environment health check...")
    print()
    all_passed, _ = run_health_check(verbose=True)

    if not all_passed:
        print()
        print("❌ Environment check failed. Fix issues before proceeding.")
        return 1

    # Step 2: Load progress
    print("Step 2: Loading progress tracker...")
    progress = load_progress()

    completed = progress['metadata']['completed_pages']
    total = progress['metadata']['total_pages']
    print(f"✅ Progress: {completed}/{total} pages complete")
    print()

    # Step 3: Get next page
    print("Step 3: Determining next page...")
    next_page = get_next_page(progress)

    if not next_page:
        print("✅ No more pages to extract! All done.")
        return 0

    print(f"✅ Next: {next_page['title']}")
    print(f"   URL: {next_page['url']}")
    print(f"   Reason: {next_page.get('reason', 'Next in sequence')}")
    print()

    # Step 4: Run extraction
    print("Step 4: Launching extraction...")
    print()

    status, count, snapshot_ids, error = run_extraction(next_page, auto=auto)

    # Step 5: Update progress
    print()
    print("Step 5: Updating progress tracker...")
    update_progress_after_extraction(
        progress,
        next_page,
        status,
        extraction_count=count,
        error=error,
        snapshot_ids=snapshot_ids
    )

    # Summary
    print()
    print("=" * 80)
    print("DAILY EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Status: {status.upper()}")
    if status == 'completed':
        print(f"Extractions: {count}")
        print(f"Snapshots: {len(snapshot_ids)}")
    elif status == 'failed':
        print(f"Error: {error}")
    print()
    print(f"Progress: {progress['metadata']['completed_pages']}/{progress['metadata']['total_pages']} pages")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
