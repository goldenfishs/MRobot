"""MCode public API.

All front ends (CLI, MRobot GUI, editor extensions and AI tools) should call
this package instead of implementing generation logic themselves.
"""

from .models import Diagnostic, GenerationPlan, PackageManifest, ProjectModel
from .service import MCodeService

__all__ = [
    "Diagnostic",
    "GenerationPlan",
    "MCodeService",
    "PackageManifest",
    "ProjectModel",
]

__version__ = "0.1.0"
