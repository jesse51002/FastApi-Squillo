"""Service layer for technique extraction business logic."""

import json
from pathlib import Path
import logging
import yaml

from src.shared.llm_service.base import BaseLLMService
from src.shared.technique_service.technique_service import TechniqueService
from src.shared.technique_service.schemas import Technique

from src.util.template_formatter import TemplateFormatter
from .schema import TechniqueExtractionResponse

logger = logging.getLogger(__name__)


class TechniqueExtractionService:
    """Service for extracting cooking techniques from recipe text."""

    EXTRACTION_TEMPLATE = str(Path(__file__).parent / "template.md")

    def __init__(
        self, llm_service: BaseLLMService, technique_service: TechniqueService
    ):
        """Initialize the technique extraction service.

        Args:
            mistral_service: Injected Mistral LLM service
            technique_service: Injected technique service for validation
        """
        self.llm_service = llm_service
        self.technique_service = technique_service

    def _get_template(self, recipe_text: str) -> str:
        """Generate the formatted prompt template for technique extraction.

        Args:
            recipe_text: Raw text of the recipe

        Returns:
            str: Formatted prompt ready for LLM API

        Raises:
            ValueError: If recipe text is too short
        """
        # Validate input
        if not recipe_text or len(recipe_text.strip()) < 10:
            raise ValueError("Recipe text must be at least 10 characters long")

        techniques_dict: dict[str, Technique] = (
            self.technique_service.get_all_techniques()
        )

        # Format techniques for prompt (excluding tips and difficulty)
        techniques_list = []
        for tech in techniques_dict.values():
            if tech.restrict_classification:
                continue

            techniques_list.append(f"- **{tech.name}** ({tech.id}): {tech.description}")

        techniques_text = "\n".join(techniques_list)

        # Get JSON schema from Pydantic model
        output_json_schema = json.dumps(
            TechniqueExtractionResponse.model_json_schema(), indent=2
        )

        # Format prompt using template
        prompt = TemplateFormatter.format_template(
            self.EXTRACTION_TEMPLATE,
            recipe_text=recipe_text,
            json_schema=output_json_schema,
            techniques=techniques_text,
        )

        return prompt

    def _validate_and_correct_technique(
        self, technique_info: Technique, step_number: str, valid_technique_ids: set[str]
    ) -> dict | None:
        """Validate and correct a single technique, returning correction info if needed.

        Args:
            technique_info: The technique info to validate
            step_number: The step number for logging
            valid_technique_ids: Set of valid technique IDs

        Returns:
            dict: Correction info if technique was corrected, None if valid or unmatched
            Raises ValueError if technique cannot be matched
        """
        if technique_info.id not in valid_technique_ids:
            # Attempt fuzzy matching
            matched_technique = self.technique_service.match_technique(
                technique_info.id, technique_info.name
            )

            # Track the correction
            correction = {
                "step": step_number,
                "original_id": technique_info.id,
                "original_name": technique_info.name,
                "corrected_id": matched_technique.id,
                "corrected_name": matched_technique.name,
            }

            # Correct the technique info with official values
            technique_info.id = matched_technique.id
            technique_info.name = matched_technique.name

            return correction
        else:
            # ID is valid, but ensure name matches official name
            techniques_dict = self.technique_service.get_all_techniques()
            if technique_info.name != techniques_dict[technique_info.id].name:
                logger.debug(
                    f"Corrected name for {technique_info.id}: '{technique_info.name}' -> '{techniques_dict[technique_info.id].name}'"
                )
                technique_info.name = techniques_dict[technique_info.id].name

            return None

    def _validate(
        self, response: TechniqueExtractionResponse
    ) -> TechniqueExtractionResponse:
        """Validate and correct technique IDs in the response using fuzzy matching.

        This method validates that all technique IDs in the response are valid.
        If invalid IDs are found, it attempts to fuzzy match them to correct techniques
        and automatically corrects both the ID and name to ensure consistency.
        Also ensures all technique names match official names even for valid IDs.

        Args:
            response: The technique extraction response to validate and correct

        Returns:
            bool: True if all technique IDs are valid or successfully corrected

        Raises:
            ValueError: If any technique ID cannot be fuzzy matched (score < 50%)
        """
        techniques_dict: dict[str, Technique] = (
            self.technique_service.get_all_techniques()
        )
        valid_technique_ids = set(techniques_dict.keys())

        corrections_made = []
        unmatched_techniques = []

        for step in response.steps:
            for technique_info in step.techniques:
                try:
                    correction = self._validate_and_correct_technique(
                        technique_info, step.step_number, valid_technique_ids
                    )
                    if correction:
                        corrections_made.append(correction)
                except ValueError as e:
                    # Could not find a reasonable match
                    unmatched_techniques.append(
                        {
                            "step": step.step_number,
                            "technique_id": technique_info.id,
                            "technique_name": technique_info.name,
                            "error": str(e),
                        }
                    )

        # Log all corrections made
        if corrections_made:
            logger.info(
                f"Corrected {len(corrections_made)} invalid technique ID(s) using fuzzy matching"
            )
            for correction in corrections_made:
                logger.debug(
                    f"Step {correction['step']}: "
                    f"'{correction['original_name']}' (ID: {correction['original_id']}) -> "
                    f"'{correction['corrected_name']}' (ID: {correction['corrected_id']})"
                )

        # Raise error if any techniques could not be matched
        if unmatched_techniques:
            error_details = "\n".join(
                [
                    f"  - Step {t['step']}: {t['technique_name']} (ID: {t['technique_id']}) - {t['error']}"
                    for t in unmatched_techniques
                ]
            )
            raise ValueError(
                f"Could not match the following technique(s) to valid techniques:\n{error_details}"
            )

        return response

    def _add_difficulty(
        self, response: TechniqueExtractionResponse
    ) -> TechniqueExtractionResponse:
        """Add difficulty levels to all techniques in the response.

        Args:
            response: The technique extraction response

        Returns:
            TechniqueExtractionResponse: The response with difficulty levels added to all techniques
        """
        techniques_dict: dict[str, Technique] = (
            self.technique_service.get_all_techniques()
        )

        for step in response.steps:
            for technique_info in step.techniques:
                # Look up the technique and add its difficulty
                technique_info.difficulty = techniques_dict[
                    technique_info.id
                ].difficulty

        return response

    def _sort_techniques(
        self, response: TechniqueExtractionResponse
    ) -> TechniqueExtractionResponse:
        """Sort techniques in each step by importance (high to low), and difficulty (low to high).

        Args:
            response: The technique extraction response

        Returns:
            TechniqueExtractionResponse: The response with sorted techniques in each step
        """

        response.steps.sort(
            key=lambda t: (
                int(t.step_number.split(".")[0]),
                (
                    int(t.step_number.split(".")[1])
                    if len(t.step_number.split(".")) > 1
                    else 0
                ),
            )
        )

        for step in response.steps:
            # Sort by: importance DESC, difficulty ASC
            step.techniques.sort(
                key=lambda t: (
                    -t.importance,  # Higher importance first (negate for descending)
                    t.difficulty,  # Lower difficulty first (ascending)
                )
            )

        return response

    def _calculate_recipe_times(
        self, response: TechniqueExtractionResponse
    ) -> TechniqueExtractionResponse:
        """Calculate active and total time for a recipe.

        Args:
            response: The technique extraction response

        Returns:
            TechniqueExtractionResponse: The response with calculated time fields
        """
        active_time = 0.0
        total_time = 0.0

        for step in response.steps:
            total_time += step.estimated_time
            if step.is_active_step:
                active_time += step.estimated_time

        response.active_time = active_time
        response.total_time = total_time

        return response

    async def extract_techniques(self, recipe_text: str) -> TechniqueExtractionResponse:
        """Extract cooking techniques from recipe text.

        Args:
            recipe_text: Raw text of the recipe

        Returns:
            TechniqueExtractionResponse: Structured recipe with techniques

        Raises:
            ValueError: If the recipe text is invalid or technique IDs are invalid
            Exception: If LLM API call fails or response is invalid
        """
        # Generate formatted prompt
        prompt = self._get_template(recipe_text)

        logger.debug(f"Input prompt:\\n\\n {prompt}")

        # Call LLM API
        llm_response = await self.llm_service.call_llm_api(
            prompt, TechniqueExtractionResponse.model_json_schema()
        )

        if not llm_response:
            raise Exception("LLM returned no response")

        # Parse JSON response
        try:
            json.loads(llm_response)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")

        # Validate and construct response using Pydantic
        try:
            response = TechniqueExtractionResponse.model_validate_json(llm_response)
        except Exception as e:
            raise Exception(f"Failed to construct response from LLM data: {str(e)}")

        # Validate technique IDs
        response = self._validate(response)

        response = self._add_difficulty(response)
        response = self._sort_techniques(response)
        response = self._calculate_recipe_times(response)

        # Debug log the response in YAML format
        logger.debug(
            "Technique extraction response:\n%s",
            yaml.dump(
                response.model_dump(),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            ),
        )

        return response
