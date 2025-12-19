"""
Prompt templates for summary generation.
All outputs are in plain text format.
"""

# Text Summary Prompt - Plain Text Input, Plain Text Output
TEXT_SUMMARY_PROMPT = """You are an expert summarizer. Read the task description + comments below and produce a high-signal summary.

Task Description:
{task_description}

Task Comments:
{task_comments}

Rules:
1. Use ONLY information present in the input. Do NOT invent details, dates, owners, or decisions.
2. Prefer short, information-dense bullets; avoid repetition.
3. Focus only on summarizing the content.

Output requirements (CRITICAL):
- Return ONLY plain text (no HTML, no markdown, no code fences).
- Use simple formatting with dashes (-) for bullet points.

Use this structure:
Overview:
1-3 sentences on the objective and current status.

Key Points:
- Point 1
- Point 2
- etc."""


# Document Summary Prompt - Plain Text Output
DOCUMENT_SUMMARY_PROMPT = """You are an expert document analyzer. Read and summarize the following document content.

Document Content:
{document_content}

Instructions:
1. Identify the main topics and themes
2. Extract key information and important points
3. Note any conclusions or recommendations
4. Maintain the logical flow of information

IMPORTANT: Your response MUST be in plain text format only.
- Use clear section headings followed by colon
- Use dashes (-) for bullet points
- No HTML tags, no markdown

Output the summary in plain text format only:"""


# Video Transcript Summary Prompt - Plain Text Output
VIDEO_SUMMARY_PROMPT = """You are an expert at summarizing video transcripts. Analyze the following transcript and provide a clear summary.

Video Transcript:
{transcript}

Instructions:
1. Identify the main topics discussed
2. Extract key points and important information
3. Note any action items or conclusions mentioned
4. Capture the essence of the video content

IMPORTANT: Your response MUST be in plain text format only.
- Use clear section headings followed by colon
- Use dashes (-) for bullet points
- No HTML tags, no markdown

Output the summary in plain text format only:"""


# System prompts for different models
SYSTEM_PROMPT = """You are a helpful AI assistant specialized in creating accurate and concise summaries.
Your summaries should be:
- Clear and easy to understand
- Well-organized with logical structure
- Comprehensive yet concise
- Focused on the most important information

CRITICAL: Always output your response in plain text format only. No HTML tags, no markdown. Use simple dashes (-) for bullet points."""
