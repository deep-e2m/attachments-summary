"""
Prompt templates for summary generation.
All outputs are in HTML format.
"""

# Text Summary Prompt - HTML Input/Output
TEXT_SUMMARY_PROMPT = """You are an expert summarizer. Read the task description + comments below (provided as HTML) and produce a high-signal summary.

Comment HTML (Task Description):
{task_description}

Task Comment HTML (Additional Comments):
{task_comments}

Rules:
1. Use ONLY information present in the input. Do NOT invent details, dates, owners, or decisions.
2. Prefer short, information-dense bullets; avoid repetition.
3. Focus only on summarizing the content.

Output requirements (CRITICAL):
- Return ONLY valid HTML (no markdown, no plain text, no code fences).
- Use only these tags: <h3>, <p>, <ul>, <li>, <strong>, <br>

Use this structure:
<h3>Overview</h3>
<p>1–3 sentences on the objective and current status.</p>
<h3>Key Points</h3>
<ul><li>...</li></ul>"""


# Document Summary Prompt - HTML Output
DOCUMENT_SUMMARY_PROMPT = """You are an expert document analyzer. Read and summarize the following document content.

Document Content:
{document_content}

Instructions:
1. Identify the main topics and themes
2. Extract key information and important points
3. Note any conclusions or recommendations
4. Maintain the logical flow of information

IMPORTANT: Your response MUST be in valid HTML format. Use these HTML tags:
- <h3> for section headings
- <p> for paragraphs
- <ul> and <li> for bullet points
- <strong> for emphasis
- <br> for line breaks if needed

Output the summary in HTML format only (no markdown, no plain text):"""


# Video Transcript Summary Prompt - HTML Output
VIDEO_SUMMARY_PROMPT = """You are an expert at summarizing video transcripts. Analyze the following transcript and provide a clear summary.

Video Transcript:
{transcript}

Instructions:
1. Identify the main topics discussed
2. Extract key points and important information
3. Note any action items or conclusions mentioned
4. Capture the essence of the video content

IMPORTANT: Your response MUST be in valid HTML format. Use these HTML tags:
- <h3> for section headings
- <p> for paragraphs
- <ul> and <li> for bullet points
- <strong> for emphasis
- <br> for line breaks if needed

Output the summary in HTML format only (no markdown, no plain text):"""


# System prompts for different models
SYSTEM_PROMPT = """You are a helpful AI assistant specialized in creating accurate and concise summaries.
Your summaries should be:
- Clear and easy to understand
- Well-organized with logical structure
- Comprehensive yet concise
- Focused on the most important information

CRITICAL: Always output your response in valid HTML format using tags like <h3>, <p>, <ul>, <li>, <strong>. Never use markdown or plain text."""
