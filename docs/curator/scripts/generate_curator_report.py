"""
Generate Curator Observation Reports

Creates oversight reports about system efficiency, cost optimization,
limitations, tool gaps, and performance patterns.

Usage:
    # Daily summary
    python generate_curator_report.py --type daily

    # Weekly analysis
    python generate_curator_report.py --type weekly

    # Custom observation
    python generate_curator_report.py --type custom \
        --title "High confidence on datasheet pages" \
        --category "Pattern Discovery" \
        --severity "Informational"
"""

import psycopg
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import json

# Load environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

def get_daily_metrics(conn, date=None):
    """
    Get metrics for a specific day.

    Args:
        conn: Database connection
        date: Date to analyze (defaults to today)

    Returns:
        Dict with daily metrics
    """
    if date is None:
        date = datetime.now(timezone.utc).date()

    with conn.cursor() as cur:
        # Pages processed (snapshots captured)
        cur.execute("""
            SELECT COUNT(*)
            FROM raw_snapshots
            WHERE DATE(captured_at) = %s
        """, (date,))
        pages_processed = cur.fetchone()[0]

        # Extractions created
        cur.execute("""
            SELECT COUNT(*)
            FROM staging_extractions
            WHERE DATE(created_at) = %s
        """, (date,))
        extractions_created = cur.fetchone()[0]

        # Average confidence
        cur.execute("""
            SELECT AVG(confidence_score), AVG(lineage_confidence)
            FROM staging_extractions
            WHERE DATE(created_at) = %s
        """, (date,))
        avg_scores = cur.fetchone()
        avg_confidence = float(avg_scores[0]) if avg_scores[0] else 0.0
        avg_lineage = float(avg_scores[1]) if avg_scores[1] else 0.0

        # Errors (if you have an errors table, otherwise estimate)
        errors_encountered = 0  # Placeholder

        # Pending review
        cur.execute("""
            SELECT COUNT(*)
            FROM staging_extractions
            WHERE status = 'pending'
        """, ())
        pending_review = cur.fetchone()[0]

        # Approved
        cur.execute("""
            SELECT COUNT(*)
            FROM staging_extractions
            WHERE status = 'approved'
        """, ())
        approved = cur.fetchone()[0]

        # Estimate cost (rough calculation)
        # Assume: $0.20 per page extraction
        cost_estimate = pages_processed * 0.20

        return {
            'date': date.isoformat(),
            'pages_processed': pages_processed,
            'extractions_created': extractions_created,
            'extractions_per_page': round(extractions_created / pages_processed, 2) if pages_processed > 0 else 0,
            'avg_confidence': round(avg_confidence, 2),
            'avg_lineage': round(avg_lineage, 2),
            'errors_encountered': errors_encountered,
            'pending_review': pending_review,
            'approved': approved,
            'cost_estimate': round(cost_estimate, 2)
        }

