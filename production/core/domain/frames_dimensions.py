"""
FRAMES Dimensional Metadata

Represents the 7-question FRAMES epistemic model that captures
socio-organizational provenance of knowledge.

The FRAMES methodology addresses CubeSat mission failures by capturing
not just technical specifications but the context of how knowledge
was produced, transferred, and verified.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FramesDimensions:
    """
    FRAMES 7-question epistemic model (human-verified).

    These dimensions capture the socio-organizational context of knowledge:
    - How was it produced? (knowledge_form)
    - How direct is the evidence? (contact_level)
    - What's the temporal relationship? (directionality)
    - What's the temporal scope? (temporality)
    - Can it be transferred? (formalizability)
    - Where does it reside? (carrier)

    Each dimension has:
    - value: The categorical answer
    - confidence: Human confidence in this classification (0.0-1.0)
    - reasoning: Why this classification was chosen

    This is the core of what makes PROVES different from traditional
    knowledge graphs - we track HOW we know, not just WHAT we know.
    """

    # Question 1: What form does this knowledge take?
    knowledge_form: Optional[str] = None  # 'embodied', 'inferred', 'unknown'
    knowledge_form_confidence: Optional[float] = None
    knowledge_form_reasoning: Optional[str] = None

    # Question 2: How direct is the contact with the source?
    contact_level: Optional[str] = None  # 'direct', 'mediated', 'indirect', 'derived', 'unknown'
    contact_confidence: Optional[float] = None
    contact_reasoning: Optional[str] = None

    # Question 3: What's the temporal relationship between knowledge and events?
    directionality: Optional[str] = None  # 'forward', 'backward', 'bidirectional', 'unknown'
    directionality_confidence: Optional[float] = None
    directionality_reasoning: Optional[str] = None

    # Question 4: What's the temporal scope?
    temporality: Optional[str] = None  # 'snapshot', 'sequence', 'history', 'lifecycle', 'unknown'
    temporality_confidence: Optional[float] = None
    temporality_reasoning: Optional[str] = None

    # Question 5: How transferable is this knowledge?
    formalizability: Optional[str] = None  # 'portable', 'conditional', 'local', 'tacit', 'unknown'
    formalizability_confidence: Optional[float] = None
    formalizability_reasoning: Optional[str] = None

    # Question 6: Where does this knowledge reside?
    carrier: Optional[str] = None  # 'body', 'instrument', 'artifact', 'community', 'machine', 'unknown'
    carrier_confidence: Optional[float] = None
    carrier_reasoning: Optional[str] = None

    def validate(self) -> List[str]:
        """
        Validate dimensional constraints.

        Returns:
            List of error messages (empty if valid)

        Examples:
            >>> dims = FramesDimensions(contact_level='direct', contact_confidence=1.5)
            >>> dims.validate()
            ['contact_confidence must be between 0.0 and 1.0']
        """
        errors = []

        # Validate confidence scores are 0-1
        confidence_fields = [
            'knowledge_form_confidence',
            'contact_confidence',
            'directionality_confidence',
            'temporality_confidence',
            'formalizability_confidence',
            'carrier_confidence',
        ]

        for field in confidence_fields:
            val = getattr(self, field)
            if val is not None and not (0.0 <= val <= 1.0):
                errors.append(f"{field} must be between 0.0 and 1.0, got {val}")

        # Validate value enums
        if self.knowledge_form and self.knowledge_form not in ['embodied', 'inferred', 'unknown']:
            errors.append(f"knowledge_form must be 'embodied', 'inferred', or 'unknown', got '{self.knowledge_form}'")

        if self.contact_level and self.contact_level not in ['direct', 'mediated', 'indirect', 'derived', 'unknown']:
            errors.append(f"contact_level must be one of: direct, mediated, indirect, derived, unknown")

        if self.directionality and self.directionality not in ['forward', 'backward', 'bidirectional', 'unknown']:
            errors.append(f"directionality must be one of: forward, backward, bidirectional, unknown")

        if self.temporality and self.temporality not in ['snapshot', 'sequence', 'history', 'lifecycle', 'unknown']:
            errors.append(f"temporality must be one of: snapshot, sequence, history, lifecycle, unknown")

        if self.formalizability and self.formalizability not in ['portable', 'conditional', 'local', 'tacit', 'unknown']:
            errors.append(f"formalizability must be one of: portable, conditional, local, tacit, unknown")

        if self.carrier and self.carrier not in ['body', 'instrument', 'artifact', 'community', 'machine', 'unknown']:
            errors.append(f"carrier must be one of: body, instrument, artifact, community, machine, unknown")

        return errors

    def is_complete(self) -> bool:
        """
        Check if all dimensions have been assessed.

        Returns:
            True if all dimension values are set
        """
        return all([
            self.knowledge_form is not None,
            self.contact_level is not None,
            self.directionality is not None,
            self.temporality is not None,
            self.formalizability is not None,
            self.carrier is not None,
        ])

    def avg_confidence(self) -> Optional[float]:
        """
        Calculate average confidence across all dimensions.

        Returns:
            Average confidence (0.0-1.0), or None if no confidences set

        Examples:
            >>> dims = FramesDimensions(
            ...     contact_level='direct', contact_confidence=0.9,
            ...     formalizability='portable', formalizability_confidence=0.8
            ... )
            >>> dims.avg_confidence()
            0.85
        """
        confidences = [
            self.knowledge_form_confidence,
            self.contact_confidence,
            self.directionality_confidence,
            self.temporality_confidence,
            self.formalizability_confidence,
            self.carrier_confidence,
        ]

        valid_confidences = [c for c in confidences if c is not None]

        if not valid_confidences:
            return None

        return sum(valid_confidences) / len(valid_confidences)

    def assess_epistemic_risk(self) -> str:
        """
        Assess epistemic risk level based on dimensions.

        High risk conditions:
        - Embodied + tacit/local = knowledge loss risk
        - Indirect/derived + backward = inference cascade risk
        - History/lifecycle without temporal grounding = context missing

        Returns:
            Risk category: 'high_loss_risk', 'inference_cascade_risk',
                          'temporal_context_missing', 'low_risk'

        Examples:
            >>> dims = FramesDimensions(
            ...     knowledge_form='embodied',
            ...     formalizability='tacit'
            ... )
            >>> dims.assess_epistemic_risk()
            'high_loss_risk'
        """
        # High loss risk: Embodied tacit knowledge
        if (self.knowledge_form == 'embodied' and
            self.formalizability in ['tacit', 'local']):
            return 'high_loss_risk'

        # Inference cascade risk: Indirect/derived + backward reasoning
        if (self.contact_level in ['indirect', 'derived'] and
            self.directionality == 'backward'):
            return 'inference_cascade_risk'

        # Temporal context missing: Historical knowledge without grounding
        if self.temporality in ['history', 'lifecycle']:
            # Note: This would ideally check for episode relationships,
            # but that requires database context
            return 'temporal_context_missing'

        return 'low_risk'

    def to_dict(self) -> dict:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation suitable for JSON/JSONB

        Examples:
            >>> dims = FramesDimensions(
            ...     contact_level='direct',
            ...     contact_confidence=0.9
            ... )
            >>> dims.to_dict()
            {'contact_level': 'direct', 'contact_confidence': 0.9, ...}
        """
        return {
            'knowledge_form': self.knowledge_form,
            'knowledge_form_confidence': self.knowledge_form_confidence,
            'knowledge_form_reasoning': self.knowledge_form_reasoning,
            'contact_level': self.contact_level,
            'contact_confidence': self.contact_confidence,
            'contact_reasoning': self.contact_reasoning,
            'directionality': self.directionality,
            'directionality_confidence': self.directionality_confidence,
            'directionality_reasoning': self.directionality_reasoning,
            'temporality': self.temporality,
            'temporality_confidence': self.temporality_confidence,
            'temporality_reasoning': self.temporality_reasoning,
            'formalizability': self.formalizability,
            'formalizability_confidence': self.formalizability_confidence,
            'formalizability_reasoning': self.formalizability_reasoning,
            'carrier': self.carrier,
            'carrier_confidence': self.carrier_confidence,
            'carrier_reasoning': self.carrier_reasoning,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FramesDimensions":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with dimensional metadata

        Returns:
            FramesDimensions instance

        Examples:
            >>> data = {'contact_level': 'direct', 'contact_confidence': 0.9}
            >>> dims = FramesDimensions.from_dict(data)
            >>> dims.contact_level
            'direct'
        """
        return cls(**data)

    def __str__(self) -> str:
        """Human-readable summary"""
        parts = []
        if self.knowledge_form:
            parts.append(f"form={self.knowledge_form}")
        if self.contact_level:
            parts.append(f"contact={self.contact_level}")
        if self.formalizability:
            parts.append(f"formal={self.formalizability}")

        if parts:
            return f"FramesDimensions({', '.join(parts)})"
        return "FramesDimensions(empty)"
