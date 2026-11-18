"""Orca Box Studio — offline enclosure design, calibration and export."""

from .schema import DEFAULT_PARAMS, SCHEMA_VERSION, normalize_params, validate_params
from .mesh_generator import (
    MeshData,
    generate_box_mesh,
    generate_fit_test_kit,
    collect_target_meshes,
    topology_report,
)
from .plugin_main import (
    OrcaBoxStudioPlugin,
    BoxStudioPageCapability,
    BoxStudioDockCapability,
    BoxStudioController,
)

__version__ = "1.2.0"
__all__ = [
    "DEFAULT_PARAMS",
    "SCHEMA_VERSION",
    "normalize_params",
    "validate_params",
    "MeshData",
    "generate_box_mesh",
    "generate_fit_test_kit",
    "collect_target_meshes",
    "topology_report",
    "OrcaBoxStudioPlugin",
    "BoxStudioPageCapability",
    "BoxStudioDockCapability",
    "BoxStudioController",
]
