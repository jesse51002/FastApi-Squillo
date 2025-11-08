"""Service layer for technique extraction business logic."""

import json
from pathlib import Path
import logging
import yaml

from src.shared.llm_service.mistral import MistralService
from src.shared.technique_service.technique_service import TechniqueService
from src.shared.technique_service.schemas import Technique

from src.util.template_formatter import TemplateFormatter
from .schema import TechniqueExtractionResponse

logger = logging.getLogger(__name__)

class TechniqueExtractionService:
    """Service for extracting cooking techniques from recipe text."""

    EXTRACTION_TEMPLATE = str(Path(__file__).parent / "template.md")

    def __init__(
            self,
            mistral_service: MistralService,
            technique_service: TechniqueService
            ):
        """Initialize the technique extraction service.

        Args:
            mistral_service: Injected Mistral LLM service
            technique_service: Injected technique service for validation
        """
        self.mistral_service = mistral_service
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

        techniques_dict: dict[str, Technique] = self.technique_service.get_all_techniques()

        # Format techniques for prompt (excluding tips and difficulty)
        techniques_list = [
            f"- **{tech.name}** ({tech.id}): {tech.description}"
            for tech in techniques_dict.values()
        ]
        techniques_text = "\n".join(techniques_list)

        # Get JSON schema from Pydantic model
        output_json_schema = json.dumps(
            TechniqueExtractionResponse.model_json_schema(),
            indent=2
        )

        # Format prompt using template
        prompt = TemplateFormatter.format_template(
            self.EXTRACTION_TEMPLATE,
            recipe_text=recipe_text,
            json_schema=output_json_schema,
            techniques=techniques_text
        )

        return prompt

    def _validate(self, response: TechniqueExtractionResponse) -> bool:
        """Validate that all technique IDs in the response are valid.

        Args:
            response: The technique extraction response to validate

        Returns:
            bool: True if all technique IDs are valid

        Raises:
            ValueError: If any technique ID is invalid
        """
        techniques_dict: dict[str, Technique] = self.technique_service.get_all_techniques()
        valid_technique_ids = set(techniques_dict.keys())

        invalid_techniques = []

        for step in response.steps:
            for technique_info in step.techniques:
                if technique_info.id not in valid_technique_ids:
                    invalid_techniques.append({
                        "step": step.step_number,
                        "technique_id": technique_info.id,
                        "technique_name": technique_info.name
                    })

        if invalid_techniques:
            error_details = "\n".join([
                f"  - Step {t['step']}: {t['technique_name']} (ID: {t['technique_id']})"
                for t in invalid_techniques
            ])
            raise ValueError(
                f"Invalid technique IDs found in response:\n{error_details}"
            )

        return True

    def _add_difficulty(self, response: TechniqueExtractionResponse) -> TechniqueExtractionResponse:
        """Add difficulty levels to all techniques in the response.

        Args:
            response: The technique extraction response

        Returns:
            TechniqueExtractionResponse: The response with difficulty levels added to all techniques
        """
        techniques_dict: dict[str, Technique] = self.technique_service.get_all_techniques()

        for step in response.steps:
            for technique_info in step.techniques:
                # Look up the technique and add its difficulty
                technique_info.difficulty = techniques_dict[technique_info.id].difficulty

        return response

    def _sort_techniques(self, response: TechniqueExtractionResponse) -> TechniqueExtractionResponse:
        """Sort techniques in each step by relevance (high to low), importance (high to low), and difficulty (low to high).

        Args:
            response: The technique extraction response

        Returns:
            TechniqueExtractionResponse: The response with sorted techniques in each step
        """
        
        response.steps.sort(
            key=lambda t: (
                int(t.step_number.split(".")[0]),
                int(t.step_number.split(".")[1]) if len(t.step_number.split(".")) > 1 else 0
            )
        )

        for step in response.steps:
            # Sort by: relevance DESC, importance DESC, difficulty ASC
            step.techniques.sort(
                key=lambda t: (
                    -t.relevance,      # Higher relevance first (negate for descending)
                    -t.importance,     # Higher importance first (negate for descending)
                    t.difficulty       # Lower difficulty first (ascending)
                )
            )

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

        # Call LLM API
        llm_response = await self.mistral_service.call_llm_api(prompt)

        if not llm_response:
            raise Exception("LLM returned no response")

        # Parse JSON response
        try:
            response_data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")

        # Validate and construct response using Pydantic
        try:
            response = TechniqueExtractionResponse(**response_data)
        except Exception as e:
            raise Exception(f"Failed to construct response from LLM data: {str(e)}")

        # Validate technique IDs
        self._validate(response)

        # Add difficulty levels to all techniques
        response = self._add_difficulty(response)

        # Sort techniques by relevance, importance, and difficulty
        response = self._sort_techniques(response)

        # Debug log the response in YAML format
        logger.debug("Technique extraction response:\n%s", yaml.dump(
            response.model_dump(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        ))

        return response
