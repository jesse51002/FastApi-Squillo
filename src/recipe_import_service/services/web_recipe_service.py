"""Web recipe import service for extracting recipes from recipe websites."""

from bs4 import BeautifulSoup, Comment
import httpx
import json
from typing import Optional
from pathlib import Path
import logging
from recipe_scrapers import scrape_html

from src.shared.llm_service.mistral import MistralService, MistralModels
from src.recipe_import_service.schemas.web_recipe_schema import WebRecipeData
from src.recipe_import_service.schemas.import_schema import LlmOutputFormat
from src.recipe_import_service.services.base_import_service import BaseImportService
from src.util.template_formatter import TemplateFormatter


logger = logging.getLogger(__name__)


class WebRecipeService(BaseImportService):
    """Service for importing recipes from web recipe sites.

    Uses a hybrid approach:
    1. Attempts to extract structured data using recipe-scrapers (550+ sites)
    2. Falls back to Mistral Small LLM if structured data unavailable
    """

    MODEL = MistralModels.small
    TEMPLATE_PATH = (
        Path(__file__).parent.parent / "templates" / "web_recipe_template.md"
    )

    def __init__(self, mistral_service: MistralService):
        """Initialize web recipe import service.

        Args:
            mistral_service: Mistral LLM service for recipe extraction fallback
        """
        self.mistral_service = mistral_service

    async def _url_to_text_recipe(
        self, url: str, mock: bool
    ) -> tuple[Optional[str], Optional[str]]:
        """Extract and create a recipe from a recipe website URL.

        This orchestrates the full pipeline:
        1. Attempt to extract structured data using recipe-scrapers
        2. If structured data found, format it as markdown and extract image
        3. If no structured data, fall back to LLM extraction from HTML

        Args:
            url: Recipe website URL
            mock: If to mock ensemble request (unused)

        Returns:
            Tuple of (recipe in markdown format, thumbnail URL) or (None, None) if no recipe found

        Raises:
            Exception: If both structured extraction and LLM extraction fail
        """

        # Fetch the HTML content
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Referer": "https://www.google.com/",
                },
            )
            response.raise_for_status()
            html_content = response.text

        # Step 1: Try structured data extraction
        recipe_data = await self._scrape_recipe_structured_data(url, html_content)

        if recipe_data:
            # Format structured data as markdown
            recipe = self._format_recipe_markdown(recipe_data)
            thumbnail_url = recipe_data.image
            logger.info(
                f"Successfully extracted recipe using structured data: {recipe_data.title}"
            )
            if thumbnail_url:
                logger.info(f"Extracted web recipe thumbnail: {thumbnail_url}")
            return recipe, thumbnail_url
        else:
            # Step 2: Fall back to LLM extraction (no thumbnail available)
            logger.info("No structured data found, falling back to LLM extraction")
            recipe = await self._extract_recipe_with_llm(html_content)
            return recipe, None

    async def _scrape_recipe_structured_data(
        self, url: str, html_content: str
    ) -> Optional[WebRecipeData]:
        """Extract structured recipe data from a recipe website URL.

        Uses the recipe-scrapers library to extract schema.org structured data
        from 550+ supported recipe websites.

        Args:
            url: URL of the recipe webpage

        Returns:
            WebRecipeData model with extracted recipe information, or None if extraction fails
        """
        try:

            # Use recipe-scrapers to extract structured data
            scraper = scrape_html(html=html_content, org_url=url)

            # Extract required fields to variables
            title = scraper.title()
            ingredients = scraper.ingredients()
            instructions = scraper.instructions()

            # Extract optional fields to variables with error handling
            try:
                total_time = scraper.total_time()
            except Exception:
                total_time = None

            try:
                prep_time = scraper.prep_time()
            except Exception:
                prep_time = None

            try:
                cook_time = scraper.cook_time()
            except Exception:
                cook_time = None

            try:
                yields_value = scraper.yields()
            except Exception:
                yields_value = None

            try:
                image = scraper.image()
            except Exception:
                image = None

            try:
                description = scraper.description()
            except Exception:
                description = None

            # Construct Pydantic model with named parameters
            recipe_data = WebRecipeData(
                title=title,
                ingredients=ingredients,
                instructions=instructions,
                total_time=total_time,
                prep_time=prep_time,
                cook_time=cook_time,
                yields=yields_value,
                image=image,
                description=description,
            )

            logger.info(f"Successfully extracted recipe: {title}")
            return recipe_data

        except Exception as e:
            logger.warning(f"Failed to extract structured data from {url}: {str(e)}")
            return None

    def _format_recipe_markdown(self, recipe_data: WebRecipeData) -> str:
        """Format WebRecipeData as markdown text.

        Args:
            recipe_data: Structured recipe data

        Returns:
            Recipe formatted as markdown
        """
        lines = []

        # Title
        lines.append(f"# {recipe_data.title}\n")

        # Description
        if recipe_data.description:
            lines.append(f"{recipe_data.description}\n")

        # Metadata
        metadata = []
        if recipe_data.prep_time:
            metadata.append(f"**Prep Time:** {recipe_data.prep_time} minutes")
        if recipe_data.cook_time:
            metadata.append(f"**Cook Time:** {recipe_data.cook_time} minutes")
        if recipe_data.total_time:
            metadata.append(f"**Total Time:** {recipe_data.total_time} minutes")
        if recipe_data.yields:
            metadata.append(f"**Yields:** {recipe_data.yields}")

        if metadata:
            lines.append(" | ".join(metadata))
            lines.append("")

        # Ingredients
        lines.append("## Ingredients\n")
        for ingredient in recipe_data.ingredients:
            lines.append(f"- {ingredient}")
        lines.append("")

        # Instructions
        lines.append("## Instructions\n")
        lines.append(recipe_data.instructions)

        return "\n".join(lines)

    async def _extract_recipe_with_llm(self, html_content: str) -> Optional[str]:
        """Extract recipe from HTML using Mistral Small LLM as fallback.

        Args:
            url: Recipe website URL

        Returns:
            Recipe in markdown format, or None if no recipe found
        """
        try:
            clean_content = self._extract_readable_text(html_content)

            # Get JSON schema from LlmOutputFormat
            json_schema = LlmOutputFormat.model_json_schema()
            str_json_schema = json.dumps(json_schema, indent=2)

            # Format the template with HTML and schema
            prompt = TemplateFormatter.format_template(
                self.TEMPLATE_PATH, html=clean_content, schema=str_json_schema
            )

            # Call Mistral API with text prompt
            response_text = await self.mistral_service.call_llm_api(
                input_prompt=prompt, model=self.MODEL, json_schema=json_schema
            )

            if not response_text:
                raise Exception("No response received from Mistral API")

            # Parse and validate the JSON response using Pydantic
            try:
                llm_output = LlmOutputFormat.model_validate_json(response_text)
                logger.info("Successfully extracted recipe using LLM fallback")
                return llm_output.recipe

            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON response from LLM: {str(e)}")
            except Exception as e:
                raise Exception(f"LLM response validation failed: {str(e)}")

        except Exception as e:
            raise Exception(f"LLM call failed to parse web recipe: {str(e)}")

    def _extract_readable_text(self, html_content: str) -> str:
        """
        Parses HTML content, removes scripts, styles, and other non-content
        elements, and returns the cleaned text.
        """
        soup = BeautifulSoup(html_content, "lxml")

        # 1. Remove non-content elements and their contents
        # This is the most crucial step for cleaning
        for element in soup(
            [
                "script",  # JavaScript code
                "style",  # CSS styles
                "noscript",  # Fallback content for disabled JS
                "header",  # Common site header/navigation
                "footer",  # Common site footer/links
                "nav",  # Navigation links
                "form",  # Input forms
                "button",  # Buttons
                "svg",  # Scalable Vector Graphics
                "img",  # Images (keeping alt text often better)
                "a",  # Links (might strip link text if not careful)
                "iframe",  # Embedded content
                "meta",  # Metadata
                "link",  # External resources
            ]
        ):
            element.decompose()  # .decompose() removes the tag and its contents

        # 2. Remove HTML comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 3. Extract all remaining text
        # .get_text() automatically joins text from various tags
        text = soup.get_text(separator="\n", strip=True)

        # 4. Clean up excessive whitespace (important if separator is a single space)
        # The 'strip=True' above usually handles leading/trailing whitespace well.
        # This step ensures multiple newlines are handled nicely.
        cleaned_text = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )

        return cleaned_text
