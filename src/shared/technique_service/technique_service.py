"""Service for loading and managing technique definitions from YAML files."""

import yaml
import logging

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
                    logger.error(err_msg)
                    raise Exception(err_msg)

                self.techniques[technique.id] = technique

        logger.info(f"Loaded {len(self.techniques)} techniques into technique service")

    def get_all_techniques(self) -> dict[str, Technique]:
        """Get all loaded techniques.

        Returns:
            Dictionary mapping technique names to Technique objects.
        """
        return self.techniques
