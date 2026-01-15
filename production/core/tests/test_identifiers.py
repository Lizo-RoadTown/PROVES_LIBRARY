"""
Tests for PROVES identifier system.

Validates:
- URI/URN generation
- Key normalization
- Parsing from URI/URN strings
- Equality and hashing
"""

import pytest
from production.core.identifiers import ProvesIdentifier


class TestKeyNormalization:
    """Test key normalization to URL-safe format"""

    def test_normalize_simple_key(self):
        """Simple alphanumeric keys should lowercase"""
        assert ProvesIdentifier._normalize_key("TestDriver") == "testdriver"
        assert ProvesIdentifier._normalize_key("MSP430") == "msp430"

    def test_normalize_spaces_to_hyphens(self):
        """Spaces should become hyphens"""
        assert ProvesIdentifier._normalize_key("MSP430 Microcontroller") == "msp430-microcontroller"
        assert ProvesIdentifier._normalize_key("Flight Computer") == "flight-computer"

    def test_normalize_underscores_to_hyphens(self):
        """Underscores should become hyphens"""
        assert ProvesIdentifier._normalize_key("CFS_EVT_Handler") == "cfs-evt-handler"
        assert ProvesIdentifier._normalize_key("uart_tx_port") == "uart-tx-port"

    def test_normalize_mixed_separators(self):
        """Mixed spaces and underscores should normalize"""
        assert ProvesIdentifier._normalize_key("MSP430 UART_Handler") == "msp430-uart-handler"

    def test_normalize_special_characters_removed(self):
        """Special characters should be removed"""
        assert ProvesIdentifier._normalize_key("RP2350#UART@Port") == "rp2350uartport"
        assert ProvesIdentifier._normalize_key("CFS-EVT/Handler") == "cfs-evthandler"

    def test_normalize_consecutive_hyphens_collapsed(self):
        """Multiple consecutive hyphens should collapse to one"""
        assert ProvesIdentifier._normalize_key("RP2350--UART---Port") == "rp2350-uart-port"

    def test_normalize_strip_leading_trailing_hyphens(self):
        """Leading and trailing hyphens should be stripped"""
        assert ProvesIdentifier._normalize_key("-uart-port-") == "uart-port"
        assert ProvesIdentifier._normalize_key("--test--") == "test"

    def test_normalize_complex_real_world_cases(self):
        """Real-world entity names"""
        assert ProvesIdentifier._normalize_key("MSP430FR-RP2350 UART Connection") == "msp430fr-rp2350-uart-connection"
        assert ProvesIdentifier._normalize_key("FaceBoards_to_FlightController_SensorData") == "faceboards-to-flightcontroller-sensordata"
        assert ProvesIdentifier._normalize_key("battery_board_led_driver_dependency") == "battery-board-led-driver-dependency"


class TestURIGeneration:
    """Test HTTP URI generation"""

    def test_uri_without_ecosystem(self):
        """URI without ecosystem should omit ecosystem segment"""
        id = ProvesIdentifier("component", "test-driver")
        assert id.uri == "http://proves.space/component/test-driver"

    def test_uri_with_ecosystem(self):
        """URI with ecosystem should include ecosystem segment"""
        id = ProvesIdentifier("component", "cfs-evt", ecosystem="fprime")
        assert id.uri == "http://proves.space/fprime/component/cfs-evt"

    def test_uri_normalizes_key(self):
        """URI should use normalized key"""
        id = ProvesIdentifier("component", "MSP430 Microcontroller", ecosystem="cubesat")
        assert id.uri == "http://proves.space/cubesat/component/msp430-microcontroller"

    def test_str_returns_uri(self):
        """str() should return URI"""
        id = ProvesIdentifier("port", "uart-tx", ecosystem="fprime")
        assert str(id) == "http://proves.space/fprime/port/uart-tx"


