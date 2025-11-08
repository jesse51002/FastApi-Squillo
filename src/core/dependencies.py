"""Dependency injection container for FastAPI application."""

from dependency_injector import containers, providers

from src.shared.llm_service.mistral import MistralService
from src.shared.technique_service.technique_service import TechniqueService
from src.ai_recipe_engine.service import TechniqueExtractionService


class DependencyManager(containers.DeclarativeContainer):
    """Dependency injection container for application services."""

    # LLM Services
    mistral_service = providers.Singleton(MistralService)

    # Technique Service
    technique_service = providers.Singleton(TechniqueService)

    # Technique Extraction Service
    technique_extraction_service = providers.Singleton(
        TechniqueExtractionService,
        mistral_service=mistral_service,
        technique_service=technique_service
    )


# Global container instance
container = DependencyManager()
