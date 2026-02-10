"""
In-Memory Audit Repository

WHY: Enables local development and testing without a real database.
Perfect for the "Adapter" pattern - the domain doesn't know it's just a dict in memory.
"""
import logging
from typing import Dict, List, Optional
from uuid import UUID

from ...domain.entities import AuditResult
from ...domain.ports import AuditRepository
from ...domain.value_objects import CleanlinessStatus

logger = logging.getLogger(__name__)


class InMemoryAuditRepository(AuditRepository):
    """
    Thread-safe in-memory implementation of AuditRepository.
    
    WHY: 
    1. Zero-dependency setup for developers
    2. Fast integration testing
    3. Simulates DB behavior (async methods)
    """

    def __init__(self):
        self._audits: Dict[UUID, AuditResult] = {}
        logger.info("Initialized InMemoryAuditRepository")

    async def save(self, audit: AuditResult) -> None:
        """
        Persist audit result in memory.
        """
        self._audits[audit.audit_id] = audit
        logger.debug(f"Saved audit {audit.audit_id} to memory")

    async def find_by_id(self, audit_id: UUID) -> Optional[AuditResult]:
        """
        Retrieve audit by ID.
        """
        return self._audits.get(audit_id)

    async def find_by_dealer_and_checkpoint(
        self,
        dealer_id: str,
        checkpoint_id: str,
        limit: int = 100
    ) -> List[AuditResult]:
        """
        Filter audits by dealer and checkpoint.
        """
        # Linear search is fine for in-memory dev database
        results = [
            audit for audit in self._audits.values()
            if audit.image_metadata.dealer_id == dealer_id 
            and audit.image_metadata.checkpoint_id == checkpoint_id
        ]
        
        # Sort by date (newest first)
        results.sort(key=lambda x: x.analyzed_at, reverse=True)
        return results[:limit]

    async def find_pending_reviews(self, limit: int = 100) -> List[AuditResult]:
        """
        Find audits needing review.
        """
        results = [
            audit for audit in self._audits.values()
            if audit.status == CleanlinessStatus.REQUIRES_MANUAL_REVIEW
            and not audit.is_finalized()
        ]
        results.sort(key=lambda x: x.analyzed_at)
        return results[:limit]

    async def count_by_status(self, dealer_id: str) -> dict:
        """
        Aggregate stats.
        """
        counts = {status.value: 0 for status in CleanlinessStatus}
        
        for audit in self._audits.values():
            if audit.image_metadata.dealer_id == dealer_id:
                counts[audit.status.value] += 1
                
        return counts
