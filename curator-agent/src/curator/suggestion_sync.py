"""
Suggestion Sync - Bidirectional sync for Improvement Suggestions

Handles syncing between Neon database and Notion for meta-learning suggestions:
- Push: Improvement suggestions to Notion for review
- Pull: Approval/rejection status back to Neon database

This module analyzes extraction patterns and generates suggestions for:
- Prompt improvements
- Ontology changes
- Method improvements
- Evidence type refinements
- Confidence calibration
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from notion_client import Client
import psycopg

# Load environment
load_dotenv()

class SuggestionSync:
    """Handles bidirectional sync for improvement suggestions"""

    def __init__(self):
        self.notion_key = os.getenv('NOTION_API_KEY')
        if not self.notion_key:
            raise ValueError("NOTION_API_KEY not found in environment")

        # Use Notion API version 2025-09-03
        self.client = Client(auth=self.notion_key, notion_version="2025-09-03")
        self.db_url = os.getenv('NEON_DATABASE_URL')

        # Suggestions database ID and data source ID
        self.suggestions_db_id = os.getenv('NOTION_SUGGESTIONS_DB_ID')
        self.suggestions_data_source_id = os.getenv('NOTION_SUGGESTIONS_DATA_SOURCE_ID')

        if not self.suggestions_db_id:
            raise ValueError("NOTION_SUGGESTIONS_DB_ID not set in environment")
        if not self.suggestions_data_source_id:
            raise ValueError("NOTION_SUGGESTIONS_DATA_SOURCE_ID not set in environment")

    # =========================================================================
    # PUSH TO NOTION
    # =========================================================================

    def sync_suggestion(self, suggestion_data: Dict[str, Any]) -> str:
        """Push an improvement suggestion to Notion for human review"""

        # Map database status to Notion status
        status_map = {
            'pending': 'Pending',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'implemented': 'Implemented',
            'needs_review': 'Needs Review'
        }

        # Map database category to Notion category
        category_map = {
            'prompt_update': 'Prompt Update',
            'ontology_change': 'Ontology Change',
            'method_improvement': 'Method Improvement',
            'evidence_type_refinement': 'Evidence Type Refinement',
            'confidence_calibration': 'Confidence Calibration'
        }

        # Map database confidence to Notion confidence
        confidence_map = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High'
        }

        # Build properties (only using properties that exist in Notion database)
        properties = {
            "Title": {"title": [{"text": {"content": suggestion_data['title'][:2000]}}]},
            "Category": {"select": {"name": category_map.get(suggestion_data['category'], 'Method Improvement')}},
            "Impact": {"number": suggestion_data.get('impact_count', 0)},
            "Confidence": {"select": {"name": confidence_map.get(suggestion_data['confidence'], 'Medium')}},
            "Status": {"status": {"name": status_map.get(suggestion_data.get('status', 'pending'), 'Pending')}}
        }

        # Note: Evidence, Current State, Proposed Change, Suggestion ID, and Extraction IDs
        # are displayed in the page content blocks instead of as properties

        # Build content blocks with formatted details
        content_blocks = self._build_suggestion_content_blocks(suggestion_data)

        # Create the page
        # Use data_source_id for API version 2025-09-03
        try:
            page = self.client.pages.create(
                parent={"type": "data_source_id", "data_source_id": self.suggestions_data_source_id},
                properties=properties,
                children=content_blocks
            )

            page_id = page["id"]
            print(f"✓ Created Notion page for suggestion: {page_id}")

            # Update database with Notion page ID
            self._update_notion_page_id(suggestion_data['suggestion_id'], page_id)

            return page_id

        except Exception as e:
            print(f"Error creating Notion page for suggestion: {e}")
            raise

    def _build_suggestion_content_blocks(
        self,
        suggestion_data: Dict[str, Any]
    ) -> List[Dict]:
        """Build formatted Notion content blocks for suggestion display"""
        blocks = []

        # 🔍 PATTERN ANALYSIS
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🔍 PATTERN ANALYSIS"}}]}
        })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": suggestion_data['evidence']}}]}
        })

        # 📊 CURRENT STATE
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📊 CURRENT STATE"}}]}
        })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": suggestion_data['current_state']}}]}
        })

        # 💡 PROPOSED CHANGE
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "💡 PROPOSED CHANGE"}}]}
        })

        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": suggestion_data['proposed_change']}}],
                "icon": {"emoji": "💡"},
                "color": "blue_background"
            }
        })

        # 📈 IMPACT
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📈 IMPACT"}}]}
        })

        impact_text = f"This suggestion affects {suggestion_data.get('impact_count', 0)} extraction(s)"
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": impact_text}}]}
        })

        # 🔗 SUPPORTING EXTRACTIONS
        if suggestion_data.get('extraction_ids'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔗 SUPPORTING EXTRACTIONS"}}]}
            })

            extraction_list = '\n'.join(f"• {eid}" for eid in suggestion_data['extraction_ids'][:10])
            if len(suggestion_data['extraction_ids']) > 10:
                extraction_list += f"\n• ... and {len(suggestion_data['extraction_ids']) - 10} more"

            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": extraction_list}}]}
            })

        # 🔖 METADATA
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🔖 METADATA"}}]}
        })

        metadata_text = f"Suggestion ID: {suggestion_data['suggestion_id']}"
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": metadata_text}}]}
        })

        return blocks

    def _update_notion_page_id(self, suggestion_id: str, page_id: str):
        """Update the database with the Notion page ID"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE improvement_suggestions
                    SET notion_page_id = %s,
                        updated_at = NOW()
                    WHERE suggestion_id = %s::uuid
                """, (page_id, suggestion_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating notion_page_id: {e}")
            raise

    # =========================================================================
    # PULL FROM NOTION (Status Updates)
    # =========================================================================

    def update_suggestion_status(
        self,
        suggestion_id: str,
        new_status: str,
        review_decision: str = None
    ) -> bool:
        """Update the status of a suggestion in the Neon database"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                if review_decision:
                    # Update with review tracking
                    cur.execute("""
                        UPDATE improvement_suggestions
                        SET status = %s::suggestion_status,
                            updated_at = NOW(),
                            reviewed_at = NOW(),
                            review_decision = %s
                        WHERE suggestion_id = %s::uuid
                        RETURNING suggestion_id
                    """, (new_status, review_decision, suggestion_id))
                else:
                    # Update without review tracking
                    cur.execute("""
                        UPDATE improvement_suggestions
                        SET status = %s::suggestion_status,
                            updated_at = NOW()
                        WHERE suggestion_id = %s::uuid
                        RETURNING suggestion_id
                    """, (new_status, suggestion_id))

                result = cur.fetchone()
                conn.commit()
            conn.close()

            if result:
                print(f"✓ Updated suggestion {suggestion_id} status to {new_status}")
                return True
            else:
                print(f"✗ Suggestion {suggestion_id} not found")
                return False

        except Exception as e:
            print(f"Error updating suggestion status: {e}")
            return False

    def get_suggestion_by_page_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a suggestion from the database by its Notion page ID"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        suggestion_id, category, title, evidence,
                        current_state, proposed_change, impact_count,
                        confidence, extraction_ids, status,
                        review_decision, reviewed_at, review_notes,
                        notion_page_id, created_at, updated_at
                    FROM improvement_suggestions
                    WHERE notion_page_id = %s
                """, (page_id,))

                row = cur.fetchone()
            conn.close()

            if not row:
                return None

            return {
                'suggestion_id': row[0],
                'category': row[1],
                'title': row[2],
                'evidence': row[3],
                'current_state': row[4],
                'proposed_change': row[5],
                'impact_count': row[6],
                'confidence': row[7],
                'extraction_ids': row[8],
                'status': row[9],
                'review_decision': row[10],
                'reviewed_at': row[11],
                'review_notes': row[12],
                'notion_page_id': row[13],
                'created_at': row[14],
                'updated_at': row[15]
            }

        except Exception as e:
            print(f"Error retrieving suggestion by page ID: {e}")
            return None
