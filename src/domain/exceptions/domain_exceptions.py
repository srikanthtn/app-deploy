"""Domain exceptions"""


class DomainException(Exception):
    """Base exception for all domain errors"""
    pass


class InvalidConfidenceScoreError(DomainException):
    """Raised when confidence score is out of valid range"""
    pass


class InvalidImageError(DomainException):
    """Raised when image doesn't meet analysis requirements"""
    pass


class AuditAlreadyFinalizedError(DomainException):
    """Raised when trying to modify a finalized audit"""
    pass
