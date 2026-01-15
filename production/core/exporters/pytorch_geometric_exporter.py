"""
PyTorch Geometric Exporter for PROVES Knowledge Graph.

Exports PROVES entities to PyTorch Geometric Data format for graph neural networks.
Enables GraphSAGE and other GNN models to learn from PROVES knowledge graph.

Key Features:
- FRAMES dimensions encoded as numerical node features
- Relationships encoded as edges with coupling strength
- Stable URI-based node IDs
- Preserves epistemic metadata in node attributes
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from production.core.domain.core_entity import CoreEntity
from production.core.domain.frames_dimensions import FramesDimensions
from production.core.exporters.base_exporter import BaseExporter, ExportResult


class PyTorchGeometricExporter(BaseExporter):
    """
    Export PROVES knowledge graph to PyTorch Geometric format.

    Output format:
    {
        "node_ids": ["uri1", "uri2", ...],
        "node_features": [[f1, f2, ...], [f1, f2, ...], ...],
        "node_labels": ["component", "port", ...],
        "edge_index": [[src_idx, ...], [dst_idx, ...]],
        "edge_attr": [[weight, ...], ...],
        "metadata": {...}
    }

    Node features encode FRAMES dimensions as numerical vectors:
    - Contact confidence (0.0-1.0)
    - Formalizability confidence (0.0-1.0)
    - Knowledge form encoded (0=unknown, 1=embodied, 2=inferred)
    - Contact level encoded (0=unknown, 1=direct, 2=mediated, 3=indirect, 4=derived)
    - Directionality encoded (0=unknown, 1=forward, 2=backward, 3=bidirectional)
    - Temporality encoded (0=unknown, 1=snapshot, 2=sequence, 3=history, 4=lifecycle)
    - Formalizability encoded (0=unknown, 1=portable, 2=conditional, 3=local, 4=tacit)
    - Carrier encoded (0=unknown, 1=body, 2=instrument, 3=artifact, 4=community, 5=machine)
    """

    # Enum encodings for FRAMES dimensions
    KNOWLEDGE_FORM_ENCODING = {
        'unknown': 0,
        'embodied': 1,
        'inferred': 2
    }

    CONTACT_LEVEL_ENCODING = {
        'unknown': 0,
        'direct': 1,
        'mediated': 2,
        'indirect': 3,
        'derived': 4
    }

    DIRECTIONALITY_ENCODING = {
        'unknown': 0,
        'forward': 1,
        'backward': 2,
        'bidirectional': 3
    }

    TEMPORALITY_ENCODING = {
        'unknown': 0,
        'snapshot': 1,
        'sequence': 2,
        'history': 3,
        'lifecycle': 4
    }

    FORMALIZABILITY_ENCODING = {
        'unknown': 0,
        'portable': 1,
        'conditional': 2,
        'local': 3,
        'tacit': 4
    }

    CARRIER_ENCODING = {
        'unknown': 0,
        'body': 1,
        'instrument': 2,
        'artifact': 3,
        'community': 4,
        'machine': 5
    }

    def export(
        self,
        entities: List[CoreEntity],
        output_path: Optional[Path] = None,
        include_metadata: bool = True,
        **kwargs
    ) -> ExportResult:
        """
        Export entities to PyTorch Geometric format.

        Args:
            entities: List of CoreEntity instances
            output_path: Optional JSON file path to save export
            include_metadata: Include FRAMES metadata in output
            **kwargs: Additional options (unused)

        Returns:
            ExportResult with PyG-compatible data
        """
        # Validate entities
        errors = self.validate_entities(entities)
        if errors:
            return ExportResult(
                success=False,
                format='pytorch_geometric',
                errors=errors
            )

        # Filter to exportable entities only
        exportable = self.filter_exportable(entities)
        if not exportable:
            return ExportResult(
                success=False,
                format='pytorch_geometric',
                errors=["No exportable entities found"]
            )

        # Build node features and mappings
        node_ids = []
        node_features = []
        node_labels = []
        node_metadata = []

        for entity in exportable:
            node_ids.append(self.get_entity_uri(entity))
            node_features.append(self._encode_entity_features(entity))
            node_labels.append(entity.entity_type)

            if include_metadata:
                node_metadata.append(self._extract_entity_metadata(entity))

        # Build edge index and attributes from relationships
        edge_index, edge_attr = self._extract_edges(exportable)

        # Create export data
        export_data = {
            'node_ids': node_ids,
            'node_features': node_features,
            'node_labels': node_labels,
            'edge_index': edge_index,
            'edge_attr': edge_attr,
            'feature_names': self._get_feature_names(),
            'num_nodes': len(node_ids),
            'num_edges': len(edge_index[0]) if edge_index[0] else 0
        }

        if include_metadata:
            export_data['node_metadata'] = node_metadata

        # Save to file if requested
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)

        return ExportResult(
            success=True,
            format='pytorch_geometric',
            output_path=output_path,
            data=export_data,
            entity_count=len(exportable),
            metadata={
                'num_nodes': len(node_ids),
                'num_edges': len(edge_index[0]) if edge_index[0] else 0,
                'feature_dim': len(node_features[0]) if node_features else 0
            }
        )

    def _encode_entity_features(self, entity: CoreEntity) -> List[float]:
        """
        Encode entity as numerical feature vector.

        Args:
            entity: CoreEntity instance

        Returns:
            Feature vector [contact_conf, formal_conf, knowledge_form, contact, dir, temp, formal, carrier]
        """
        dims = entity.dimensions

        if dims is None:
            # No FRAMES dimensions - return zero vector
            return [0.0] * 8

        return [
            dims.contact_confidence or 0.0,
            dims.formalizability_confidence or 0.0,
            float(self.KNOWLEDGE_FORM_ENCODING.get(dims.knowledge_form or 'unknown', 0)),
            float(self.CONTACT_LEVEL_ENCODING.get(dims.contact_level or 'unknown', 0)),
            float(self.DIRECTIONALITY_ENCODING.get(dims.directionality or 'unknown', 0)),
            float(self.TEMPORALITY_ENCODING.get(dims.temporality or 'unknown', 0)),
            float(self.FORMALIZABILITY_ENCODING.get(dims.formalizability or 'unknown', 0)),
            float(self.CARRIER_ENCODING.get(dims.carrier or 'unknown', 0))
        ]

    def _extract_entity_metadata(self, entity: CoreEntity) -> Dict[str, Any]:
        """
        Extract entity metadata for debugging/analysis.

        Args:
            entity: CoreEntity instance

        Returns:
            Dictionary of metadata
        """
        return {
            'uri': self.get_entity_uri(entity),
            'urn': self.get_entity_urn(entity),
            'canonical_key': entity.canonical_key,
            'name': entity.name,
            'ecosystem': entity.ecosystem,
            'entity_type': entity.entity_type,
            'verification_status': entity.verification_status,
            'epistemic_risk': entity.get_epistemic_risk() if entity.dimensions else 'no_dimensions'
        }

    def _extract_edges(
        self,
        entities: List[CoreEntity]
    ) -> Tuple[List[List[int]], List[List[float]]]:
        """
        Extract edges from entity relationships.

        Args:
            entities: List of CoreEntity instances

        Returns:
            Tuple of (edge_index, edge_attr)
            - edge_index: [[source_idx, ...], [target_idx, ...]]
            - edge_attr: [[weight, ...], ...]

        Note:
            Currently returns empty edges. This will be populated when
            relationship extraction is implemented in the domain model.
        """
        # Build URI to index mapping
        uri_to_idx = {
            self.get_entity_uri(e): i
            for i, e in enumerate(entities)
        }

        source_indices = []
        target_indices = []
        edge_weights = []

        # TODO: Extract relationships from entity.attributes or separate relationship table
        # For now, return empty edge structure
        # This will be populated when relationship model is implemented

        return [source_indices, target_indices], [edge_weights]

    def _get_feature_names(self) -> List[str]:
        """
        Get names of features in feature vector.

        Returns:
            List of feature names in order
        """
        return [
            'contact_confidence',
            'formalizability_confidence',
            'knowledge_form_encoded',
            'contact_level_encoded',
            'directionality_encoded',
            'temporality_encoded',
            'formalizability_encoded',
            'carrier_encoded'
        ]
