"""Template formatter utility for reading and formatting template files."""

from pathlib import Path
from typing import Any


class TemplateFormatter:
    """Utility for reading and formatting template files with dynamic data."""

    @staticmethod
    def read_template(path: Path) -> str:
        """Read template file contents.

        Args:
            file_path: Path to the template file

        Returns:
            str: The template file contents

        Raises:
            FileNotFoundError: If the template file doesn't exist
            IOError: If there's an error reading the file
        """
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {str(path)}")

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(f"Error reading template file: {str(e)}")

    @classmethod
    def format_template(cls, file_path: Path, **kwargs: Any) -> str:
        """Read a template file and format it with provided data.

        Args:
            file_path: Path to the template file
            **kwargs: Key-value pairs to format into the template

        Returns:
            str: The formatted template string

        Raises:
            FileNotFoundError: If the template file doesn't exist
            IOError: If there's an error reading the file
            KeyError: If a required template variable is missing

        Example:
            >>> formatted = TemplateFormatter.format_template(
            ...     'prompts/recipe.txt',
            ...     user_input='pasta',
            ...     cuisine='Italian'
            ... )
        """
        template = cls.read_template(file_path)

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required template variable: {str(e)}")