class TestURNGeneration:
    """Test URN generation"""

    def test_urn_without_ecosystem(self):
        """URN without ecosystem should omit ecosystem"""
        id = ProvesIdentifier("dependency", "power-link")
        assert id.urn == "urn:proves:dependency:power-link"

    def test_urn_with_ecosystem(self):
        """URN with ecosystem should include ecosystem"""
        id = ProvesIdentifier("component", "cfs-evt", ecosystem="fprime")
        assert id.urn == "urn:proves:fprime:component:cfs-evt"

    def test_urn_normalizes_key(self):
        """URN should use normalized key"""
        id = ProvesIdentifier("port", "UART TX Port", ecosystem="ros2")
        assert id.urn == "urn:proves:ros2:port:uart-tx-port"


class TestURIParsing:
    """Test parsing URIs back to identifiers"""

    def test_parse_uri_without_ecosystem(self):
        """Should parse URI without ecosystem"""
        uri = "http://proves.space/component/test-driver"
        id = ProvesIdentifier.from_uri(uri)

        assert id is not None
        assert id.entity_type == "component"
        assert id.key == "test-driver"
        assert id.ecosystem is None

    def test_parse_uri_with_ecosystem(self):
        """Should parse URI with ecosystem"""
        uri = "http://proves.space/fprime/component/cfs-evt"
        id = ProvesIdentifier.from_uri(uri)

        assert id is not None
        assert id.ecosystem == "fprime"
        assert id.entity_type == "component"
        assert id.key == "cfs-evt"

    def test_parse_invalid_namespace(self):
        """Should return None for wrong namespace"""
        uri = "http://example.com/component/test"
        id = ProvesIdentifier.from_uri(uri)
        assert id is None

    def test_parse_invalid_structure(self):
        """Should return None for invalid structure"""
        uri = "http://proves.space/only-one-segment"
        id = ProvesIdentifier.from_uri(uri)
        assert id is None

    def test_parse_roundtrip_without_ecosystem(self):
        """URI should roundtrip without ecosystem"""
        original = ProvesIdentifier("component", "test-driver")
        parsed = ProvesIdentifier.from_uri(original.uri)

        assert parsed == original

    def test_parse_roundtrip_with_ecosystem(self):
        """URI should roundtrip with ecosystem"""
        original = ProvesIdentifier("port", "uart-tx", ecosystem="fprime")
        parsed = ProvesIdentifier.from_uri(original.uri)

        assert parsed == original


class TestURNParsing:
    """Test parsing URNs back to identifiers"""

    def test_parse_urn_without_ecosystem(self):
        """Should parse URN without ecosystem"""
        urn = "urn:proves:dependency:power-link"
        id = ProvesIdentifier.from_urn(urn)

        assert id is not None
        assert id.entity_type == "dependency"
        assert id.key == "power-link"
        assert id.ecosystem is None

    def test_parse_urn_with_ecosystem(self):
        """Should parse URN with ecosystem"""
        urn = "urn:proves:fprime:component:cfs-evt"
        id = ProvesIdentifier.from_urn(urn)

        assert id is not None
        assert id.ecosystem == "fprime"
        assert id.entity_type == "component"
        assert id.key == "cfs-evt"

    def test_parse_invalid_prefix(self):
        """Should return None for wrong prefix"""
        urn = "urn:isbn:component:test"
        id = ProvesIdentifier.from_urn(urn)
        assert id is None

    def test_parse_invalid_structure(self):
        """Should return None for invalid structure"""
        urn = "urn:proves:only-one-segment"
        id = ProvesIdentifier.from_urn(urn)
        assert id is None

    def test_parse_roundtrip_without_ecosystem(self):
        """URN should roundtrip without ecosystem"""
        original = ProvesIdentifier("component", "test-driver")
        parsed = ProvesIdentifier.from_urn(original.urn)

        assert parsed == original

    def test_parse_roundtrip_with_ecosystem(self):
        """URN should roundtrip with ecosystem"""
        original = ProvesIdentifier("port", "uart-tx", ecosystem="fprime")
        parsed = ProvesIdentifier.from_urn(original.urn)

        assert parsed == original


