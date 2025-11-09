"""Dependency injection container for FastAPI application."""

from dependency_injector import containers, providers

from src.shared.llm_service.mistral import MistralService
from src.shared.llm_service.claude import ClaudeService
from src.shared.llm_service.gemini import GeminiService
from src.shared.technique_service.technique_service import TechniqueService
from src.ai_recipe_engine.service import TechniqueExtractionService
from src.recipe_import_service.services.tiktok_service import TiktokImportService


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
        technique_service=technique_service
    )

    # TikTok Import Service
    tiktok_import_service = providers.Singleton(
        TiktokImportService,
        mistral_service=mistral_service
    )


# Global container instance
container = DependencyManager()
