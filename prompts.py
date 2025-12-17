"""
Prompt templates for summary generation.
All outputs are in HTML format.
"""

# Text Summary Prompt - HTML Output
TEXT_SUMMARY_PROMPT = """You are an expert summarizer. Analyze the following task description and comments (which may contain HTML), then provide a clear, concise summary.

Task Description:
{task_description}

Task Comments:
{task_comments}

Instructions:
1. Identify the main objective of the task
2. Highlight key points from the comments
3. Note any important decisions or action items mentioned
4. Keep the summary concise but comprehensive

IMPORTANT: Your response MUST be in valid HTML format. Use these HTML tags:
- <h3> for section headings
- <p> for paragraphs
- <ul> and <li> for bullet points
- <strong> for emphasis
- <br> for line breaks if needed

Output the summary in HTML format only (no markdown, no plain text):"""


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
