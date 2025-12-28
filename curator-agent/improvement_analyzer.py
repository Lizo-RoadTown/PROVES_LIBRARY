#!/usr/bin/env python3
"""
Improvement Analyzer - Meta-Learning Agent

Analyzes extraction patterns from the staging_extractions table and generates
suggestions for improving prompts, ontology, and extraction methods.

This agent watches:
- Approved extractions (high-quality patterns to reinforce)
- Rejected extractions (failure patterns to avoid)
- Modified extractions (edge cases needing refinement)
- Confidence scores vs. human decisions (calibration issues)

And generates suggestions for:
- Prompt updates (how to extract better)
- Ontology changes (what to track)
- Method improvements (extraction approach)
- Evidence type refinements (classification accuracy)
- Confidence calibration (score reliability)
"""

import os
import psycopg
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path(__file__).parent.parent / '.env' if (Path(__file__).parent.parent / '.env').exists() else Path(__file__).parent / '.env'
load_dotenv(env_path)

# Import our sync module
from src.curator.suggestion_sync import SuggestionSync

DATABASE_URL = os.getenv('NEON_DATABASE_URL')

class ImprovementAnalyzer:
    """Analyzes extraction patterns and generates improvement suggestions"""

    def __init__(self):
        self.db_url = DATABASE_URL
        self.suggestion_sync = SuggestionSync()

    def analyze_and_generate_suggestions(self, lookback_days: int = 7) -> List[str]:
        """
        Main analysis routine - looks back N days and generates suggestions

        Returns: List of suggestion IDs created
        """
        print("=" * 80)
        print("IMPROVEMENT ANALYZER")
        print("=" * 80)
        print(f"Analyzing extractions from the last {lookback_days} days...")
        print()

        # Fetch reviewed extractions
        extractions = self._fetch_reviewed_extractions(lookback_days)
        print(f"Found {len(extractions)} reviewed extractions")

        if not extractions:
            print("No reviewed extractions found. Nothing to analyze.")
            return []

        # Run analysis routines
        suggestions = []

        # 1. Analyze rejection patterns
        rejection_suggestions = self._analyze_rejection_patterns(extractions)
        suggestions.extend(rejection_suggestions)

        # 2. Analyze confidence calibration
        calibration_suggestions = self._analyze_confidence_calibration(extractions)
        suggestions.extend(calibration_suggestions)

        # 3. Analyze evidence type accuracy
        evidence_suggestions = self._analyze_evidence_types(extractions)
        suggestions.extend(evidence_suggestions)

        # 4. Analyze candidate type patterns
        candidate_suggestions = self._analyze_candidate_types(extractions)
        suggestions.extend(candidate_suggestions)

        print()
        print(f"Generated {len(suggestions)} improvement suggestions")
        print()

        # Store and sync suggestions
        suggestion_ids = []
        for suggestion in suggestions:
            suggestion_id = self._store_suggestion(suggestion)
            if suggestion_id:
                suggestion_ids.append(suggestion_id)
                # Sync to Notion
                try:
                    self.suggestion_sync.sync_suggestion(suggestion)
                    print(f"✓ Synced suggestion to Notion: {suggestion['title']}")
                except Exception as e:
                    print(f"✗ Failed to sync suggestion to Notion: {e}")

        return suggestion_ids

    def _fetch_reviewed_extractions(self, lookback_days: int) -> List[Dict[str, Any]]:
        """Fetch all reviewed extractions from the last N days"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        extraction_id, candidate_type, candidate_key,
                        candidate_payload, status, confidence_score,
                        confidence_reason, ecosystem, evidence,
                        evidence_type, review_decision, reviewed_at,
                        created_at, updated_at
                    FROM staging_extractions
                    WHERE reviewed_at >= NOW() - INTERVAL '%s days'
                        AND review_decision IS NOT NULL
                    ORDER BY reviewed_at DESC
                """, (lookback_days,))

                rows = cur.fetchall()
            conn.close()

            extractions = []
            for row in rows:
                extractions.append({
                    'extraction_id': row[0],
                    'candidate_type': row[1],
                    'candidate_key': row[2],
                    'candidate_payload': row[3],
                    'status': row[4],
                    'confidence_score': row[5],
                    'confidence_reason': row[6],
                    'ecosystem': row[7],
                    'evidence': row[8],
                    'evidence_type': row[9],
                    'review_decision': row[10],
                    'reviewed_at': row[11],
                    'created_at': row[12],
                    'updated_at': row[13]
                })

            return extractions

        except Exception as e:
            print(f"Error fetching reviewed extractions: {e}")
            return []

    def _analyze_rejection_patterns(self, extractions: List[Dict]) -> List[Dict]:
        """Analyze why extractions are being rejected"""
        suggestions = []

        # Group rejections by candidate type
        rejections_by_type = defaultdict(list)
        for ext in extractions:
            if ext['review_decision'] == 'reject':
                rejections_by_type[ext['candidate_type']].append(ext)

        # For each type with significant rejections, generate a suggestion
        total_reviewed = len(extractions)
        for candidate_type, rejected in rejections_by_type.items():
            rejection_count = len(rejected)
            rejection_rate = rejection_count / total_reviewed

            # Only suggest if rejection rate is significant
            if rejection_rate > 0.3 and rejection_count >= 3:
                # Analyze common patterns in rejected extractions
                common_reasons = self._extract_common_rejection_reasons(rejected)

                suggestions.append({
                    'suggestion_id': None,  # Will be assigned when stored
                    'category': 'prompt_update',
                    'title': f'Reduce {candidate_type} rejections ({rejection_count} rejected)',
                    'evidence': f'Found {rejection_count} rejected {candidate_type} extractions ({rejection_rate:.1%} rejection rate). Common issues: {", ".join(common_reasons)}',
                    'current_state': f'Extractor is producing {candidate_type} candidates that are frequently rejected by humans.',
                    'proposed_change': f'Update the {candidate_type} extraction prompt to avoid common rejection patterns: {", ".join(common_reasons)}. Add more specific criteria for valid {candidate_type} extractions.',
                    'impact_count': rejection_count,
                    'confidence': 'high' if rejection_count >= 10 else 'medium',
                    'extraction_ids': [ext['extraction_id'] for ext in rejected],
                    'status': 'pending',
                    'created_at': datetime.now()
                })

        return suggestions

    def _analyze_confidence_calibration(self, extractions: List[Dict]) -> List[Dict]:
        """Analyze if confidence scores match human decisions"""
        suggestions = []

        # Find high-confidence rejections and low-confidence approvals
        high_conf_rejections = [
            ext for ext in extractions
            if ext['review_decision'] == 'reject' and ext['confidence_score'] >= 0.8
        ]

        low_conf_approvals = [
            ext for ext in extractions
            if ext['review_decision'] == 'approve' and ext['confidence_score'] < 0.5
        ]

        # Suggest confidence recalibration if there's a significant mismatch
        if len(high_conf_rejections) >= 3:
            suggestions.append({
                'suggestion_id': None,
                'category': 'confidence_calibration',
                'title': f'Recalibrate high-confidence rejections ({len(high_conf_rejections)} cases)',
                'evidence': f'Found {len(high_conf_rejections)} extractions with confidence >= 0.8 that were rejected by humans. The model is overconfident.',
                'current_state': 'Confidence scoring is giving high scores to extractions that humans reject.',
                'proposed_change': 'Recalibrate confidence scoring algorithm. Add penalty factors for characteristics common in these rejected high-confidence extractions. Consider adding human feedback to the confidence model.',
                'impact_count': len(high_conf_rejections),
                'confidence': 'high',
                'extraction_ids': [ext['extraction_id'] for ext in high_conf_rejections],
                'status': 'pending',
                'created_at': datetime.now()
            })

        if len(low_conf_approvals) >= 5:
            suggestions.append({
                'suggestion_id': None,
                'category': 'confidence_calibration',
                'title': f'Boost confidence for approved patterns ({len(low_conf_approvals)} cases)',
                'evidence': f'Found {len(low_conf_approvals)} extractions with confidence < 0.5 that were approved by humans. The model is underconfident.',
                'current_state': 'Confidence scoring is giving low scores to valid extractions.',
                'proposed_change': 'Boost confidence scores for extraction patterns that match these approved cases. Analyze common characteristics and add positive signals to confidence model.',
                'impact_count': len(low_conf_approvals),
                'confidence': 'medium',
                'extraction_ids': [ext['extraction_id'] for ext in low_conf_approvals],
                'status': 'pending',
                'created_at': datetime.now()
            })

        return suggestions

    def _analyze_evidence_types(self, extractions: List[Dict]) -> List[Dict]:
        """Analyze if evidence types are classified correctly"""
        suggestions = []

        # Group by evidence type and check rejection rates
        by_evidence_type = defaultdict(lambda: {'total': 0, 'rejected': 0, 'extractions': []})

        for ext in extractions:
            evidence_type = ext['evidence_type']
            by_evidence_type[evidence_type]['total'] += 1
            by_evidence_type[evidence_type]['extractions'].append(ext)
            if ext['review_decision'] == 'reject':
                by_evidence_type[evidence_type]['rejected'] += 1

        # Find evidence types with high rejection rates
        for evidence_type, stats in by_evidence_type.items():
            if stats['total'] >= 5:
                rejection_rate = stats['rejected'] / stats['total']
                if rejection_rate > 0.5:
                    suggestions.append({
                        'suggestion_id': None,
                        'category': 'evidence_type_refinement',
                        'title': f'Refine {evidence_type} classification ({rejection_rate:.1%} rejected)',
                        'evidence': f'{stats["rejected"]} out of {stats["total"]} {evidence_type} extractions were rejected.',
                        'current_state': f'Evidence type "{evidence_type}" has a {rejection_rate:.1%} rejection rate.',
                        'proposed_change': f'Review the criteria for classifying evidence as "{evidence_type}". Either tighten the classification rules or update the extraction approach for this evidence type.',
                        'impact_count': stats['total'],
                        'confidence': 'medium',
                        'extraction_ids': [ext['extraction_id'] for ext in stats['extractions']],
                        'status': 'pending',
                        'created_at': datetime.now()
                    })

        return suggestions

    def _analyze_candidate_types(self, extractions: List[Dict]) -> List[Dict]:
        """Analyze patterns in candidate type extractions"""
        suggestions = []

        # Count approvals by candidate type
        approvals_by_type = defaultdict(int)
        rejections_by_type = defaultdict(int)

        for ext in extractions:
            if ext['review_decision'] == 'approve':
                approvals_by_type[ext['candidate_type']] += 1
            elif ext['review_decision'] == 'reject':
                rejections_by_type[ext['candidate_type']] += 1

        # Find underrepresented types that might need more extraction
        all_types = set(approvals_by_type.keys()) | set(rejections_by_type.keys())

        for candidate_type in all_types:
            approvals = approvals_by_type.get(candidate_type, 0)
            rejections = rejections_by_type.get(candidate_type, 0)
            total = approvals + rejections

            # If we have very few of a type, suggest boosting it
            if total > 0 and total < 3 and approvals > 0:
                suggestions.append({
                    'suggestion_id': None,
                    'category': 'method_improvement',
                    'title': f'Increase {candidate_type} extraction coverage',
                    'evidence': f'Only {total} {candidate_type} extractions found, but {approvals} were approved. This suggests the type is useful but underrepresented.',
                    'current_state': f'Low coverage of {candidate_type} extractions.',
                    'proposed_change': f'Enhance prompts to extract more {candidate_type} candidates. This type has good approval rate ({approvals}/{total}) but low volume.',
                    'impact_count': total,
                    'confidence': 'low',
                    'extraction_ids': [],
                    'status': 'pending',
                    'created_at': datetime.now()
                })

        return suggestions

    def _extract_common_rejection_reasons(self, rejected_extractions: List[Dict]) -> List[str]:
        """Extract common patterns from rejection confidence reasons"""
        # Simple heuristic: look for repeated words in confidence_reason
        all_words = []
        for ext in rejected_extractions:
            reason = ext.get('confidence_reason', '')
            if reason:
                # Extract keywords (simple tokenization)
                words = reason.lower().split()
                # Filter common words
                filtered = [w for w in words if len(w) > 4 and w not in ['extraction', 'confidence', 'because', 'found', 'based']]
                all_words.extend(filtered)

        if not all_words:
            return ['unclear patterns']

        # Get most common words
        common = Counter(all_words).most_common(3)
        return [word for word, count in common if count >= 2] or ['various issues']

    def _store_suggestion(self, suggestion: Dict) -> str:
        """Store a suggestion in the database and return its ID"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO improvement_suggestions (
                        category, title, evidence, current_state,
                        proposed_change, impact_count, confidence,
                        extraction_ids, status, created_at
                    ) VALUES (
                        %s::suggestion_category, %s, %s, %s,
                        %s, %s, %s::suggestion_confidence,
                        %s, %s::suggestion_status, %s
                    )
                    RETURNING suggestion_id
                """, (
                    suggestion['category'],
                    suggestion['title'],
                    suggestion['evidence'],
                    suggestion['current_state'],
                    suggestion['proposed_change'],
                    suggestion['impact_count'],
                    suggestion['confidence'],
                    suggestion['extraction_ids'],
                    suggestion['status'],
                    suggestion['created_at']
                ))

                result = cur.fetchone()
                suggestion_id = result[0] if result else None

            conn.commit()
            conn.close()

            if suggestion_id:
                # Update suggestion dict with ID
                suggestion['suggestion_id'] = suggestion_id
                print(f"✓ Stored suggestion: {suggestion_id}")
                return suggestion_id
            else:
                print(f"✗ Failed to store suggestion")
                return None

        except Exception as e:
            print(f"Error storing suggestion: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    import sys

    lookback_days = 7
    if len(sys.argv) > 1:
        try:
            lookback_days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid lookback days: {sys.argv[1]}, using default: 7")

    analyzer = ImprovementAnalyzer()
    suggestion_ids = analyzer.analyze_and_generate_suggestions(lookback_days)

    print()
    print("=" * 80)
    print(f"ANALYSIS COMPLETE - Generated {len(suggestion_ids)} suggestions")
    print("=" * 80)

    if suggestion_ids:
        print()
        print("Suggestion IDs:")
        for sid in suggestion_ids:
            print(f"  - {sid}")
        print()
        print("Check Notion database for review!")
