"""
Training Data Logger for PROVES Library Curator Agent

Captures interactions, human feedback, and corrections for fine-tuning local models.
Stores to Neon PostgreSQL for persistence across sessions.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, asdict
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TrainingInteraction:
    """Represents a single curator agent interaction for training data collection."""
    thread_id: str
    session_type: str  # 'extraction', 'validation', 'storage'
    
    # Input
    doc_chunk: Optional[str] = None
    doc_source: Optional[str] = None
    doc_chunk_start_line: Optional[int] = None
    doc_chunk_end_line: Optional[int] = None
    
    # AI output
    ai_extraction: Optional[dict] = None
    ai_raw_response: Optional[str] = None
    model_used: str = "claude-sonnet-4-5"
    
    # Human feedback (filled in later)
    human_decision: Optional[str] = None  # 'approved', 'rejected', 'corrected'
    human_correction: Optional[dict] = None
    correction_reason: Optional[str] = None
    correction_categories: Optional[list[str]] = None
    
    # Performance
    latency_ms: Optional[int] = None
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    
    # Internal
    id: Optional[str] = None
    timestamp: Optional[datetime] = None


class TrainingDataLogger:
    """
    Logs curator agent interactions to Neon PostgreSQL for training data collection.
    
    Usage:
        logger = TrainingDataLogger()
        
        # Log an extraction
        interaction_id = logger.log_interaction(
            thread_id="curator-session-1",
            session_type="extraction",
            doc_chunk="...",
            doc_source="trial_docs/fprime_i2c.md",
            ai_raw_response="Found dependencies: ...",
            model_used="claude-sonnet-4-5",
            latency_ms=2500
        )
        
        # Later, record human feedback
        logger.record_feedback(
            interaction_id=interaction_id,
            decision="corrected",
            correction={"fixed": "output"},
            reason="Wrong criticality level",
            categories=["wrong_criticality"]
        )
        
        # Generate training example
        logger.create_training_example(interaction_id)
    """
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv('NEON_DATABASE_URL')
        if not self.db_url:
            raise ValueError("Database URL not provided and NEON_DATABASE_URL not set")
        self._conn = None
    
    def _get_conn(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url)
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
    
    def log_interaction(
        self,
        thread_id: str,
        session_type: str,
        doc_chunk: Optional[str] = None,
        doc_source: Optional[str] = None,
        doc_chunk_start_line: Optional[int] = None,
        doc_chunk_end_line: Optional[int] = None,
        ai_extraction: Optional[dict] = None,
        ai_raw_response: Optional[str] = None,
        model_used: str = "claude-sonnet-4-5",
        latency_ms: Optional[int] = None,
        token_count_input: Optional[int] = None,
        token_count_output: Optional[int] = None,
    ) -> str:
        """
        Log a new interaction to the database.
        
        Returns:
            interaction_id (UUID as string)
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO training_interactions (
                    thread_id, session_type,
                    doc_chunk, doc_source, doc_chunk_start_line, doc_chunk_end_line,
                    ai_extraction, ai_raw_response, model_used,
                    latency_ms, token_count_input, token_count_output
                ) VALUES (
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                ) RETURNING id
            """, (
                thread_id, session_type,
                doc_chunk, doc_source, doc_chunk_start_line, doc_chunk_end_line,
                Json(ai_extraction) if ai_extraction else None, ai_raw_response, model_used,
                latency_ms, token_count_input, token_count_output
            ))
            
            result = cur.fetchone()
            interaction_id = str(result[0])
            conn.commit()
            
            print(f"[TRAINING] Logged interaction: {interaction_id[:8]}...")
            return interaction_id
            
        except Exception as e:
            conn.rollback()
            print(f"[TRAINING] Error logging interaction: {e}")
            raise
        finally:
            cur.close()
    
    def record_feedback(
        self,
        interaction_id: str,
        decision: str,  # 'approved', 'rejected', 'corrected'
        correction: Optional[dict] = None,
        reason: Optional[str] = None,
        categories: Optional[list[str]] = None
    ) -> None:
        """
        Record human feedback for an interaction.
        
        Args:
            interaction_id: UUID of the interaction
            decision: 'approved', 'rejected', or 'corrected'
            correction: If corrected, the fixed output
            reason: Why the human made this decision
            categories: Tags like 'wrong_criticality', 'missing_dep', etc.
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE training_interactions
                SET 
                    human_decision = %s,
                    human_correction = %s,
                    correction_reason = %s,
                    correction_categories = %s
                WHERE id = %s
            """, (
                decision,
                Json(correction) if correction else None,
                reason,
                categories,
                interaction_id
            ))
            
            conn.commit()
            print(f"[TRAINING] Recorded feedback: {decision} for {interaction_id[:8]}...")
            
        except Exception as e:
            conn.rollback()
            print(f"[TRAINING] Error recording feedback: {e}")
            raise
        finally:
            cur.close()
    
    def create_training_example(
        self,
        interaction_id: str,
        task_type: str = "dependency_extraction"
    ) -> Optional[str]:
        """
        Create a training example from an interaction.
        Uses the PostgreSQL function we defined.
        
        Returns:
            example_id or None if not applicable
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "SELECT create_training_example(%s, %s)",
                (interaction_id, task_type)
            )
            result = cur.fetchone()
            conn.commit()
            
            if result and result[0]:
                example_id = str(result[0])
                print(f"[TRAINING] Created example: {example_id[:8]}...")
                return example_id
            return None
            
        except Exception as e:
            conn.rollback()
            print(f"[TRAINING] Error creating example: {e}")
            raise
        finally:
            cur.close()
    
    def get_stats(self) -> dict:
        """Get training data collection statistics."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT * FROM training_data_summary")
            row = cur.fetchone()
            
            if row:
                return {
                    "total_interactions": row[0],
                    "approved": row[1],
                    "rejected": row[2],
                    "corrected": row[3],
                    "pending": row[4],
                    "training_examples_ready": row[5],
                    "corrections_count": row[6],
                    "lessons_learned": row[7]
                }
            return {}
            
        except Exception as e:
            print(f"[TRAINING] Error getting stats: {e}")
            return {"error": str(e)}
        finally:
            cur.close()
    
    def export_jsonl(
        self,
        output_path: str,
        task_type: Optional[str] = None,
        only_corrections: bool = False
    ) -> int:
        """
        Export training examples to JSONL file for fine-tuning.
        
        Args:
            output_path: Path to write JSONL file
            task_type: Filter by task type (optional)
            only_corrections: Only export human-corrected examples
            
        Returns:
            Number of examples exported
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "SELECT * FROM export_training_jsonl(%s, %s)",
                (task_type, only_corrections)
            )
            rows = cur.fetchall()
            conn.commit()
            
            with open(output_path, 'w') as f:
                for row in rows:
                    f.write(row[0] + '\n')
            
            count = len(rows)
            print(f"[TRAINING] Exported {count} examples to {output_path}")
            return count
            
        except Exception as e:
            conn.rollback()
            print(f"[TRAINING] Error exporting: {e}")
            raise
        finally:
            cur.close()
    
    def log_lesson(
        self,
        lesson_type: str,
        summary: str,
        details: Optional[dict] = None,
        interaction_ids: Optional[list[str]] = None
    ) -> str:
        """
        Log a lesson learned from corrections.
        
        Args:
            lesson_type: 'pattern', 'mistake', 'edge_case'
            summary: Brief description
            details: Structured details
            interaction_ids: Which interactions taught this
            
        Returns:
            lesson_id
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO learning_log (
                    lesson_type, lesson_summary, lesson_details, interaction_ids
                ) VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                lesson_type,
                summary,
                Json(details) if details else None,
                interaction_ids
            ))
            
            result = cur.fetchone()
            lesson_id = str(result[0])
            conn.commit()
            
            print(f"[TRAINING] Logged lesson: {summary[:50]}...")
            return lesson_id
            
        except Exception as e:
            conn.rollback()
            print(f"[TRAINING] Error logging lesson: {e}")
            raise
        finally:
            cur.close()


# Singleton instance for easy import
_logger_instance: Optional[TrainingDataLogger] = None


def get_training_logger() -> TrainingDataLogger:
    """Get the singleton training data logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TrainingDataLogger()
    return _logger_instance
