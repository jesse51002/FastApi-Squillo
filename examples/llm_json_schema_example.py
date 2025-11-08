"""Example demonstrating JSON schema usage with Claude, Mistral, and Gemini services."""

import asyncio
from src.shared.llm_service import ClaudeService, MistralService, GeminiService


# Define a JSON schema for structured recipe output
RECIPE_SCHEMA = {
    "properties": {
        "name": {
            "type": "string",
            "description": "Name of the recipe"
        },
        "ingredients": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of ingredients"
        },
        "instructions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Step-by-step cooking instructions"
        },
        "prep_time": {
            "type": "string",
            "description": "Preparation time"
        },
        "cook_time": {
            "type": "string",
            "description": "Cooking time"
        }
    },
    "required": ["name", "ingredients", "instructions"]
}


async def example_claude_with_schema():
    """Example using Claude with JSON schema enforced via tool calling."""
    claude = ClaudeService()

    prompt = """
    Create a simple recipe for chocolate chip cookies.
    Include the name, ingredients, instructions, prep time, and cook time.
    """

    # Claude will use tool calling to ensure JSON output matching the schema
    response = await claude.call_llm_api(
        input_prompt=prompt,
        json_schema=RECIPE_SCHEMA
    )

    print("Claude Response (with JSON schema):")
    print(response)
    print("\n" + "="*80 + "\n")


async def example_claude_without_schema():
    """Example using Claude without JSON schema (regular text response)."""
    claude = ClaudeService()

    prompt = "Explain what makes chocolate chip cookies delicious in 2 sentences."

    # Regular text response
    response = await claude.call_llm_api(input_prompt=prompt)

    print("Claude Response (without schema):")
    print(response)
    print("\n" + "="*80 + "\n")


async def example_mistral():
    """Example using Mistral (always returns JSON)."""
    mistral = MistralService()

    prompt = """
    Create a simple recipe for chocolate chip cookies.
    Return as JSON with: name, ingredients, instructions, prep_time, cook_time.
    """

    # Mistral always uses json_object response format
    response = await mistral.call_llm_api(input_prompt=prompt)

    print("Mistral Response (always JSON):")
    print(response)
    print("\n" + "="*80 + "\n")


async def example_gemini_with_schema():
    """Example using Gemini with JSON schema enforced via response_schema."""
    gemini = GeminiService()

    prompt = """
    Create a simple recipe for chocolate chip cookies.
    Include the name, ingredients, instructions, prep time, and cook time.
    """

    # Gemini will use response_schema to ensure JSON output matching the schema
    response = await gemini.call_llm_api(
        input_prompt=prompt,
        json_schema=RECIPE_SCHEMA
    )

    print("Gemini Response (with JSON schema):")
    print(response)
    print("\n" + "="*80 + "\n")


async def example_gemini_without_schema():
    """Example using Gemini without JSON schema (regular text response)."""
    gemini = GeminiService()

    prompt = "Explain what makes chocolate chip cookies delicious in 2 sentences."

    # Regular text response
    response = await gemini.call_llm_api(input_prompt=prompt)

    print("Gemini Response (without schema):")
    print(response)
    print("\n" + "="*80 + "\n")


async def main():
    """Run all examples."""
    print("LLM Service JSON Schema Examples\n")
    print("="*80 + "\n")

    # Example 1: Claude with JSON schema (uses tool calling)
    await example_claude_with_schema()

    # Example 2: Claude without JSON schema (regular text)
    await example_claude_without_schema()

    # Example 3: Mistral (always JSON)
    await example_mistral()

    # Example 4: Gemini with JSON schema (uses response_schema)
    await example_gemini_with_schema()

    # Example 5: Gemini without JSON schema (regular text)
    await example_gemini_without_schema()


if __name__ == "__main__":
    asyncio.run(main())
