"""
Audit Repository Port (Interface)

WHY: Repository Pattern - abstract persistence to enable:
1. Unit testing with in-memory repository
2. Migration from DynamoDB to RDS
3. Multi-region replication strategies
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities import AuditResult


class AuditRepository(ABC):
    """
    Port for audit result persistence.
    
    WHY: Domain defines WHAT it needs to persist, not HOW.
    Infrastructure decides whether to use DynamoDB, Postgres, etc.
    """

    @abstractmethod
    async def save(self, audit: AuditResult) -> None:
        """
        Persist audit result.
        
        WHY: Idempotent operation - multiple saves of same audit_id should
        update existing record, not create duplicates.
        
        Raises:
            RepositoryError: If save fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, audit_id: UUID) -> Optional[AuditResult]:
        """
        Retrieve audit by ID.
        
        Returns:
            AuditResult if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_dealer_and_checkpoint(
        self,
        dealer_id: str,
        checkpoint_id: str,
        limit: int = 100
    ) -> List[AuditResult]:
        """
        Find audits for specific dealer/checkpoint.
        
        WHY: Business query - "show me all audits for this location"
        """
        pass

    @abstractmethod
    async def find_pending_reviews(self, limit: int = 100) -> List[AuditResult]:
        """
        Find audits requiring manual review.
        
        WHY: Workflow support - auditors need queue of items to review.
        """
        pass

    @abstractmethod
    async def count_by_status(self, dealer_id: str) -> dict:
        """
        Count audits by status for a dealer.
        
        WHY: Dashboard metrics - show compliance rates.
        
        Returns:
            Dict like {'CLEAN': 150, 'NOT_CLEAN': 20, 'REQUIRES_MANUAL_REVIEW': 5}
        """
        pass
