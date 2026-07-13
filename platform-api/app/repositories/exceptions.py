class RepositoryError(Exception):
    """Base repository-layer exception."""


class ResourceNotFoundError(RepositoryError):
    """Raised when a requested resource does not exist."""


class OptimisticConcurrencyError(RepositoryError):
    """Raised when resource_version does not match the persisted value."""
