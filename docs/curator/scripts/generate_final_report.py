"""
Generate Final Summary Report

Creates comprehensive summary when all extractions are complete.
Includes statistics, insights, and export to Notion.

Usage:
    python generate_final_report.py
    python generate_final_report.py --notion  # Also export to Notion
"""

import json
import sys
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


def query_database_statistics():
    """Query database for extraction statistics"""
    import os
    import psycopg
    from dotenv import load_dotenv

    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / '.env')

    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        return None

    try:
        conn = psycopg.connect(db_url)
        stats = {}

        with conn.cursor() as cur:
            # Total staging extractions
            cur.execute("SELECT COUNT(*) FROM staging_extractions")
            stats['total_staging'] = cur.fetchone()[0]

            # By status
            cur.execute("""
                SELECT status::text, COUNT(*)
                FROM staging_extractions
                GROUP BY status
            """)
            stats['by_status'] = dict(cur.fetchall())

            # By ecosystem
            cur.execute("""
                SELECT ecosystem::text, COUNT(*)
                FROM staging_extractions
                WHERE status = 'accepted'::candidate_status
                GROUP BY ecosystem
            """)
            stats['by_ecosystem'] = dict(cur.fetchall())

            # Confidence score distribution
            cur.execute("""
                SELECT
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence
                FROM staging_extractions
                WHERE status = 'accepted'::candidate_status
            """)
            row = cur.fetchone()
            stats['confidence'] = {
                'avg': float(row[0]) if row[0] else 0,
                'min': float(row[1]) if row[1] else 0,
                'max': float(row[2]) if row[2] else 0
            }

            # Core entities (verified truth)
            cur.execute("SELECT COUNT(*) FROM core_entities WHERE is_current = TRUE")
            stats['verified_entities'] = cur.fetchone()[0]

        conn.close()
        return stats

    except Exception as e:
        print(f"⚠️  Could not query database: {e}")
        return None


