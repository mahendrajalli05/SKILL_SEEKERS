"""Geospatial Consistency V1.

Location consistency between reported image GPS and available project
coordinates. Satellite imagery is not downloaded or processed.
"""

from app.engines.geo.constants import ENGINE_NAME, ENGINE_VERSION

__all__ = ["ENGINE_NAME", "ENGINE_VERSION"]
