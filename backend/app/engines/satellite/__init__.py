"""Satellite / Remote-Sensing Consistency V1.

Compares a claimed site with available remote-sensing imagery metadata
when a provider can actually supply it. Does not fabricate imagery.
Does not modify Risk Fusion V1.1.
"""

from app.engines.satellite.constants import ENGINE_NAME, ENGINE_VERSION

__all__ = ["ENGINE_NAME", "ENGINE_VERSION"]
