"""
OpenTelemetry tracing configuration for PROVES Curator Agent

This module sets up tracing for the agent framework with AI Toolkit support.
Traces are sent to the local OTLP collector (http://localhost:4317 for gRPC).

Usage:
    from src.curator.tracing import setup_tracing
    setup_tracing()  # Call once at app startup
"""

import os
from typing import Optional


def setup_tracing(
    otlp_endpoint: Optional[str] = None,
    enable_sensitive_data: bool = True,
    service_name: str = "curator-agent"
) -> None:
    """
    Set up OpenTelemetry tracing for the curator agent.
    
    Args:
        otlp_endpoint: OTLP collector endpoint. Defaults to AI Toolkit gRPC (http://localhost:4317)
        enable_sensitive_data: Whether to capture prompts/completions in traces
        service_name: Service name for traces
    
    Example:
        setup_tracing()  # Use defaults (AI Toolkit)
        setup_tracing(otlp_endpoint="http://localhost:4318")  # Custom HTTP endpoint
    """
    if otlp_endpoint is None:
        # Default to AI Toolkit's gRPC endpoint
        otlp_endpoint = "http://localhost:4317"
    
    try:
        # Import agent framework observability
        from agent_framework.observability import setup_observability
        
        setup_observability(
            otlp_endpoint=otlp_endpoint,
            enable_sensitive_data=enable_sensitive_data
        )
        
        print(f"✓ OpenTelemetry tracing enabled")
        print(f"  Endpoint: {otlp_endpoint}")
        print(f"  Service: {service_name}")
        if enable_sensitive_data:
            print(f"  Sensitive data: Captured (prompts/completions included)")
        
    except ImportError as e:
        print(f"⚠ Warning: Could not import agent_framework.observability: {e}")
        print(f"  Make sure 'agent-framework' is installed: pip install agent-framework")
        return
    except Exception as e:
        print(f"⚠ Warning: Failed to set up tracing: {e}")
        return


def is_tracing_enabled() -> bool:
    """Check if tracing was successfully initialized."""
    try:
        from opentelemetry.trace import get_tracer
        return get_tracer(__name__) is not None
    except Exception:
        return False
