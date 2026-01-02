"""
Notion Integration for Curator Agent

Handles bidirectional sync between Neon database and Notion:
- Push: Errors, extractions, and reports to Notion
- Pull: Status updates from Notion back to Neon database

Uses Notion API v2025-09-03 with webhook support.
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

class NotionSync:
    """Handles all Notion integration operations"""

    def __init__(self):
        self.notion_key = os.getenv('NOTION_API_KEY')
        if not self.notion_key:
            raise ValueError("NOTION_API_KEY not found in environment")

        # Use Notion API version 2025-09-03 (multi-source databases)
        self.client = Client(auth=self.notion_key, notion_version="2025-09-03")
        self.db_url = os.getenv('NEON_DATABASE_URL')

        # Database IDs (loaded from env or created)
        self.errors_db_id = os.getenv('NOTION_ERRORS_DB_ID')
        self.extractions_db_id = os.getenv('NOTION_EXTRACTIONS_DB_ID')
        self.extractions_data_source_id = os.getenv('NOTION_EXTRACTIONS_DATA_SOURCE_ID')
        self.reports_db_id = os.getenv('NOTION_REPORTS_DB_ID')

    # =========================================================================
    # DATABASE CREATION & UPDATES
    # =========================================================================

    def add_review_decision_property(self):
        """Add Review Decision property to existing extractions database"""
        if not self.extractions_db_id:
            raise ValueError("NOTION_EXTRACTIONS_DB_ID not set")

        try:
            self.client.databases.update(
                database_id=self.extractions_db_id,
                properties={
                    "Review Decision": {
                        "select": {
                            "options": [
                                {"name": "Approve", "color": "green"},
                                {"name": "Reject", "color": "red"}
                            ]
                        }
                    }
                }
            )
            print("✓ Added 'Review Decision' property to Extractions database")
        except Exception as e:
            print(f"Error adding Review Decision property: {e}")
            raise

    def create_errors_database(self, parent_page_id: str) -> str:
        """Create the Curator Errors Log database in Notion"""
        database = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Curator Errors Log"}}],
            properties={
                "URL": {"title": {}},  # Title property
                "Error Message": {"rich_text": {}},
                "Stack Trace": {"rich_text": {}},
                "Timestamp": {"date": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "New", "color": "red"},
                            {"name": "Investigating", "color": "yellow"},
                            {"name": "Resolved", "color": "green"}
                        ]
                    }
                },
                "Error ID": {"rich_text": {}}  # For tracking
            }
        )
        return database["id"]

    def create_extractions_database(self, parent_page_id: str) -> str:
        """Create the Staging Extractions Review database in Notion"""
        database = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Staging Extractions Review"}}],
            properties={
                "Candidate Key": {"title": {}},  # Title property
                "Type": {
                    "select": {
                        "options": [
                            {"name": "component", "color": "blue"},
                            {"name": "port", "color": "green"},
                            {"name": "command", "color": "purple"},
                            {"name": "telemetry", "color": "orange"},
                            {"name": "event", "color": "pink"},
                            {"name": "parameter", "color": "yellow"},
                            {"name": "data_type", "color": "gray"},
                            {"name": "dependency", "color": "red"},
                            {"name": "connection", "color": "brown"},
                            {"name": "inheritance", "color": "default"}
                        ]
                    }
                },
                "Evidence Quote": {"rich_text": {}},
                "Source URL": {"url": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Pending", "color": "yellow"},
                            {"name": "Approved", "color": "green"},
                            {"name": "Rejected", "color": "red"},
                            {"name": "Needs Review", "color": "orange"}
                        ]
                    }
                },
                "Confidence Score": {"number": {"format": "percent"}},
                "Extraction ID": {"rich_text": {}},  # UUID for sync back
                "Created At": {"date": {}},
                "Ecosystem": {"select": {
                    "options": [
                        {"name": "fprime", "color": "blue"},
                        {"name": "proveskit", "color": "green"},
                        {"name": "pysquared", "color": "purple"},
                        {"name": "cubesat_general", "color": "gray"},
                        {"name": "external", "color": "default"}
                    ]
                }},
                "Lineage Verified": {"checkbox": {}},
                "Lineage Confidence": {"number": {"format": "percent"}},
                # Epistemic Metadata (7-Question Knowledge Capture Checklist)
                "Observer": {"rich_text": {}},  # Q1: Who knew this
                "Contact Mode": {"select": {
                    "options": [
                        {"name": "direct", "color": "green"},
                        {"name": "mediated", "color": "blue"},
                        {"name": "effect_only", "color": "yellow"},
                        {"name": "derived", "color": "gray"}
                    ]
                }},
                "Contact Strength": {"number": {"format": "number"}},  # Q1: How close
                "Signal Type": {"select": {
                    "options": [
                        {"name": "text", "color": "default"},
                        {"name": "code", "color": "blue"},
                        {"name": "spec", "color": "green"},
                        {"name": "diagram", "color": "purple"},
                        {"name": "model", "color": "orange"}
                    ]
                }},
                "Pattern Storage": {"select": {  # Q2: Where experience lives
                    "options": [
                        {"name": "internalized", "color": "red"},
                        {"name": "externalized", "color": "green"},
                        {"name": "mixed", "color": "yellow"}
                    ]
                }},
                "Scope": {"select": {  # Q4: Context
                    "options": [
                        {"name": "local", "color": "gray"},
                        {"name": "subsystem", "color": "blue"},
                        {"name": "system", "color": "green"},
                        {"name": "general", "color": "purple"}
                    ]
                }},
                "Staleness Risk": {"number": {"format": "percent"}},  # Q5: Temporal validity
                "Intent": {"select": {  # Q6: Authorship intent
                    "options": [
                        {"name": "explain", "color": "blue"},
                        {"name": "instruct", "color": "green"},
                        {"name": "justify", "color": "purple"},
                        {"name": "explore", "color": "yellow"},
                        {"name": "comply", "color": "red"}
                    ]
                }},
                "Reenactment Required": {"checkbox": {}},  # Q7: Practice needed
                "Skill Transferability": {"select": {  # Q7: Can it transfer
                    "options": [
                        {"name": "portable", "color": "green"},
                        {"name": "conditional", "color": "yellow"},
                        {"name": "local", "color": "orange"},
                        {"name": "tacit_like", "color": "red"}
                    ]
                }}
            }
        )
        return database["id"]

    def create_reports_database(self, parent_page_id: str) -> str:
        """Create the Run Reports database in Notion"""
        database = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": "Curator Run Reports"}}],
            properties={
                "Run Date": {"title": {}},  # Title property
                "URLs Processed": {"number": {}},
                "Successful": {"number": {}},
                "Failed": {"number": {}},
                "Total Extractions": {"number": {}},
                "Summary": {"rich_text": {}},
                "LangSmith Trace": {"url": {}},
                "Run ID": {"rich_text": {}}  # For tracking
            }
        )
        return database["id"]

    # =========================================================================
    # PUSH TO NOTION (Errors, Extractions, Reports)
    # =========================================================================

    def log_error(self, url: str, error_message: str, stack_trace: str = None) -> str:
        """Log an error to Notion"""
        if not self.errors_db_id:
            raise ValueError("NOTION_ERRORS_DB_ID not set. Run setup first.")

        properties = {
            "URL": {"title": [{"text": {"content": url[:2000]}}]},  # Notion limit
            "Error Message": {"rich_text": [{"text": {"content": error_message[:2000]}}]},
            "Timestamp": {"date": {"start": datetime.now().isoformat()}},
            "Status": {"select": {"name": "New"}}
        }

        if stack_trace:
            properties["Stack Trace"] = {"rich_text": [{"text": {"content": stack_trace[:2000]}}]}

        page = self.client.pages.create(
            parent={"database_id": self.errors_db_id},
            properties=properties
        )
        return page["id"]

    def sync_extraction(self, extraction_data: Dict[str, Any]) -> str:
        """Push an extraction to Notion for human review with formatted content"""
        if not self.extractions_db_id:
            raise ValueError("NOTION_EXTRACTIONS_DB_ID not set. Run setup first.")

        # Map database status to Notion status
        status_map = {
            'pending': 'Pending',
            'accepted': 'Approved',
            'rejected': 'Rejected',
            'flagged': 'Needs Review'
        }

        # Build properties for database table view
        properties = {
            "Candidate Key": {"title": [{"text": {"content": extraction_data['candidate_key'][:2000]}}]},
            "Type": {"select": {"name": extraction_data['candidate_type']}},
            "Status": {"select": {"name": status_map.get(extraction_data.get('status', 'pending'), 'Pending')}},
            "Extraction ID": {"rich_text": [{"text": {"content": str(extraction_data['extraction_id'])}}]},
            "Created At": {"date": {"start": extraction_data['created_at'].isoformat()}},
            "Confidence Score": {"number": float(extraction_data.get('confidence_score', 0))},
            "Ecosystem": {"select": {"name": extraction_data.get('ecosystem', 'external')}},
            "Lineage Verified": {"checkbox": extraction_data.get('lineage_verified', False)},
        }

        # Get data for content blocks
        evidence = extraction_data.get('evidence', {})
        payload = extraction_data.get('candidate_payload', {})
        evidence_quote = ""
        source_url = ""

        if isinstance(evidence, dict):
            evidence_quote = evidence.get('raw_text', '')
            if 'raw_text' in evidence:
                properties["Evidence Quote"] = {
                    "rich_text": [{"text": {"content": evidence_quote[:2000]}}]
                }

            if 'source_metadata' in evidence:
                source_url = evidence['source_metadata'].get('source_url', '')
                if source_url:
                    properties["Source URL"] = {"url": source_url}

        if extraction_data.get('lineage_confidence') is not None:
            properties["Lineage Confidence"] = {"number": float(extraction_data['lineage_confidence'])}

        # Add epistemic metadata from candidate_payload or top-level fields
        # These come from the 7-Question Knowledge Capture Checklist

        # Q1: Observer coupling
        if payload.get('observer_id'):
            observer_text = f"{payload.get('observer_id', 'unknown')} ({payload.get('observer_type', 'unknown')})"
            properties["Observer"] = {"rich_text": [{"text": {"content": observer_text[:2000]}}]}

        if payload.get('contact_mode'):
            properties["Contact Mode"] = {"select": {"name": payload['contact_mode']}}

        if payload.get('contact_strength') is not None:
            properties["Contact Strength"] = {"number": float(payload['contact_strength'])}

        if payload.get('signal_type'):
            properties["Signal Type"] = {"select": {"name": payload['signal_type']}}

        # Q2: Pattern storage
        if payload.get('pattern_storage'):
            properties["Pattern Storage"] = {"select": {"name": payload['pattern_storage']}}

        # Q4: Context
        if payload.get('scope'):
            properties["Scope"] = {"select": {"name": payload['scope']}}

        # Q5: Temporal validity
        if payload.get('staleness_risk') is not None:
            properties["Staleness Risk"] = {"number": float(payload['staleness_risk'])}

        # Q6: Authorship intent
        if payload.get('intent'):
            properties["Intent"] = {"select": {"name": payload['intent']}}

        # Q7: Reenactment dependency
        if payload.get('reenactment_required') is not None:
            properties["Reenactment Required"] = {"checkbox": bool(payload['reenactment_required'])}

        if payload.get('skill_transferability'):
            properties["Skill Transferability"] = {"select": {"name": payload['skill_transferability']}}

        # Build formatted page content blocks
        children = self._build_extraction_content_blocks(
            extraction_data, payload, evidence_quote, source_url
        )

        # Use data_source_id for API version 2025-09-03
        page = self.client.pages.create(
            parent={"type": "data_source_id", "data_source_id": self.extractions_data_source_id},
            properties=properties,
            children=children
        )
        return page["id"]

    def _build_extraction_content_blocks(
        self,
        extraction_data: Dict[str, Any],
        payload: Dict[str, Any],
        evidence_quote: str,
        source_url: str
    ) -> List[Dict]:
        """Build formatted Notion content blocks for extraction display"""
        import json

        blocks = []

        # 📋 EXTRACTION DETAILS
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📋 EXTRACTION DETAILS"}}]}
        })

        # Show key info based on type
        if extraction_data['candidate_type'] == 'dependency':
            from_comp = payload.get('from_component', 'Unknown')
            to_comp = payload.get('to_component', 'Unknown')
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": f"{from_comp} → {to_comp}"}}]}
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": extraction_data['candidate_key']}}]}
            })

        # 🎯 WHAT WAS EXTRACTED
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🎯 WHAT WAS EXTRACTED"}}]}
        })

        # Format payload as readable bullet points based on extraction type
        if extraction_data['candidate_type'] == 'dependency':
            # Format dependency with FRAMES metadata
            dep_lines = []
            if 'source' in payload:
                dep_lines.append(f"• Source: {payload['source']}")
            if 'target' in payload:
                dep_lines.append(f"• Target: {payload['target']}")
            if 'relationship_type' in payload:
                dep_lines.append(f"• Relationship: {payload['relationship_type']}")
            if 'layer' in payload:
                dep_lines.append(f"• Layer: {payload['layer']}")
            if 'flow' in payload:
                flow_str = ', '.join(payload['flow']) if isinstance(payload['flow'], list) else payload['flow']
                dep_lines.append(f"• Flow: {flow_str}")
            if 'failure_mode' in payload:
                dep_lines.append(f"• Failure Mode: {payload['failure_mode']}")
            if 'maintenance' in payload:
                dep_lines.append(f"• Maintenance: {payload['maintenance']}")
            if 'coupling_strength' in payload:
                dep_lines.append(f"• Coupling Strength: {payload['coupling_strength']}")

            formatted_text = '\n'.join(dep_lines)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": formatted_text[:2000]}}]}
            })
        else:
            # For other types (components, etc.), show key fields as bullets
            lines = []
            for key, value in payload.items():
                if key not in ['observer_id', 'observer_type']:  # Skip observer fields (shown separately)
                    if isinstance(value, (list, dict)):
                        value_str = json.dumps(value)
                    else:
                        value_str = str(value)
                    lines.append(f"• {key}: {value_str}")

            formatted_text = '\n'.join(lines)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": formatted_text[:2000]}}]}
            })

        # 📊 CONFIDENCE ASSESSMENT
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📊 CONFIDENCE ASSESSMENT"}}]}
        })

        conf_score = extraction_data.get('confidence_score', 0)
        conf_reason = extraction_data.get('confidence_reason', 'No reason provided')
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": f"Score: {conf_score:.2f}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": f"Reasoning: {conf_reason[:1000]}"}}]}
        })

        # 📝 EVIDENCE
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📝 EVIDENCE"}}]}
        })

        if evidence_quote:
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [{"text": {"content": evidence_quote[:2000]}}]}
            })

        if source_url:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": f"Source: {source_url}"}}]}
            })

        # ✓ LINEAGE VERIFICATION
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "✓ LINEAGE VERIFICATION"}}]}
        })

        lineage_verified = extraction_data.get('lineage_verified', False)
        lineage_conf = extraction_data.get('lineage_confidence', 0)
        snapshot_id = extraction_data.get('snapshot_id', 'Unknown')

        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Verified: {'✓ Yes' if lineage_verified else '✗ No'}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Confidence: {lineage_conf:.2f}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Snapshot ID: {snapshot_id}"}}]}
        })

        # 🧠 EPISTEMIC METADATA (7-Question Knowledge Capture Checklist)
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🧠 KNOWLEDGE CAPTURE CHECKLIST"}}]}
        })

        # Q1: Who knew this, and how close were they? (Observer coupling)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q1: Who knew this, and how close were they?"}}]}
        })
        observer_id = payload.get('observer_id', 'unknown')
        observer_type = payload.get('observer_type', 'unknown')
        contact_mode = payload.get('contact_mode', 'derived')
        contact_strength = payload.get('contact_strength', 0.20)
        signal_type = payload.get('signal_type', 'text')
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Observer: {observer_id} ({observer_type})"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Contact Mode: {contact_mode}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Contact Strength: {contact_strength:.2f}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Signal Type: {signal_type}"}}]}
        })

        # Q2: Where does the experience live now? (Pattern storage)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q2: Where does the experience live?"}}]}
        })
        pattern_storage = payload.get('pattern_storage', 'externalized')
        representation_media = payload.get('representation_media', ['text'])
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Pattern Storage: {pattern_storage}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Media: {', '.join(representation_media) if isinstance(representation_media, list) else representation_media}"}}]}
        })

        # Q3: What has to stay connected? (Relational integrity)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q3: What has to stay connected?"}}]}
        })
        dependencies = payload.get('dependencies', [])
        sequence_role = payload.get('sequence_role', 'none')
        relational_notes = payload.get('relational_notes', '')
        if dependencies:
            deps_text = ', '.join(dependencies) if isinstance(dependencies, list) else str(dependencies)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Dependencies: {deps_text[:500]}"}}]}
            })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Sequence Role: {sequence_role}"}}]}
        })
        if relational_notes:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Notes: {relational_notes[:500]}"}}]}
            })

        # Q4: Under what conditions was this true? (Context preservation)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q4: Under what conditions was this true?"}}]}
        })
        validity_conditions = payload.get('validity_conditions', {})
        assumptions = payload.get('assumptions', [])
        scope = payload.get('scope', 'subsystem')
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Scope: {scope}"}}]}
        })
        if validity_conditions:
            import json
            conditions_text = json.dumps(validity_conditions, indent=2)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Validity Conditions: {conditions_text[:500]}"}}]}
            })
        if assumptions:
            assumptions_text = ', '.join(assumptions) if isinstance(assumptions, list) else str(assumptions)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Assumptions: {assumptions_text[:500]}"}}]}
            })

        # Q5: When does this stop being reliable? (Temporal validity)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q5: When does this stop being reliable?"}}]}
        })
        observed_at = payload.get('observed_at', 'Unknown')
        valid_from = payload.get('valid_from', '')
        valid_to = payload.get('valid_to', '')
        refresh_trigger = payload.get('refresh_trigger', '')
        staleness_risk = payload.get('staleness_risk', 0.20)
        if observed_at != 'Unknown':
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Observed At: {observed_at}"}}]}
            })
        if valid_from or valid_to:
            validity_range = f"{valid_from} to {valid_to}" if valid_from and valid_to else (valid_from or valid_to)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Valid: {validity_range}"}}]}
            })
        if refresh_trigger:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Refresh Trigger: {refresh_trigger}"}}]}
            })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Staleness Risk: {staleness_risk:.2f}"}}]}
        })

        # Q6: Who wrote or taught this, and why? (Authorship & intent)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q6: Who wrote this, and why?"}}]}
        })
        author_id = payload.get('author_id', 'unknown')
        intent = payload.get('intent', 'instruct')
        uncertainty_notes = payload.get('uncertainty_notes', '')
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Author: {author_id}"}}]}
        })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Intent: {intent}"}}]}
        })
        if uncertainty_notes:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Uncertainty: {uncertainty_notes[:500]}"}}]}
            })

        # Q7: Does this only work if someone keeps doing it? (Reenactment dependency)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "Q7: Does this require practice?"}}]}
        })
        reenactment_required = payload.get('reenactment_required', False)
        practice_interval = payload.get('practice_interval', '')
        skill_transferability = payload.get('skill_transferability', 'portable')
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Reenactment Required: {'Yes' if reenactment_required else 'No'}"}}]}
        })
        if practice_interval:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Practice Interval: {practice_interval}"}}]}
            })
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"Skill Transferability: {skill_transferability}"}}]}
        })

        # FRAMES Metadata (if dependency)
        if extraction_data['candidate_type'] == 'dependency':
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔗 FRAMES COUPLING ANALYSIS"}}]}
            })
            flow = payload.get('flow', [])
            failure_mode = payload.get('failure_mode', 'Unknown')
            maintenance = payload.get('maintenance', 'Unknown')
            coupling_strength = payload.get('coupling_strength', 0.0)
            layer = payload.get('layer', 'unknown')

            flow_text = ', '.join(flow) if isinstance(flow, list) else str(flow)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Q1 - What flows: {flow_text}"}}]}
            })
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Q2 - Failure mode: {failure_mode[:500]}"}}]}
            })
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Q3 - Maintenance: {maintenance[:500]}"}}]}
            })
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Q4 - Coupling strength: {coupling_strength:.2f}"}}]}
            })
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": f"Layer: {layer}"}}]}
            })

        return blocks

    def create_run_report(self, report_data: Dict[str, Any]) -> str:
        """Create a completion report in Notion"""
        if not self.reports_db_id:
            raise ValueError("NOTION_REPORTS_DB_ID not set. Run setup first.")

        properties = {
            "Run Date": {"title": [{"text": {"content": report_data['run_date']}}]},
            "URLs Processed": {"number": report_data['urls_processed']},
            "Successful": {"number": report_data['successful']},
            "Failed": {"number": report_data['failed']},
            "Total Extractions": {"number": report_data.get('total_extractions', 0)},
            "Summary": {"rich_text": [{"text": {"content": report_data.get('summary', '')[:2000]}}]},
        }

        if report_data.get('langsmith_trace'):
            properties["LangSmith Trace"] = {"url": report_data['langsmith_trace']}

        if report_data.get('run_id'):
            properties["Run ID"] = {"rich_text": [{"text": {"content": str(report_data['run_id'])}}]}

        page = self.client.pages.create(
            parent={"database_id": self.reports_db_id},
            properties=properties
        )
        return page["id"]

    # =========================================================================
    # PULL FROM NOTION (Status updates)
    # =========================================================================

    def fetch_updated_extractions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch extractions that have been updated in Notion since a given time.
        Returns list of {extraction_id, new_status} dicts.
        """
        if not self.extractions_db_id:
            raise ValueError("NOTION_EXTRACTIONS_DB_ID not set. Run setup first.")

        # Build filter for recently edited pages
        filter_params = {}
        if since:
            filter_params["filter"] = {
                "timestamp": "last_edited_time",
                "last_edited_time": {
                    "after": since.isoformat()
                }
            }

        # Query database
        results = self.client.databases.query(
            database_id=self.extractions_db_id,
            **filter_params
        )

        # Map Notion status back to database status
        reverse_status_map = {
            'Pending': 'pending',
            'Approved': 'accepted',
            'Rejected': 'rejected',
            'Needs Review': 'flagged'
        }

        updates = []
        for page in results['results']:
            props = page['properties']

            # Extract extraction ID
            extraction_id_prop = props.get('Extraction ID', {})
            if extraction_id_prop.get('rich_text'):
                extraction_id = extraction_id_prop['rich_text'][0]['plain_text']
            else:
                continue  # Skip if no extraction ID

            # Extract status
            status_prop = props.get('Status', {})
            if status_prop.get('select'):
                notion_status = status_prop['select']['name']
                db_status = reverse_status_map.get(notion_status, 'pending')
            else:
                continue  # Skip if no status

            updates.append({
                'extraction_id': extraction_id,
                'new_status': db_status,
                'notion_page_id': page['id'],
                'last_edited_time': page['last_edited_time']
            })

        return updates

    def update_database_status(self, extraction_id: str, new_status: str, review_decision: str = None) -> bool:
        """Update the status of an extraction in the Neon database"""
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                if review_decision:
                    # Update with review tracking
                    cur.execute("""
                        UPDATE staging_extractions
                        SET status = %s::candidate_status,
                            updated_at = NOW(),
                            reviewed_at = NOW(),
                            review_decision = %s
                        WHERE extraction_id = %s::uuid
                        RETURNING extraction_id
                    """, (new_status, review_decision, extraction_id))
                else:
                    # Update without review tracking
                    cur.execute("""
                        UPDATE staging_extractions
                        SET status = %s::candidate_status,
                            updated_at = NOW()
                        WHERE extraction_id = %s::uuid
                        RETURNING extraction_id
                    """, (new_status, extraction_id))

                result = cur.fetchone()
                conn.commit()
            conn.close()

            return result is not None

        except Exception as e:
            print(f"Error updating database status: {e}")
            return False

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    def sync_pending_extractions(self, limit: int = 100) -> int:
        """
        Sync pending extractions from Neon database to Notion.
        Returns count of synced extractions.
        """
        conn = psycopg.connect(self.db_url)
        synced_count = 0

        with conn.cursor() as cur:
            # Fetch pending extractions that haven't been synced to Notion yet
            cur.execute("""
                SELECT
                    extraction_id, candidate_type, candidate_key, status,
                    confidence_score, ecosystem, evidence, created_at,
                    lineage_verified, lineage_confidence
                FROM staging_extractions
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

            rows = cur.fetchall()

            for row in rows:
                extraction_data = {
                    'extraction_id': row[0],
                    'candidate_type': row[1],
                    'candidate_key': row[2],
                    'status': row[3],
                    'confidence_score': row[4],
                    'ecosystem': row[5],
                    'evidence': row[6],
                    'created_at': row[7],
                    'lineage_verified': row[8],
                    'lineage_confidence': row[9]
                }

                try:
                    self.sync_extraction(extraction_data)
                    synced_count += 1
                except Exception as e:
                    print(f"Error syncing extraction {row[0]}: {e}")

        conn.close()
        return synced_count


# ============================================================================
# CLI UTILITIES
# ============================================================================

def setup_notion_databases(parent_page_id: str = None):
    """
    One-time setup: Create the three Notion databases and update .env

    Args:
        parent_page_id: Notion page ID where databases should be created
                       If not provided, will prompt for it
    """
    if not parent_page_id:
        print("Please provide a Notion page ID where the databases should be created.")
        print("To get a page ID:")
        print("1. Open the page in Notion")
        print("2. Click 'Share' → 'Copy link'")
        print("3. Extract the ID from the URL (32-char hex after the page name)")
        print()
        parent_page_id = input("Enter Notion parent page ID: ").strip()

    # Remove dashes if user included them
    parent_page_id = parent_page_id.replace('-', '')

    print("\nCreating Notion databases...")
    sync = NotionSync()

    print("Creating Errors Log database...")
    errors_db_id = sync.create_errors_database(parent_page_id)
    print(f"✓ Errors DB created: {errors_db_id}")

    print("Creating Extractions Review database...")
    extractions_db_id = sync.create_extractions_database(parent_page_id)
    print(f"✓ Extractions DB created: {extractions_db_id}")

    print("Creating Run Reports database...")
    reports_db_id = sync.create_reports_database(parent_page_id)
    print(f"✓ Reports DB created: {reports_db_id}")

    # Update .env file
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')

    print(f"\nUpdating {env_path}...")

    with open(env_path, 'r') as f:
        env_content = f.read()

    env_content = env_content.replace(
        'NOTION_ERRORS_DB_ID=  # Auto-populated by setup script',
        f'NOTION_ERRORS_DB_ID={errors_db_id}'
    )
    env_content = env_content.replace(
        'NOTION_EXTRACTIONS_DB_ID=  # Auto-populated by setup script',
        f'NOTION_EXTRACTIONS_DB_ID={extractions_db_id}'
    )
    env_content = env_content.replace(
        'NOTION_REPORTS_DB_ID=  # Auto-populated by setup script',
        f'NOTION_REPORTS_DB_ID={reports_db_id}'
    )

    with open(env_path, 'w') as f:
        f.write(env_content)

    print("✓ .env file updated")
    print("\n=== Setup Complete ===")
    print(f"\nErrors DB: https://notion.so/{errors_db_id.replace('-', '')}")
    print(f"Extractions DB: https://notion.so/{extractions_db_id.replace('-', '')}")
    print(f"Reports DB: https://notion.so/{reports_db_id.replace('-', '')}")
    print("\nNext steps:")
    print("1. Visit your Notion integration settings")
    print("2. Add these databases to your integration's connections")
    print("3. Run the curator agent - it will now sync to Notion automatically!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        parent_page_id = sys.argv[2] if len(sys.argv) > 2 else None
        setup_notion_databases(parent_page_id)
    else:
        print("Usage: python notion_sync.py setup [parent_page_id]")
