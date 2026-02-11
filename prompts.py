"""
Prompt templates for summary generation.
All outputs are in plain text format.
"""

# Document Summary Prompt - Used with Gemini (sees full PDF with images)
DOCUMENT_SUMMARY_PROMPT = """You are an expert technical analyst creating executive-level document summaries.

Document Content:
{document_content}

TASK: Create an EXHAUSTIVE, COMPREHENSIVE summary that captures EVERY detail from this document.

MANDATORY REQUIREMENTS:
1. Your summary MUST be at least 400-600 words minimum
2. Include ALL specific details: names, numbers, percentages, timeframes, technical terms
3. If the document has multiple sections/options, summarize EACH ONE thoroughly
4. Include ALL features, capabilities, limitations mentioned
5. Preserve ALL hour estimates, costs, or effort breakdowns with their specific numbers
6. Include context like project names, website names, company names mentioned
7. If sub-options exist within options, explain each sub-option separately
8. If the document contains images, charts, or diagrams, describe their content and include relevant data from them

STRUCTURE YOUR SUMMARY AS FOLLOWS:

Overview/Context:
- What is this document about? Include project name, website, companies involved
- What is the main goal or purpose?

[For each major option/section in the document]:
Option/Section Name:
- Full description of what it involves
- ALL features and capabilities listed (do not summarize - list them all)
- ALL limitations or constraints mentioned
- Technical details (tools, plugins, APIs, methods)
- Time/effort estimates with exact numbers
- Any sub-components or breakdowns

Additional Considerations:
- Any other options mentioned (even if ruled out) and why
- Technical constraints or dependencies
- Variables that may affect the project

CRITICAL RULES:
- Do NOT condense or abbreviate - be thorough
- Do NOT skip any features, capabilities, or bullet points from the original
- Do NOT use vague language like "various features" - list them specifically
- Include hour breakdowns (e.g., "16-18 hours for X + 25-30 hours for Y = 36-48 total")
- Preserve technical terminology exactly as written
- Describe any visual content (images, charts, diagrams) and include data from them

Return only the summary in plain text format (no HTML, no markdown)."""
