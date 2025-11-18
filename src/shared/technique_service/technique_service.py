"""Service for loading and managing technique definitions from YAML files."""

import yaml
import logging
import string

from rapidfuzz import process, fuzz

from src.core.constants import TECHNIQUES_PATH
from src.shared.technique_service.schemas import Technique

logger = logging.getLogger(__file__)


class TechniqueService:
    """Service for loading and managing technique definitions.

    This service loads technique definitions from YAML files in the techniques
    directory and provides access to them through a dictionary interface.
    """

    def __init__(self) -> None:
        """Initialize the TechniqueService and load all techniques from YAML files."""
        self.techniques: dict[str, Technique] = {}
        self._load_techniques()
        self._validate_techniques()

    def _load_techniques(self) -> None:
        """Load all technique YAML files from the techniques directory.

        Iterates through all .yaml and .yml files in the TECHNIQUES_PATH directory,
        parses them, and stores them as Technique objects in the techniques dict.
        """
        # Check if techniques directory exists
        if not TECHNIQUES_PATH.exists():
            return

        # Find all YAML files recursively
        yaml_files = list(TECHNIQUES_PATH.rglob("**/*.yaml")) + list(
            TECHNIQUES_PATH.rglob("**/*.yml")
        )

        for yaml_file in yaml_files:
            with open(yaml_file, "r", encoding="utf-8") as file:
                technique_data = yaml.safe_load(file)
            if technique_data:
                technique = Technique(**technique_data)

                if technique.id in self.techniques:
                    err_msg = f"Duplicate id in {self.techniques[technique.id].name} and {technique.name}"
                    logger.error(err_msg, exc_info=True)
                    raise Exception(err_msg)

                self.techniques[technique.id] = technique

        logger.info(f"Loaded {len(self.techniques)} techniques into technique service")

    def _validate_techniques(self) -> None:
        """Validate technique references and restrictions.

        Ensures:
        1. All prerequisite_video IDs reference existing techniques
        2. All video_overwrite IDs reference existing techniques
        3. Techniques with restrict_classification=True are referenced
           in at least one other technique's prerequisite_video field
           (no "island nodes")

        Raises:
            ValueError: If any validation check fails
        """
        errors: list[str] = []

        # Track which techniques are referenced as prerequisites
        prerequisite_references: set[str] = set()

        for technique_id, technique in self.techniques.items():
            # Validate prerequisite_video references
            if technique.prerequisite_video:
                if technique.prerequisite_video not in self.techniques:
                    errors.append(
                        f"Technique '{technique.name}' (id={technique_id}) "
                        f"references non-existent prerequisite_video: "
                        f"{technique.prerequisite_video}"
                    )
                else:
                    # Track this reference
                    prerequisite_references.add(technique.prerequisite_video)

            # Validate video_overwrite references
            if technique.video_overwrite:
                if technique.video_overwrite not in self.techniques:
                    errors.append(
                        f"Technique '{technique.name}' (id={technique_id}) "
                        f"references non-existent video_overwrite: "
                        f"{technique.video_overwrite}"
                    )

        # Validate that restricted techniques are not island nodes
        for technique_id, technique in self.techniques.items():
            if technique.restrict_classification:
                if technique_id not in prerequisite_references:
                    errors.append(
                        f"Technique '{technique.name}' (id={technique_id}) "
                        f"has restrict_classification=True but is not referenced "
                        f"in any other technique's prerequisite_video field. "
                        f"This creates an unreachable 'island node'."
                    )

        # Raise all errors together
        if errors:
            error_message = "Technique validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            logger.error(error_message, exc_info=True)
            raise ValueError(error_message)

        logger.info(
            f"Technique validation passed: {len(self.techniques)} techniques, "
            f"{len(prerequisite_references)} prerequisite references"
        )

    def get_all_techniques(self) -> dict[str, Technique]:
        """Get all loaded techniques.

        Returns:
            Dictionary mapping technique names to Technique objects.
        """
        return self.techniques

    def _normalize_string(self, text: str) -> str:
        """Normalize a string for fuzzy matching by lowercasing and removing punctuation.

        Args:
            text: The string to normalize

        Returns:
            str: Normalized string (lowercase, no punctuation)
        """
        # Create translation table to remove punctuation
        translator = str.maketrans("", "", string.punctuation)
        # Remove punctuation and convert to lowercase
        return text.translate(translator).lower()

    def match_technique(self, id: str, name: str) -> Technique:
        """Find the best matching technique using fuzzy matching on ID and name.

        This method is case-insensitive and ignores punctuation to handle
        variations in capitalization and formatting from LLM outputs.
        Uses RapidFuzz's process.extract with limit=5 for optimized matching.

        Args:
            id: The technique ID to match (may be incorrect)
            name: The technique name to match (may be incorrect)

        Returns:
            Technique: The best matching technique from the loaded techniques

        Raises:
            ValueError: If no reasonable match is found (combined score < 50%)
        """
        if not self.techniques:
            raise ValueError("No techniques loaded")

        # Normalize name only (ID should be matched as-is)
        normalized_input_name = self._normalize_string(name)

        # Prepare choices for matching
        technique_ids = list(self.techniques.keys())
        normalized_names = [
            self._normalize_string(self.techniques[tid].name) for tid in technique_ids
        ]

        # Get top 5 candidates from ID matching (no normalization)
        id_matches = process.extract(id, technique_ids, scorer=fuzz.ratio, limit=5)

        # Get top 5 candidates from name matching (normalized)
        name_matches = process.extract(
            normalized_input_name, normalized_names, scorer=fuzz.ratio, limit=5
        )

        # Build score dictionaries to reuse scores from extract results
        id_scores = {idx: score for _, score, idx in id_matches}
        name_scores = {idx: score for _, score, idx in name_matches}

        # Collect all candidate indices from both matches
        candidate_indices = set(id_scores.keys()) | set(name_scores.keys())

        # Calculate combined scores for all candidates
        best_score = 0.0
        best_index = 0

        for idx in candidate_indices:
            # Get scores from dictionaries (default to 0 if not in top 5)
            id_score = id_scores.get(idx, 0.0)
            name_score = name_scores.get(idx, 0.0)

            # Combine scores with weighting: 50% ID, 50% name
            combined_score = (id_score * 0.5) + (name_score * 0.5)

            if combined_score > best_score:
                best_score = combined_score
                best_index = idx

        # Check if we found a reasonable match
        if best_score < 45.0:
            raise ValueError(
                f"No reasonable match found for technique (id='{id}', name='{name}'). "
                f"Best match score: {best_score:.1f}%"
            )

        matched_technique_id = technique_ids[best_index]
        matched_technique = self.techniques[matched_technique_id]

        # Log warning if match quality is low
        if best_score < 80.0:
            logger.warning(
                f"Low confidence fuzzy match: input (id='{id}', name='{name}') -> "
                f"matched (id='{matched_technique.id}', name='{matched_technique.name}') "
                f"with score {best_score:.1f}%"
            )

        return matched_technique
