"""Source registry loader for pre-mapped knowledge locations."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from proves_mcp.config import settings

logger = logging.getLogger(__name__)


class SourceRegistry:
    """
    Pre-mapped locations for agent knowledge extraction.
    
    Agents use this to know WHERE to look for information
    without needing to discover it at query time.
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or settings.source_registry_path
        self._data: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> None:
        """Load the source registry from YAML file."""
        if self._loaded:
            return
        
        if not self.registry_path.exists():
            logger.warning(f"Source registry not found at {self.registry_path}")
            self._data = {}
            return
        
        with open(self.registry_path, 'r') as f:
            self._data = yaml.safe_load(f)
        
        self._loaded = True
        logger.info(f"Loaded source registry from {self.registry_path}")
    
    @property
    def fprime(self) -> Dict[str, Any]:
        """Get F' framework configuration."""
        self.load()
        return self._data.get('fprime', {})
    
    @property
    def proveskit(self) -> Dict[str, Any]:
        """Get ProvesKit configuration."""
        self.load()
        return self._data.get('proveskit', {})
    
    @property
    def query_mappings(self) -> Dict[str, Any]:
        """Get query-to-path mappings."""
        self.load()
        return self._data.get('query_mappings', {})
    
    def get_component_path(self, component_name: str) -> Optional[str]:
        """
        Get the file path for a component.
        
        Args:
            component_name: Name of the component (e.g., "command_dispatcher")
            
        Returns:
            Path to the component in F' or ProvesKit
        """
        self.load()
        
        # Check F' components
        fprime_components = self.fprime.get('components', {})
        if component_name in fprime_components:
            return fprime_components[component_name].get('path')
        
        # Check ProvesKit hardware
        proveskit_hardware = self.proveskit.get('hardware', {})
        if component_name in proveskit_hardware:
            return proveskit_hardware[component_name].get('fprime_driver')
        
        return None
    
    def get_search_paths(self, topic: str) -> Dict[str, List[str]]:
        """
        Get paths to search for a given topic.
        
        Args:
            topic: Topic to search for (e.g., "i2c", "scheduling")
            
        Returns:
            Dict with fprime_paths and proveskit_paths
        """
        self.load()
        
        # Check query mappings
        if topic in self.query_mappings:
            mapping = self.query_mappings[topic]
            return {
                'fprime_paths': mapping.get('fprime_paths', []),
                'proveskit_paths': mapping.get('proveskit_paths', []),
                'keywords': mapping.get('keywords', [])
            }
        
        # Check risk areas
        risk_areas = self.fprime.get('risk_areas', {})
        if topic in risk_areas:
            area = risk_areas[topic]
            return {
                'fprime_paths': area.get('search_paths', []),
                'proveskit_paths': [],
                'keywords': area.get('keywords', [])
            }
        
        return {'fprime_paths': [], 'proveskit_paths': [], 'keywords': []}
    
    def get_hardware_info(self, hardware_name: str) -> Optional[Dict[str, Any]]:
        """
        Get hardware component information.
        
        Args:
            hardware_name: Name of hardware (e.g., "rtc_rv3032", "ms5611")
            
        Returns:
            Hardware info including I2C address, driver, conflicts
        """
        self.load()
        
        hardware = self.proveskit.get('hardware', {})
        
        # Direct match
        if hardware_name in hardware:
            return hardware[hardware_name]
        
        # Fuzzy match
        for key, info in hardware.items():
            if hardware_name.lower() in key.lower():
                return info
            if 'description' in info and hardware_name.lower() in info['description'].lower():
                return info
        
        return None
    
    def get_fprime_repo_url(self) -> str:
        """Get F' repository URL."""
        self.load()
        return self.fprime.get('docs', {}).get('repo', 'github.com/nasa/fprime')
    
    def get_proveskit_repos(self) -> Dict[str, Dict[str, Any]]:
        """Get all ProvesKit repository configurations."""
        self.load()
        return self.proveskit.get('repos', {})
    
    def find_matching_topics(self, query: str) -> List[str]:
        """
        Find topics that match a query string.
        
        Args:
            query: User query string
            
        Returns:
            List of matching topic names from query_mappings
        """
        self.load()
        
        query_lower = query.lower()
        matches = []
        
        for topic, mapping in self.query_mappings.items():
            keywords = mapping.get('keywords', [])
            if any(kw in query_lower for kw in keywords):
                matches.append(topic)
        
        return matches


# Singleton instance
registry = SourceRegistry()