def get_weekly_metrics(conn, end_date=None):
    """
    Get metrics for the past week.

    Args:
        conn: Database connection
        end_date: End of week (defaults to today)

    Returns:
        Dict with weekly metrics
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc).date()

    start_date = end_date - timedelta(days=7)

    with conn.cursor() as cur:
        # Total pages this week
        cur.execute("""
            SELECT COUNT(*)
            FROM raw_snapshots
            WHERE captured_at BETWEEN %s AND %s
        """, (start_date, end_date))
        total_pages = cur.fetchone()[0]

        # Total extractions this week
        cur.execute("""
            SELECT COUNT(*)
            FROM staging_extractions
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        total_extractions = cur.fetchone()[0]

        # Success rate (approved / total)
        cur.execute("""
            SELECT
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                COUNT(*) as total
            FROM staging_extractions
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        result = cur.fetchone()
        approved, rejected, total = result
        success_rate = round((approved / total * 100), 1) if total > 0 else 0

        # Re-extraction rate
        cur.execute("""
            SELECT COUNT(*)
            FROM staging_extractions
            WHERE is_reextraction = TRUE
              AND created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        reextractions = cur.fetchone()[0]
        reextraction_rate = round((reextractions / total * 100), 1) if total > 0 else 0

        # Confidence trends
        cur.execute("""
            SELECT
                AVG(confidence_score) as avg_conf,
                AVG(lineage_confidence) as avg_lineage,
                MIN(confidence_score) as min_conf,
                MAX(confidence_score) as max_conf
            FROM staging_extractions
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        conf_result = cur.fetchone()

        # Estimate weekly cost
        weekly_cost = total_pages * 0.20

        return {
            'week_start': start_date.isoformat(),
            'week_end': end_date.isoformat(),
            'total_pages': total_pages,
            'total_extractions': total_extractions,
            'extractions_per_page': round(total_extractions / total_pages, 2) if total_pages > 0 else 0,
            'approved': approved,
            'rejected': rejected,
            'success_rate': success_rate,
            'reextraction_rate': reextraction_rate,
            'avg_confidence': round(float(conf_result[0]), 2) if conf_result[0] else 0,
            'avg_lineage': round(float(conf_result[1]), 2) if conf_result[1] else 0,
            'min_confidence': round(float(conf_result[2]), 2) if conf_result[2] else 0,
            'max_confidence': round(float(conf_result[3]), 2) if conf_result[3] else 0,
            'weekly_cost': round(weekly_cost, 2)
        }

def generate_daily_summary(metrics):
    """Generate daily summary report text."""
    summary = f"""Daily activity summary for {metrics['date']}

## Metrics
- Pages processed: {metrics['pages_processed']}
- Extractions created: {metrics['extractions_created']}
- Extractions per page: {metrics['extractions_per_page']}
- Average confidence: {metrics['avg_confidence']}
- Average lineage: {metrics['avg_lineage']}
- Errors encountered: {metrics['errors_encountered']}
- Cost estimate: ${metrics['cost_estimate']}

## Status
- Pending review: {metrics['pending_review']}
- Approved: {metrics['approved']}

## Observations
- System operating nominally
- No critical issues detected
"""

    if metrics['avg_confidence'] < 0.7:
        summary += "\n⚠️ WARNING: Average confidence below 0.7 threshold\n"

    if metrics['avg_lineage'] < 0.8:
        summary += "\n⚠️ NOTE: Average lineage confidence below 0.8 (expected for retroactive verifications)\n"

    return summary

def generate_weekly_analysis(metrics):
    """Generate weekly analysis report text."""
    summary = f"""Weekly system analysis for {metrics['week_start']} to {metrics['week_end']}

## Volume
- Total pages processed: {metrics['total_pages']}
- Total extractions: {metrics['total_extractions']}
- Extractions per page: {metrics['extractions_per_page']}

## Quality
- Success rate: {metrics['success_rate']}%
- Re-extraction rate: {metrics['reextraction_rate']}%
- Average confidence: {metrics['avg_confidence']}
- Average lineage: {metrics['avg_lineage']}
- Confidence range: {metrics['min_confidence']} - {metrics['max_confidence']}

## Cost
- Weekly cost: ${metrics['weekly_cost']}
- Monthly projection: ${metrics['weekly_cost'] * 4.3:.2f}
- Budget utilization: {(metrics['weekly_cost'] * 4.3 / 20 * 100):.1f}% of $20 budget

## Trends
"""

    if metrics['success_rate'] > 90:
        summary += "✓ Excellent approval rate (>90%)\n"
    elif metrics['success_rate'] < 70:
        summary += "⚠️ Low approval rate (<70%) - investigate quality issues\n"

    if metrics['reextraction_rate'] > 10:
        summary += "⚠️ High re-extraction rate (>10%) - check confidence thresholds\n"

    if metrics['avg_confidence'] >= 0.8:
        summary += "✓ Good average confidence (≥0.8)\n"

    budget_percent = (metrics['weekly_cost'] * 4.3 / 20 * 100)
    if budget_percent > 100:
        summary += f"⚠️ OVER BUDGET: Projected ${metrics['weekly_cost'] * 4.3:.2f} exceeds $20 limit\n"
    elif budget_percent > 80:
        summary += f"⚠️ Near budget limit: {budget_percent:.1f}% utilized\n"

    return summary

def create_notion_report(
    title,
    report_type,
    category,
    severity,
    summary_text,
    detailed_findings,
    metrics=None,
    suggested_actions=None,
    cost_impact=None,
    efficiency_gain=None,
    use_api=True
):
    """
    Create a report in Notion Curator Observations database.

    Args:
        title: Report title
        report_type: Daily Summary, Weekly Analysis, etc.
        category: Observation category (can be list for multi-select)
        severity: Critical, High, Medium, Low, Informational
        summary_text: Brief executive summary
        detailed_findings: Full analysis
        metrics: JSON string of metrics
        suggested_actions: Recommended actions
        cost_impact: Estimated cost savings ($)
        efficiency_gain: Estimated efficiency gain (hours or %)
        use_api: If True, use Notion API

    Returns:
        Page ID if successful
    """
    if not use_api:
        print(f"\n{'='*80}")
        print(f"CURATOR REPORT: {title}")
        print(f"{'='*80}")
        print(f"Type: {report_type}")
        print(f"Category: {category}")
        print(f"Severity: {severity}")
        print(f"\nSummary:\n{summary_text}")
        if detailed_findings:
            print(f"\nDetailed Findings:\n{detailed_findings}")
        if suggested_actions:
            print(f"\nSuggested Actions:\n{suggested_actions}")
        print(f"{'='*80}\n")
        return None

    try:
        import requests

        notion_api_key = os.getenv('NOTION_API_KEY')
        curator_reports_db = os.getenv('NOTION_CURATOR_REPORTS_DB')

        if not notion_api_key or not curator_reports_db:
            print(f"[WARNING] Notion credentials not configured. Report logged locally only.")
            print(f"Report: {title}")
            return None

        # Build properties
        properties = {
            'Report Title': {
                'title': [{'text': {'content': title}}]
            },
            'Report Date': {
                'date': {'start': datetime.now(timezone.utc).date().isoformat()}
            },
            'Report Type': {
                'select': {'name': report_type}
            },
            'Severity/Priority': {
                'select': {'name': severity}
            },
            'Status': {
                'select': {'name': 'New'}
            },
            'Summary': {
                'rich_text': [{'text': {'content': summary_text[:2000]}}]
            }
        }

        # Add category (multi-select)
        if isinstance(category, list):
            properties['Observation Category'] = {
                'multi_select': [{'name': c} for c in category]
            }
        else:
            properties['Observation Category'] = {
                'multi_select': [{'name': category}]
            }

        # Add optional fields
        if detailed_findings:
            properties['Detailed Findings'] = {
                'rich_text': [{'text': {'content': detailed_findings[:2000]}}]
            }

        if metrics:
            properties['Metrics'] = {
                'rich_text': [{'text': {'content': str(metrics)[:2000]}}]
            }

        if suggested_actions:
            properties['Suggested Actions'] = {
                'rich_text': [{'text': {'content': suggested_actions[:2000]}}]
            }

        if cost_impact is not None:
            properties['Cost Impact'] = {
                'number': cost_impact
            }

        if efficiency_gain is not None:
            properties['Efficiency Gain'] = {
                'number': efficiency_gain
            }

        # Create page
        headers = {
            'Authorization': f'Bearer {notion_api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        data = {
            'parent': {'database_id': curator_reports_db},
            'properties': properties
        }

        response = requests.post(
            'https://api.notion.com/v1/pages',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            page_id = response.json()['id']
            print(f"[REPORT CREATED] {title} -> Notion")
            return page_id
        else:
            print(f"[WARNING] Failed to create report in Notion: {response.status_code}")
            print(f"Report: {title}")
            return None

    except Exception as e:
        print(f"[WARNING] Exception while creating report: {e}")
        print(f"Report: {title}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Generate curator observation reports'
    )
    parser.add_argument(
        '--type',
        type=str,
        required=True,
        choices=['daily', 'weekly', 'custom'],
        help='Type of report to generate'
    )
    parser.add_argument(
        '--title',
        type=str,
        help='Custom report title (for custom type)'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Observation category (for custom type)'
    )
    parser.add_argument(
        '--severity',
        type=str,
        default='Informational',
        choices=['Critical', 'High', 'Medium', 'Low', 'Informational'],
        help='Severity/priority'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print report without sending to Notion'
    )

    args = parser.parse_args()

    # Connect to database
    conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

    try:
        if args.type == 'daily':
            metrics = get_daily_metrics(conn)
            summary = generate_daily_summary(metrics)

            create_notion_report(
                title=f"Daily Summary - {metrics['date']}",
                report_type='Daily Summary',
                category='Performance Analysis',
                severity='Informational',
                summary_text=summary,
                detailed_findings=None,
                metrics=json.dumps(metrics, indent=2),
                use_api=not args.dry_run
            )

        elif args.type == 'weekly':
            metrics = get_weekly_metrics(conn)
            summary = generate_weekly_analysis(metrics)

            create_notion_report(
                title=f"Weekly Analysis - {metrics['week_start']} to {metrics['week_end']}",
                report_type='Weekly Analysis',
                category=['Performance Analysis', 'Cost Optimization'],
                severity='Informational',
                summary_text=summary,
                detailed_findings=None,
                metrics=json.dumps(metrics, indent=2),
                use_api=not args.dry_run
            )

        elif args.type == 'custom':
            if not args.title or not args.category:
                print("Error: --title and --category required for custom reports")
                sys.exit(1)

            create_notion_report(
                title=args.title,
                report_type='Efficiency Audit',
                category=args.category,
                severity=args.severity,
                summary_text="Custom observation report",
                detailed_findings="See notes for details",
                use_api=not args.dry_run
            )

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
