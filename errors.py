class MCodeError(Exception):
    """Base class for user-facing MCode errors."""


class ConfigurationError(MCodeError):
    """The project or package configuration is invalid."""


class ResolutionError(MCodeError):
    """Package dependencies cannot be resolved."""


class GenerationConflict(MCodeError):
    """Generation would overwrite content not owned by MCode."""