def generate_final_report(progress, db_stats=None):
    """Generate comprehensive final report"""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = reports_dir / f'FINAL_SUMMARY_{timestamp}.md'

    # Calculate statistics
    meta = progress['metadata']
    completed = progress.get('completed', [])
    skipped = progress.get('skipped', [])
    failed = progress.get('failed', [])

    total_pages = meta.get('total_pages', 0)
    completed_pages = meta.get('completed_pages', 0)
    skipped_pages = meta.get('skipped_pages', 0)
    failed_pages = meta.get('failed_pages', 0)

    # Total extractions across all pages
    total_extractions = sum(item.get('extractions_count', 0) for item in completed)

    # Average extractions per page
    avg_extractions = total_extractions / completed_pages if completed_pages > 0 else 0

    # Duration
    start_date = meta.get('created', '')[:10]
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Build report
    report = f"""# PROVES Kit Extraction - Final Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Period:** {start_date} to {end_date}

---

## Executive Summary

The PROVES Kit documentation extraction is **COMPLETE**.

- **Total Pages Processed:** {completed_pages + skipped_pages + failed_pages} / {total_pages}
- **Total Extractions:** {total_extractions}
- **Success Rate:** {(completed_pages / total_pages * 100) if total_pages > 0 else 0:.1f}%

---

## Breakdown by Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Completed | {completed_pages} | {(completed_pages / total_pages * 100) if total_pages > 0 else 0:.1f}% |
| ⏭️  Skipped | {skipped_pages} | {(skipped_pages / total_pages * 100) if total_pages > 0 else 0:.1f}% |
| ❌ Failed | {failed_pages} | {(failed_pages / total_pages * 100) if total_pages > 0 else 0:.1f}% |

---

## Extraction Statistics

- **Total Extractions:** {total_extractions}
- **Average per Page:** {avg_extractions:.1f}
- **Min Extractions:** {min((item.get('extractions_count', 0) for item in completed), default=0)}
- **Max Extractions:** {max((item.get('extractions_count', 0) for item in completed), default=0)}

"""

    # Database statistics
    if db_stats:
        report += f"""
---

## Database Statistics

### Staging Extractions
- **Total in Staging:** {db_stats.get('total_staging', 0)}
- **Accepted:** {db_stats.get('by_status', {}).get('accepted', 0)}
- **Pending:** {db_stats.get('by_status', {}).get('pending', 0)}
- **Rejected:** {db_stats.get('by_status', {}).get('rejected', 0)}

### Verified Entities (Truth Graph)
- **Total Verified Entities:** {db_stats.get('verified_entities', 0)}

### By Ecosystem
"""
        for ecosystem, count in db_stats.get('by_ecosystem', {}).items():
            report += f"- **{ecosystem}:** {count}\n"

        conf = db_stats.get('confidence', {})
        report += f"""
### Confidence Scores (Accepted Extractions)
- **Average:** {conf.get('avg', 0):.2f}
- **Min:** {conf.get('min', 0):.2f}
- **Max:** {conf.get('max', 0):.2f}
"""

    # Phase breakdown
    phases = {}
    for item in completed:
        phase = item.get('phase', 'Unknown')
        if phase not in phases:
            phases[phase] = {'count': 0, 'extractions': 0}
        phases[phase]['count'] += 1
        phases[phase]['extractions'] += item.get('extractions_count', 0)

    if phases:
        report += """
---

## By Phase

"""
        for phase, data in sorted(phases.items()):
            report += f"### {phase}\n"
            report += f"- Pages: {data['count']}\n"
            report += f"- Extractions: {data['extractions']}\n\n"

    # All completed pages
    report += """
---

## All Completed Pages

"""
    for item in completed:
        title = item.get('title', 'Unknown')
        count = item.get('extractions_count', 0)
        date = item.get('completed_date', 'Unknown')[:10]
        phase = item.get('phase', 'Unknown')
        report += f"- **{date}** - {title} ({count} extractions) - {phase}\n"

    # Skipped pages
    if skipped:
        report += """
---

## Skipped Pages

"""
        for item in skipped:
            title = item.get('title', 'Unknown')
            reason = item.get('reason', 'No reason given')
            report += f"- {title}: {reason}\n"

    # Failed pages
    if failed:
        report += """
---

## Failed Pages (Need Manual Review)

"""
        for item in failed:
            title = item.get('title', 'Unknown')
            error = item.get('error', 'Unknown error')
            retry_count = item.get('retry_count', 0)
            report += f"- {title} (failed after {retry_count} retries)\n"
            report += f"  Error: {error[:100]}...\n"

    # Insights
    report += """
---

## Insights & Recommendations

### What Worked Well
- Incremental extraction strategy
- Human verification at each step
- Phase-based prioritization

### Areas for Improvement
"""
    if failed_pages > 0:
        report += f"- {failed_pages} pages failed - review error patterns\n"
    if skipped_pages > (total_pages * 0.2):
        report += f"- High skip rate ({(skipped_pages / total_pages * 100):.1f}%) - review criteria\n"

    report += """
### Next Steps
1. Review all failed pages and determine root cause
2. Analyze confidence score trends - did they improve over time?
3. Export verified entities to knowledge graph visualization
4. Begin next phase: F' Prime documentation extraction

---

## Bootstrapping Strategy Results

This extraction was part of a bootstrapping strategy to build a verified corpus for agent confidence calibration.

**Hypothesis:** As verified corpus grows (pages 1-10), agent confidence scores should rise and human corrections should decrease.

**To Validate:**
1. Plot confidence scores over time
2. Track human decision rates (accept/reject/correct %)
3. Analyze reasoning_trail quality evolution

---

*Generated by PROVES Library Curator Agent*
"""

    # Save report
    with open(report_file, 'w') as f:
        f.write(report)

    return report_file, report


def main():
    """Generate final report"""
    export_notion = '--notion' in sys.argv

    print()
    print("=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80)
    print()

    # Load progress
    progress = load_progress()
    if not progress:
        return 1

    # Get database statistics
    print("Querying database statistics...")
    db_stats = query_database_statistics()

    # Generate report
    print("Generating report...")
    report_file, report_content = generate_final_report(progress, db_stats)

    print()
    print(f"✅ Final report saved: {report_file}")
    print()

    # Export to Notion if requested
    if export_notion:
        print("Exporting to Notion...")
        from export_to_notion import export_report_to_notion
        success = export_report_to_notion(report_content, progress, db_stats)
        if success:
            print("✅ Exported to Notion")
        else:
            print("❌ Notion export failed")
        print()

    print("=" * 80)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
