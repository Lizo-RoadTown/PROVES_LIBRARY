"""
PROVES Standard Identifiers

Provides URI and URN formats for entities, enabling:
- Linked data integration (HTTP URIs)
- Internal references (URNs)
- Cross-tool compatibility
- Stable identifiers across exports

URI Format: http://proves.space/{ecosystem}/{entity_type}/{key}
URN Format: urn:proves:{ecosystem}:{entity_type}:{key}

Examples:
    >>> identifier = ProvesIdentifier("component", "cfs-evt", ecosystem="fprime")
    >>> identifier.uri
    'http://proves.space/fprime/component/cfs-evt'
    >>> identifier.urn
    'urn:proves:fprime:component:cfs-evt'
"""

from typing import Optional
import re


class ProvesIdentifier:
    """
    Standard PROVES identifier with URI/URN support.

    Provides stable, globally unique identifiers for PROVES entities
    that can be referenced by external tools and exported to standards
    formats (SysML, XTCE, GraphML, etc.).
    """

    NAMESPACE = "http://proves.space"
    URN_PREFIX = "urn:proves"

    def __init__(self, entity_type: str, key: str, ecosystem: Optional[str] = None):
        """
        Create a PROVES identifier.

        Args:
            entity_type: Type of entity ('component', 'port', 'dependency', etc.)
            key: Unique key within type (will be normalized)
            ecosystem: Optional ecosystem scope ('fprime', 'ros2', 'cubesat', etc.)

        Examples:
            >>> ProvesIdentifier("component", "MSP430 Microcontroller", ecosystem="cubesat")
            ProvesIdentifier(cubesat, component, msp430-microcontroller)
        """
        self.entity_type = entity_type
        self.key = self._normalize_key(key)
        self.ecosystem = ecosystem

    @staticmethod
    def _normalize_key(key: str) -> str:
        """
        Normalize key to URL-safe format.

        Rules:
        1. Convert to lowercase
        2. Replace spaces and underscores with hyphens
        3. Remove special characters (keep only a-z, 0-9, hyphens)
        4. Collapse consecutive hyphens
        5. Strip hyphens from ends

        Args:
            key: Original key string

        Returns:
            Normalized, URL-safe key

        Examples:
            >>> ProvesIdentifier._normalize_key("MSP430 Microcontroller")
            'msp430-microcontroller'
            >>> ProvesIdentifier._normalize_key("CFS_EVT_Handler")
            'cfs-evt-handler'
            >>> ProvesIdentifier._normalize_key("RP2350--UART#Port")
            'rp2350-uart-port'
        """
        # Lowercase
        key = key.lower()

        # Replace spaces and underscores with hyphens
        key = re.sub(r'[\s_]+', '-', key)

        # Remove special characters (keep only alphanumeric and hyphens)
        key = re.sub(r'[^a-z0-9-]', '', key)

        # Collapse consecutive hyphens
        key = re.sub(r'-+', '-', key)

        # Strip hyphens from ends
        key = key.strip('-')

        return key

    @property
    def uri(self) -> str:
        """
        HTTP URI for linked data / web.

        Returns:
            Full HTTP URI in PROVES namespace

        Examples:
            >>> id = ProvesIdentifier("component", "cfs-evt", ecosystem="fprime")
            >>> id.uri
            'http://proves.space/fprime/component/cfs-evt'

            >>> id = ProvesIdentifier("port", "uart-tx")
            >>> id.uri
            'http://proves.space/port/uart-tx'
        """
        if self.ecosystem:
            return f"{self.NAMESPACE}/{self.ecosystem}/{self.entity_type}/{self.key}"
        return f"{self.NAMESPACE}/{self.entity_type}/{self.key}"

    @property
    def urn(self) -> str:
        """
        URN for internal identifiers.

        Returns:
            URN in urn:proves namespace

        Examples:
            >>> id = ProvesIdentifier("component", "cfs-evt", ecosystem="fprime")
            >>> id.urn
            'urn:proves:fprime:component:cfs-evt'

            >>> id = ProvesIdentifier("dependency", "power-link")
            >>> id.urn
            'urn:proves:dependency:power-link'
        """
        if self.ecosystem:
            return f"{self.URN_PREFIX}:{self.ecosystem}:{self.entity_type}:{self.key}"
        return f"{self.URN_PREFIX}:{self.entity_type}:{self.key}"

    @classmethod
    def from_uri(cls, uri: str) -> Optional["ProvesIdentifier"]:
        """
        Parse URI back to identifier.

        Args:
            uri: HTTP URI to parse

        Returns:
            ProvesIdentifier if valid, None otherwise

        Examples:
            >>> uri = "http://proves.space/fprime/component/cfs-evt"
            >>> id = ProvesIdentifier.from_uri(uri)
            >>> id.ecosystem
            'fprime'
            >>> id.entity_type
            'component'
            >>> id.key
            'cfs-evt'
        """
        if not uri.startswith(cls.NAMESPACE):
            return None

        # Remove namespace prefix and leading slash
        path = uri[len(cls.NAMESPACE)+1:]
        parts = path.split('/')

        if len(parts) == 2:
            # Format: /entity_type/key
            return cls(parts[0], parts[1])
        elif len(parts) == 3:
            # Format: /ecosystem/entity_type/key
            return cls(parts[1], parts[2], ecosystem=parts[0])

        return None

    @classmethod
    def from_urn(cls, urn: str) -> Optional["ProvesIdentifier"]:
        """
        Parse URN back to identifier.

        Args:
            urn: URN to parse

        Returns:
            ProvesIdentifier if valid, None otherwise

        Examples:
            >>> urn = "urn:proves:fprime:component:cfs-evt"
            >>> id = ProvesIdentifier.from_urn(urn)
            >>> id.ecosystem
            'fprime'
            >>> id.entity_type
            'component'
            >>> id.key
            'cfs-evt'
        """
        if not urn.startswith(cls.URN_PREFIX):
            return None

        # Remove prefix
        parts = urn[len(cls.URN_PREFIX)+1:].split(':')

        if len(parts) == 2:
            # Format: urn:proves:entity_type:key
            return cls(parts[0], parts[1])
        elif len(parts) == 3:
            # Format: urn:proves:ecosystem:entity_type:key
            return cls(parts[1], parts[2], ecosystem=parts[0])

        return None

    def __str__(self) -> str:
        """String representation (returns URI)"""
        return self.uri

    def __repr__(self) -> str:
        """Debug representation"""
        if self.ecosystem:
            return f"ProvesIdentifier({self.ecosystem}, {self.entity_type}, {self.key})"
        return f"ProvesIdentifier({self.entity_type}, {self.key})"

    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, ProvesIdentifier):
            return False
        return (self.entity_type == other.entity_type and
                self.key == other.key and
                self.ecosystem == other.ecosystem)

    def __hash__(self) -> int:
        """Hash for use in sets/dicts"""
        return hash((self.entity_type, self.key, self.ecosystem))
