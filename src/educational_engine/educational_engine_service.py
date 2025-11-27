"""Educational engine service for technique recommendations."""

import logging
from datetime import datetime, timezone

from src.ai_recipe_engine.schema import ExtractionRecipeStep
from src.database.database_service import DatabaseService
from src.database.schemas.user_schema import (
    TechniqueViewingInfo,
    TechniqueWatchSession,
)
from src.educational_engine.schemas import (
    MarkTechniqueWatchedResponse,
    SimplifiedTechnique,
    TechniqueRecommendationResponse,
)
from src.shared.technique_service.schemas import Technique
from src.shared.technique_service.technique_service import TechniqueService

logger = logging.getLogger(__name__)


class EducationalEngineService:
    """Service for managing technique recommendations and learning progress."""

    def __init__(
        self,
        database_service: DatabaseService,
        technique_service: TechniqueService,
    ):
        """Initialize the educational engine service.

        Args:
            database_service: Service for database operations
            technique_service: Service for technique data access
        """
        self.database_service = database_service
        self.technique_service = technique_service

    async def get_technique_recommendation(
        self, recipe_id: str, user_id: str, step_number: str
    ) -> TechniqueRecommendationResponse:
        """Get technique recommendation for a specific recipe step.

        Args:
            recipe_id: Unique identifier for the recipe
            user_id: Unique identifier for the user
            step_number: Step number in the recipe (can be decimal like 1.1)

        Returns:
            TechniqueRecommendationResponse with recommended technique,
            prerequisite (if applicable), and already_watched flag

        Raises:
            ValueError: If recipe, user, or step not found
            Exception: If technique data is inconsistent
        """
        # Fetch recipe
        recipe = await self.database_service.get_recipe(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe {recipe_id} not found")

        # Fetch user
        user = await self.database_service.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Find the step
        step = self._find_step_by_number(recipe.steps, step_number)
        if not step:
            raise ValueError(f"Step {step_number} not found in recipe {recipe_id}")

        # If step has no techniques, return None
        if not step.techniques:
            return TechniqueRecommendationResponse(
                technique=None, prerequisite=None, already_watched=False
            )

        # Sort techniques by importance (high to low), difficulty (low to high)
        sorted_techniques = sorted(
            step.techniques,
            key=lambda t: (
                -t.importance,  # Higher importance first (negate for descending)
                t.difficulty,  # Lower difficulty first (ascending)
            ),
        )

        # Get all technique IDs from the sorted step
        technique_ids = [tech.id for tech in sorted_techniques]

        # Get watched technique IDs for this user
        watched_ids = self._get_watched_technique_ids(user.techniques_watched)

        # Filter unwatched techniques
        unwatched_ids = [tid for tid in technique_ids if tid not in watched_ids]

        # Determine which technique to recommend
        if unwatched_ids:
            # Recommend first unwatched technique (already sorted)
            recommended_id = unwatched_ids[0]
            already_watched = False
        else:
            # All watched, recommend first technique anyway
            recommended_id = technique_ids[0]
            already_watched = True

        # Get technique details
        all_techniques = self.technique_service.get_all_techniques()
        recommended_technique = all_techniques.get(recommended_id)

        if not recommended_technique:
            raise Exception(
                f"Technique {recommended_id} not found in technique service"
            )

        # Check for prerequisite
        prerequisite_technique = None
        if recommended_technique.prerequisite_video:
            prereq = all_techniques.get(recommended_technique.prerequisite_video)
            if prereq:
                prerequisite_technique = self._convert_to_simplified(prereq)

        # Convert to simplified technique
        simplified_technique = self._convert_to_simplified(recommended_technique)

        return TechniqueRecommendationResponse(
            technique=simplified_technique,
            prerequisite=prerequisite_technique,
            already_watched=already_watched,
        )

    async def mark_technique_watched(
        self,
        user_id: str,
        technique_id: str,
        watched_percentage: float,
        skipped: bool = False,
    ) -> MarkTechniqueWatchedResponse:
        """Mark a technique as watched with viewing details.

        Args:
            user_id: Unique identifier for the user
            technique_id: Unique identifier for the technique
            watched_percentage: Percentage of video watched (0-100)
            skipped: Whether the video was skipped

        Returns:
            MarkTechniqueWatchedResponse with success status

        Raises:
            ValueError: If user or technique not found
        """
        # Fetch user
        user = await self.database_service.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Validate technique exists
        all_techniques = self.technique_service.get_all_techniques()
        if technique_id not in all_techniques:
            raise ValueError(f"Technique {technique_id} not found")

        # Create watch session
        watch_session = TechniqueWatchSession(
            watched_percentage=watched_percentage,
            watch_time=datetime.now(timezone.utc),
        )

        # Get existing viewing info or create new one
        if technique_id in user.techniques_watched:
            viewing_info = user.techniques_watched[technique_id]
        else:
            # Create new viewing info and add to user's dict
            viewing_info = TechniqueViewingInfo(technique_id=technique_id)
            user.techniques_watched[technique_id] = viewing_info

        # Add watch session to history
        viewing_info.watch_history.append(watch_session)

        # Update skipped flag if provided
        if skipped:
            viewing_info.skipped = True

        # Explicitly update user data with modified techniques_watched
        await self.database_service.update_user(user)

        return MarkTechniqueWatchedResponse(
            success=True,
            message=f"Technique {technique_id} watch session recorded",
        )

    def _convert_to_simplified(self, technique: Technique) -> SimplifiedTechnique:
        """Convert a full Technique to a SimplifiedTechnique.

        Args:
            technique: Full Technique object

        Returns:
            SimplifiedTechnique with only essential fields
        """
        return SimplifiedTechnique(
            id=technique.id,
            name=technique.name,
            description=technique.description,
            video_url=technique.video_url,
            image=technique.image,
            badge_image=technique.badge_image,
        )

    def _find_step_by_number(self, steps: list[ExtractionRecipeStep], step_number: str):
        """Find a step by its step_number.

        Args:
            steps: List of recipe steps
            step_number: Step number to find

        Returns:
            The matching step or None if not found
        """
        for step in steps:
            if step.step_number == step_number:
                return step
        return None

    def _get_watched_technique_ids(
        self, techniques_watched: dict[str, TechniqueViewingInfo]
    ) -> set[str]:
        """Extract technique IDs that have been watched.

        A technique is considered "watched" if it has at least one watch
        session with >= 80% completion.

        Args:
            techniques_watched: Dict of technique viewing information keyed by technique_id

        Returns:
            Set of technique IDs that have been watched
        """
        watched_ids = set()
        for technique_id, viewing_info in techniques_watched.items():
            # Check if any watch session reached 80% or more
            for session in viewing_info.watch_history:
                if session.watched_percentage >= 80.0:
                    watched_ids.add(technique_id)
                    break
        return watched_ids
