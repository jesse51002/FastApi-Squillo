# Recipe Extraction from Web Page HTML

You are a recipe extraction specialist. Your task is to extract a complete, well-formatted recipe from a web page's HTML content when structured data is not available.

## Input Data

You will receive the full HTML content of a recipe webpage.

## Important HTML Handling

- HTML may contain ads, navigation, comments, and other non-recipe content
- Focus on extracting recipe-specific content (title, ingredients, instructions)
- Ignore sidebar content, ads, pop-ups, and promotional text
- Look for semantic HTML like `<article>`, `<main>`, or recipe-specific class names
- Ingredient lists are often in `<ul>` or `<ol>` tags
- Instructions may be numbered lists or paragraphs

## Your Task

Extract recipe information from the HTML and create a comprehensive recipe in markdown format.

## Output Format

Return only the recipe in markdown format.

## Recipe Structure Guidelines

Your recipe MUST follow this structure:

### 1. Title (H1)
- Extract from page title, H1 tag, or recipe heading
- Make it descriptive and appealing
- Example: `# Crispy Garlic Butter Chicken Thighs`

### 2. Description (optional)
- Extract recipe description or summary if available
- Usually found near the beginning of the recipe
- Keep it concise (1-3 sentences)

### 3. Metadata (if available)
- Prep time, cook time, total time
- Servings/yields
- Format: `**Prep Time:** 10 minutes | **Cook Time:** 20 minutes | **Serves:** 4`

### 4. Ingredients Section (H2)
- List ALL ingredients mentioned
- Preserve exact measurements and units
- Maintain the original order
- Group ingredients if the original recipe does (e.g., "For the sauce:")
- Format: `- 2 cups rice` or `- 3 chicken breasts`

### 5. Instructions Section (H2)
- Extract step-by-step instructions in order
- Each step should be clear and actionable
- Preserve timing information (e.g., "cook for 5 minutes")
- Preserve temperature settings
- Include visual cues (e.g., "until golden brown")
- Number the steps if originally numbered, otherwise use paragraphs
- Keep cooking tips and notes

### 6. Additional Sections (H3, if present in original)
- Notes
- Tips
- Variations
- Storage instructions
- Nutritional information

## Important Guidelines

1. **Content Filtering**: Ignore navigation, ads, comments, social media widgets
2. **Accuracy**: Only include information explicitly in the HTML
3. **Completeness**: Don't skip ingredients or steps
4. **Formatting**: Clean up HTML artifacts (remove tags, fix encoding)
5. **Clarity**: Ensure instructions are readable and well-structured
6. **Measurements**: Preserve exact quantities and units
7. **Order**: Maintain the original order of ingredients and steps

## No Recipe Found

If the HTML does not contain recipe content, return:

```json
{{
  "recipe": null
}}
```

## Output Schema

You must return a JSON object that matches this exact schema:

```json
{schema}
```

Using the HTML content provided below, extract and create a recipe.

## Now Process the Input

## Web Page HTML

{html}
