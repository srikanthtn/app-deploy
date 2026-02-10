"""
Cleanliness Evaluator Domain Service

WHY: This is a DOMAIN SERVICE - it contains business logic that doesn't
naturally belong to a single entity or value object.

Key responsibilities:
1. Translate raw vision labels into business-level cleanliness decisions
2. Apply configurable rule sets (different dealers may have different standards)
3. Provide explainability for decisions
"""
from dataclasses import dataclass
from typing import List, Set

from ..entities import AuditResult, DetectedLabel
from ..value_objects import CleanlinessStatus, ConfidenceScore, ImageMetadata
from ..ports import VisionAnalysisResult


@dataclass
class CleanlinessRules:
    """
    Configuration for cleanliness evaluation.
    
    WHY: Different dealer types have different standards:
    - Premium brands: stricter rules
    - Service centers: focus on safety
    - Showrooms: focus on appearance
    
    This allows rule customization WITHOUT code changes.
    """
    # Labels that indicate NOT_CLEAN
    negative_labels: Set[str] = None
    
    # Minimum confidence to trust AI decision
    confidence_threshold: float = 80.0
    
    # Maximum allowed negative labels before failing
    max_negative_labels: int = 0
    
    # Enable/disable manual review triggers
    require_review_on_low_confidence: bool = True

    def __post_init__(self):
        if self.negative_labels is None:
            # Default negative labels for general cleanliness
            self.negative_labels = {
                # Dirt and debris
                "Dirt", "Mud", "Debris", "Trash", "Garbage", "Litter",
                "Waste", "Rubbish", "Clutter", "Mess",
                
                # Stains and damage
                "Stain", "Graffiti", "Rust", "Corrosion", "Mold", "Mildew",
                "Decay", "Deterioration",
                
                # Pests
                "Insect", "Bug", "Rodent", "Pest", "Spider Web",
                
                # Disorganization
                "Disorder", "Disorganized", "Untidy", "Unkempt",
                
                # Hazards
                "Spill", "Leak", "Broken Glass", "Sharp Object",
            }


class CleanlinessEvaluator:
    """
    Domain service for evaluating cleanliness from vision analysis.
    
    WHY: Domain Service (not entity method) because:
    1. It operates on multiple objects (VisionAnalysisResult + ImageMetadata)
    2. It applies configurable business rules
    3. It doesn't have identity or lifecycle
    
    Design: Stateless and deterministic.
    WHY: Same inputs should always produce same outputs (testability + reproducibility).
    """

    def __init__(self, rules: CleanlinessRules):
        self.rules = rules

    def evaluate(
        self,
        vision_result: VisionAnalysisResult,
        image_metadata: ImageMetadata,
        manual_override: bool = None
    ) -> AuditResult:
        """
        Core domain logic: Convert vision analysis into audit decision.
        
        WHY: This is THE critical business logic - centralized here, not scattered.
        
        Algorithm:
        1. If manual override exists, use it
        2. Check overall confidence against threshold
        3. Identify negative labels
        4. Apply business rules to determine status
        5. Generate explainability
        
        Args:
            vision_result: Raw output from vision provider
            image_metadata: Context about the image
            manual_override: Optional human override
        
        Returns:
            Complete AuditResult entity
        """
        # Step 1: Convert vision labels to domain labels
        detected_labels = self._convert_labels(vision_result.labels)
        
        # Step 2: Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(detected_labels)
        
        # Step 3: Identify negative labels
        negative_labels = self._identify_negative_labels(detected_labels)
        
        # Step 4: Determine status based on rules
        status = self._determine_status(
            negative_labels=negative_labels,
            overall_confidence=overall_confidence,
            manual_override=manual_override
        )
        
        # Step 5: Create audit result entity
        audit_result = AuditResult(
            image_metadata=image_metadata,
            detected_labels=detected_labels,
            overall_confidence=overall_confidence,
            status=status,
            negative_labels=negative_labels,
            manual_override=manual_override,
            vision_provider=vision_result.provider_name,
            model_version=vision_result.model_version,
        )
        
        return audit_result

    def _convert_labels(self, vision_labels: List) -> List[DetectedLabel]:
        """
        Convert provider-specific labels to domain labels.
        
        WHY: Domain layer works with DetectedLabel, not VisionLabel.
        This is the anti-corruption layer.
        """
        return [
            DetectedLabel(
                name=label.name,
                confidence=label.confidence,
                is_negative=self._is_negative_label(label.name)
            )
            for label in vision_labels
        ]

    def _is_negative_label(self, label_name: str) -> bool:
        """
        Check if label indicates unclean condition.
        
        WHY: Business rule - what constitutes "not clean"?
        Centralized here for consistency.
        """
        # Case-insensitive matching
        label_lower = label_name.lower()
        return any(
            neg_label.lower() in label_lower
            for neg_label in self.rules.negative_labels
        )

    def _identify_negative_labels(
        self,
        labels: List[DetectedLabel]
    ) -> List[DetectedLabel]:
        """
        Filter to only negative labels.
        
        WHY: For explainability - show WHICH issues were detected.
        """
        return [label for label in labels if label.is_negative]

    def _calculate_overall_confidence(
        self,
        labels: List[DetectedLabel]
    ) -> ConfidenceScore:
        """
        Calculate aggregate confidence.
        
        WHY: Business decision - how confident are we in this analysis?
        
        Strategy: Average of top 5 labels (most confident predictions).
        Alternative strategies could be: max, min, median.
        """
        if not labels:
            return ConfidenceScore(value=0.0)
        
        # Sort by confidence, take top 5
        top_labels = sorted(
            labels,
            key=lambda x: x.confidence.value,
            reverse=True
        )[:5]
        
        avg_confidence = sum(l.confidence.value for l in top_labels) / len(top_labels)
        return ConfidenceScore(value=avg_confidence)

    def _determine_status(
        self,
        negative_labels: List[DetectedLabel],
        overall_confidence: ConfidenceScore,
        manual_override: bool = None
    ) -> CleanlinessStatus:
        """
        Apply business rules to determine final status.
        
        WHY: This is THE business logic for cleanliness determination.
        All rules centralized here, not scattered across codebase.
        
        Decision Tree:
        1. Manual override wins
        2. Low confidence → Manual review
        3. Too many negative labels → Not clean
        4. Any negative labels → Not clean
        5. Otherwise → Clean
        """
        # Rule 1: Manual override has highest priority
        if manual_override is not None:
            return CleanlinessStatus.CLEAN if manual_override else CleanlinessStatus.NOT_CLEAN
        
        # Rule 2: Low confidence requires human review
        if not overall_confidence.is_above_threshold(self.rules.confidence_threshold):
            if self.rules.require_review_on_low_confidence:
                return CleanlinessStatus.REQUIRES_MANUAL_REVIEW
            else:
                return CleanlinessStatus.INSUFFICIENT_DATA
        
        # Rule 3: Check negative label count
        if len(negative_labels) > self.rules.max_negative_labels:
            return CleanlinessStatus.NOT_CLEAN
        
        # Rule 4: Any negative labels fail the audit
        if negative_labels:
            return CleanlinessStatus.NOT_CLEAN
        
        # Rule 5: Pass
        return CleanlinessStatus.CLEAN
