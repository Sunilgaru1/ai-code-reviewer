import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not configured in settings.")

def generate_code_review(filename, code_content, metrics, score):
    """
    Sends complex or messy code to Gemini to generate actionable refactoring tips and Mermaid diagrams.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # We upgraded the prompt using the senior developer's Mermaid trick!
        prompt = f"""
        You are an elite Staff Software Engineer and automated code reviewer.
        Analyze the following Python file and provide a concise, high-impact review.
        
        File Name: {filename}
        Static Analysis Metrics: {metrics}
        Predicted Maintainability Score: {score}/100
        
        Source Code:
        ```python
        {code_content}
        ```
        
        Provide your response in clean Markdown. Your review MUST include exactly these 4 sections:
        
        ### 1. Code Review Summary
        Provide a 2-sentence breakdown of why this code received its maintainability score.
        
        ### 2. Code Smells & Bottlenecks
        Identify specific areas where complexity, nesting, or loops can be reduced.
        
        ### 3. Refactoring Recommendation
        Provide a brief, optimized Python code snippet showing how to fix the worst offender.
        
        ### 4. Architecture Flow
        Output a valid Mermaid diagram showing the flow or process of the provided code.
        - It MUST render correctly on GitHub — avoid quotes, semicolons, and invalid characters.
        - Always start with ```mermaid and end with ```.
        - Make it a flowchart (graph TD).
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"Failed to generate LLM review: {e}")
        return None