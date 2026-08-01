"""OrgFlow exception hierarchy — one project-rooted base plus domain errors."""


class OrgFlowError(Exception):
    """Base class for every OrgFlow-specific error."""


class TopologyError(OrgFlowError):
    """Raised when a graph topology is unknown or unsupported."""


class ConfigError(OrgFlowError):
    """Raised when a ``SimConfig`` fails validation."""
