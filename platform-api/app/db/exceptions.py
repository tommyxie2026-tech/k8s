class RepositoryError(Exception):
    """Base exception for repository-layer errors."""


class ResourceNotFoundError(RepositoryError):
    """Raised when a requested resource does not exist or is soft-deleted."""


class ResourceVersionConflictError(RepositoryError):
    """Raised when optimistic concurrency validation fails."""
