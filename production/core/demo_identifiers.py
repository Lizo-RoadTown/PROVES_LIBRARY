"""
Demo: PROVES Identifier System

Shows how identifiers work with real entity names from the database.
Run: python production/core/demo_identifiers.py
"""

from identifiers import ProvesIdentifier


def demo_basic_usage():
    """Basic identifier creation and formatting"""
    print("=" * 70)
    print("BASIC USAGE")
    print("=" * 70)

    # Create identifier
    id = ProvesIdentifier("component", "TestDriver", ecosystem="fprime")

    print(f"\nOriginal key: 'TestDriver'")
    print(f"Normalized:   '{id.key}'")
    print(f"URI:          {id.uri}")
    print(f"URN:          {id.urn}")
    print(f"Repr:         {repr(id)}")


def demo_key_normalization():
    """Show key normalization with various inputs"""
    print("\n" + "=" * 70)
    print("KEY NORMALIZATION")
    print("=" * 70)

    test_cases = [
        "MSP430 Microcontroller",
        "CFS_EVT_Handler",
        "RP2350--UART#Port",
        "FaceBoards_to_FlightController_SensorData",
        "battery_board_led_driver_dependency",
    ]

    for original in test_cases:
        id = ProvesIdentifier("component", original, ecosystem="test")
        print(f"\n'{original}'")
        print(f"  -> '{id.key}'")


def demo_real_entities():
    """Real entities from the PROVES database"""
    print("\n" + "=" * 70)
    print("REAL ENTITIES FROM DATABASE")
    print("=" * 70)

    entities = [
        ("component", "TestDriver", "fprime"),
        ("dependency", "flight_computer_power_dependency", "proveskit"),
        ("port", "MSP430FR-RP2350 UART Connection", "proveskit"),
        ("dependency", "FaceBoards_to_FlightController_SensorData", "proveskit"),
    ]

    for entity_type, key, ecosystem in entities:
        id = ProvesIdentifier(entity_type, key, ecosystem=ecosystem)
        print(f"\n{entity_type.upper()}: {key}")
        print(f"  URI: {id.uri}")
        print(f"  URN: {id.urn}")


def demo_parsing():
    """Parse URIs and URNs back to identifiers"""
    print("\n" + "=" * 70)
    print("PARSING URIs AND URNs")
    print("=" * 70)

    # Create original
    original = ProvesIdentifier("component", "CFS-EVT", ecosystem="fprime")

    # Roundtrip via URI
    uri = original.uri
    from_uri = ProvesIdentifier.from_uri(uri)

    print(f"\nOriginal: {repr(original)}")
    print(f"URI:      {uri}")
    print(f"Parsed:   {repr(from_uri)}")
    print(f"Equal:    {original == from_uri}")

    # Roundtrip via URN
    urn = original.urn
    from_urn = ProvesIdentifier.from_urn(urn)

    print(f"\nOriginal: {repr(original)}")
    print(f"URN:      {urn}")
    print(f"Parsed:   {repr(from_urn)}")
    print(f"Equal:    {original == from_urn}")


def demo_collections():
    """Using identifiers in sets and dicts"""
    print("\n" + "=" * 70)
    print("COLLECTIONS (Sets and Dicts)")
    print("=" * 70)

    # Create some identifiers
    id1 = ProvesIdentifier("component", "TestDriver", ecosystem="fprime")
    id2 = ProvesIdentifier("component", "TestDriver", ecosystem="fprime")  # Duplicate
    id3 = ProvesIdentifier("component", "CFS-EVT", ecosystem="fprime")

    # Use in set (duplicates removed)
    id_set = {id1, id2, id3}
    print(f"\nCreated 3 identifiers (2 duplicates)")
    print(f"Set size: {len(id_set)}")
    print("Set contents:")
    for id in id_set:
        print(f"  - {id.key}")

    # Use as dict keys
    metadata = {
        id1: {"description": "Test driver component", "verified": True},
        id3: {"description": "Event handler", "verified": False},
    }

    print(f"\nDict with {len(metadata)} entries:")
    for id, meta in metadata.items():
        print(f"  {id.key}: {meta}")


if __name__ == "__main__":
    demo_basic_usage()
    demo_key_normalization()
    demo_real_entities()
    demo_parsing()
    demo_collections()

    print("\n" + "=" * 70)
    print("✓ Identifier system ready for integration")
    print("=" * 70)
