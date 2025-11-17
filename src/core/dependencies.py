"""Dependency injection container for FastAPI application."""

from dependency_injector import containers, providers

from src.shared.llm_service.mistral import MistralService
from src.shared.llm_service.claude import ClaudeService
from src.shared.llm_service.gemini import GeminiService
from src.shared.technique_service.technique_service import TechniqueService
from src.ai_recipe_engine.ai_recipe_service import TechniqueExtractionService
from src.recipe_import_service.services.tiktok_service import TiktokImportService
from src.recipe_import_service.services.youtube_service import YouTubeImportService
from src.recipe_import_service.services.instagram_service import InstagramImportService
from src.recipe_import_service.services.web_recipe_service import WebRecipeService
from src.database.database_service import DatabaseService


class DependencyManager(containers.DeclarativeContainer):
    """Dependency injection container for application services."""

    # LLM Services
    mistral_service = providers.Singleton(MistralService)
    claude_service = providers.Singleton(ClaudeService)
    gemini_service = providers.Singleton(GeminiService)

    # Technique Service
    technique_service = providers.Singleton(TechniqueService)

    # Technique Extraction Service
    technique_extraction_service = providers.Singleton(
        TechniqueExtractionService,
        llm_service=gemini_service,
        technique_service=technique_service,
    )

    # TikTok Import Service
    tiktok_import_service = providers.Singleton(
        TiktokImportService, mistral_service=mistral_service
    )

    # YouTube Import Service (handles both regular videos and Shorts)
    youtube_import_service = providers.Singleton(
        YouTubeImportService, mistral_service=mistral_service
    )

    # Instagram Import Service
    instagram_import_service = providers.Singleton(
        InstagramImportService, mistral_service=mistral_service
    )

    # Web Recipe Import Service
    web_recipe_service = providers.Singleton(
        WebRecipeService, mistral_service=mistral_service
    )

    # YouTube Import Service (handles both regular videos and Shorts)
    youtube_import_service = providers.Singleton(
        YouTubeImportService, mistral_service=mistral_service
    )

    # Instagram Import Service
    instagram_import_service = providers.Singleton(
        InstagramImportService, mistral_service=mistral_service
    )

    # Web Recipe Import Service
    web_recipe_service = providers.Singleton(
        WebRecipeService, mistral_service=mistral_service
    )

    # Database Service
    database_service = providers.Singleton(DatabaseService)


# Global container instance
container = DependencyManager()