class TestEqualityAndHashing:
    """Test equality comparison and hashing"""

    def test_equality_same_values(self):
        """Identifiers with same values should be equal"""
        id1 = ProvesIdentifier("component", "test-driver", ecosystem="fprime")
        id2 = ProvesIdentifier("component", "test-driver", ecosystem="fprime")

        assert id1 == id2

    def test_equality_different_keys(self):
        """Identifiers with different keys should not be equal"""
        id1 = ProvesIdentifier("component", "test-driver")
        id2 = ProvesIdentifier("component", "other-driver")

        assert id1 != id2

    def test_equality_different_types(self):
        """Identifiers with different types should not be equal"""
        id1 = ProvesIdentifier("component", "test-driver")
        id2 = ProvesIdentifier("port", "test-driver")

        assert id1 != id2

    def test_equality_different_ecosystems(self):
        """Identifiers with different ecosystems should not be equal"""
        id1 = ProvesIdentifier("component", "test", ecosystem="fprime")
        id2 = ProvesIdentifier("component", "test", ecosystem="ros2")

        assert id1 != id2

    def test_equality_with_none_ecosystem(self):
        """Identifier with ecosystem should not equal one without"""
        id1 = ProvesIdentifier("component", "test", ecosystem="fprime")
        id2 = ProvesIdentifier("component", "test")

        assert id1 != id2

    def test_hashing_consistent(self):
        """Hash should be consistent for same identifier"""
        id1 = ProvesIdentifier("component", "test-driver", ecosystem="fprime")
        id2 = ProvesIdentifier("component", "test-driver", ecosystem="fprime")

        assert hash(id1) == hash(id2)

    def test_hashing_in_set(self):
        """Identifiers should work correctly in sets"""
        id1 = ProvesIdentifier("component", "test-driver")
        id2 = ProvesIdentifier("component", "test-driver")
        id3 = ProvesIdentifier("component", "other-driver")

        id_set = {id1, id2, id3}
        assert len(id_set) == 2  # id1 and id2 should deduplicate

    def test_hashing_in_dict(self):
        """Identifiers should work correctly as dict keys"""
        id1 = ProvesIdentifier("component", "test-driver")
        id2 = ProvesIdentifier("component", "test-driver")

        data = {id1: "value1"}
        data[id2] = "value2"

        assert len(data) == 1  # id1 and id2 are same key
        assert data[id1] == "value2"


class TestRepr:
    """Test debug representation"""

    def test_repr_without_ecosystem(self):
        """repr() should show all components without ecosystem"""
        id = ProvesIdentifier("component", "test-driver")
        assert repr(id) == "ProvesIdentifier(component, test-driver)"

    def test_repr_with_ecosystem(self):
        """repr() should show ecosystem when present"""
        id = ProvesIdentifier("component", "test-driver", ecosystem="fprime")
        assert repr(id) == "ProvesIdentifier(fprime, component, test-driver)"


class TestRealWorldCases:
    """Test with real entity names from the database"""

    def test_testdriver_component(self):
        """TestDriver component from FPrime"""
        id = ProvesIdentifier("component", "TestDriver", ecosystem="fprime")

        assert id.key == "testdriver"
        assert id.uri == "http://proves.space/fprime/component/testdriver"
        assert id.urn == "urn:proves:fprime:component:testdriver"

    def test_flight_computer_power_dependency(self):
        """flight_computer_power_dependency from proveskit"""
        id = ProvesIdentifier("dependency", "flight_computer_power_dependency", ecosystem="proveskit")

        assert id.key == "flight-computer-power-dependency"
        assert id.uri == "http://proves.space/proveskit/dependency/flight-computer-power-dependency"

    def test_msp430_rp2350_uart_connection(self):
        """MSP430FR-RP2350 UART Connection port"""
        id = ProvesIdentifier("port", "MSP430FR-RP2350 UART Connection", ecosystem="proveskit")

        assert id.key == "msp430fr-rp2350-uart-connection"
        assert id.uri == "http://proves.space/proveskit/port/msp430fr-rp2350-uart-connection"

    def test_faceboards_to_flightcontroller_sensordata(self):
        """FaceBoards_to_FlightController_SensorData dependency"""
        id = ProvesIdentifier("dependency", "FaceBoards_to_FlightController_SensorData", ecosystem="proveskit")

        assert id.key == "faceboards-to-flightcontroller-sensordata"
        assert id.urn == "urn:proves:proveskit:dependency:faceboards-to-flightcontroller-sensordata"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
