"""Test script for technique extraction service."""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_recipe_engine.ai_recipe_service import TechniqueExtractionService  # noqa
from src.core.dependencies import container  # noqa


async def main():
    """Test technique extraction service."""
    recipe_text = """
# Garlic Honey Chili Chicken

Tender, juicy chicken with a perfect balance of sweet honey, spicy chili, and fragrant garlic. This marinade infuses the chicken with incredible flavor while keeping the meat moist and succulent. Perfect for grilling, baking, or pan-searing.

## Ingredients

### For the Marinade:
- 1/2 cup honey
- 1/3 cup soy sauce
- 6 cloves garlic, minced
- 3 red chili peppers, finely chopped (or 2 tbsp chili flakes)
- 3 tbsp rice vinegar
- 2 tbsp sesame oil
- 1 tbsp grated fresh ginger
- 2 tsp Dijon mustard
- 1/2 tsp black pepper
- 1/4 tsp salt (adjust to taste)

### For the Chicken:
- 4 boneless, skinless chicken breasts (or 8 thighs)
- 2 tbsp vegetable oil for cooking
- 2 cloves garlic, sliced (for garnish)
- 1 tsp sesame seeds (for garnish)
- Fresh cilantro or green onions (optional)

## Instructions

Start by preparing your marinade - this is where the magic happens. In a medium bowl, combine the honey, soy sauce, minced garlic, red chili peppers, rice vinegar, sesame oil, ginger, Dijon mustard, black pepper, and salt. Whisk everything together until the honey is fully incorporated and the marinade is smooth. The consistency should be thick and glossy.

Pat your chicken breasts dry with paper towels - this helps the marinade stick better. Place them in a large zip-lock bag or shallow dish. Pour your marinade over the chicken, making sure every piece is well coated. If using a bag, seal it and massage the marinade into the chicken. If using a dish, turn the chicken a few times to coat evenly.

Let the chicken marinate for at least 2 hours in the refrigerator, but ideally overnight (8-12 hours). The longer it sits, the more flavorful it becomes. The garlic and chili will penetrate deep into the meat, and the honey will help create a caramelized exterior when cooked.

When you're ready to cook, remove the chicken from the refrigerator 15 minutes before cooking to bring it closer to room temperature. Heat your vegetable oil in a large skillet or grill over medium-high heat.

Remove the chicken from the marinade, allowing excess marinade to drip back into the bowl. Reserve about 1/4 cup of the marinade for basting. Place the chicken in the hot skillet and cook for 6-7 minutes on the first side without moving it - you want a golden crust to form.

Flip the chicken and cook for another 5-6 minutes on the second side. The internal temperature should reach 165°F (74°C). During the last 2 minutes of cooking, brush the chicken with your reserved marinade on both sides for extra flavor and shine.

If the chicken browns too quickly, reduce the heat to medium. The goal is to get a caramelized, slightly charred exterior while keeping the inside juicy and cooked through.

Remove the chicken from the heat and let it rest for 5 minutes before serving. This allows the juices to redistribute throughout the meat, keeping it tender and moist.

Garnish with sliced garlic, sesame seeds, and fresh cilantro or green onions for a beautiful presentation.

Serve hot with steamed rice, roasted vegetables, or a fresh salad.

**Serves 4 | Prep time: 15 minutes | Marinating time: 2-12 hours | Cook time: 12-15 minutes**"""

    # Get service from dependency container
    service: TechniqueExtractionService = container.technique_extraction_service()

    start_time = time.time()

    # Call service directly
    result = await service.extract_techniques(recipe_text)

    print(result.model_dump_json(indent=2))
    print(f"\n\nFinished in {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
