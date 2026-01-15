"""
Demo: Export PROVES entities to PyTorch Geometric format.

Shows how to use the PyTorchGeometricExporter to export verified entities
for use with graph neural networks like GraphSAGE.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
version3_path = project_root / 'production' / 'Version 3'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(version3_path))

from production.core.repositories.postgres_core_entity_repository import PostgresCoreEntityRepository
from production.core.exporters.pytorch_geometric_exporter import PyTorchGeometricExporter


def main():
    """Export verified entities to PyTorch Geometric format"""

    print("=" * 60)
    print("PROVES -> PyTorch Geometric Export Demo")
    print("=" * 60)
    print()

    # Initialize repository
    print("1. Loading verified entities from database...")
    repo = PostgresCoreEntityRepository()

    # Get all verified entities
    entities = repo.find_verified(limit=100)
    print(f"   Found {len(entities)} verified entities")

    if not entities:
        print("\n[WARNING] No verified entities found in database.")
        print("          Run extraction and promotion first.")
        return

    print()

    # Export to PyTorch Geometric format
    print("2. Exporting to PyTorch Geometric format...")
    exporter = PyTorchGeometricExporter()

    result = exporter.export(
        entities,
        output_path=Path('exports/proves_graph_pyg.json'),
        include_metadata=True
    )

    if result.success:
        print(f"   [SUCCESS] Export successful!")
        print(f"   Exported {result.entity_count} entities")
        print(f"   Output: {result.output_path}")
        print()
        print("   Export metadata:")
        for key, value in result.metadata.items():
            print(f"      {key}: {value}")

        # Show sample features
        if result.data and result.data['node_features']:
            print()
            print("   Sample node features (first entity):")
            feature_names = result.data['feature_names']
            features = result.data['node_features'][0]
            for name, value in zip(feature_names, features):
                print(f"      {name}: {value}")

    else:
        print(f"   [FAILED] Export failed:")
        for error in result.errors:
            print(f"      - {error}")

    print()
    print("=" * 60)
    print("Next steps:")
    print("  1. Load exported JSON in Python:")
    print("     import json")
    print("     with open('exports/proves_graph_pyg.json') as f:")
    print("         data = json.load(f)")
    print()
    print("  2. Convert to PyTorch Geometric Data object:")
    print("     import torch")
    print("     from torch_geometric.data import Data")
    print("     pyg_data = Data(")
    print("         x=torch.tensor(data['node_features'], dtype=torch.float),")
    print("         edge_index=torch.tensor(data['edge_index'], dtype=torch.long)")
    print("     )")
    print()
    print("  3. Train GraphSAGE or other GNN model on the graph")
    print("=" * 60)


if __name__ == '__main__':
    main()
