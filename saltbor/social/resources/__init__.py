"""Common-pool resource management package."""

from saltbor.social.resources.cpr_manager import (
    CommonPoolResource,
    CollectiveResourceManager,
    CPRExtractionRecord,
    CPRHealthStatus,
    CPRMaintenanceRecord,
    CPRType,
)

__all__ = [
    "CommonPoolResource",
    "CollectiveResourceManager",
    "CPRExtractionRecord",
    "CPRHealthStatus",
    "CPRMaintenanceRecord",
    "CPRType",
]
