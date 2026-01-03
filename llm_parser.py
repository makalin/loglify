from openai import OpenAI
from typing import Dict, Optional, List
from config import settings
import json
import re


class LLMParser:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def parse_natural_language(self, text: str) -> Dict:
        """
        Parse natural language text into structured log entry.
        Returns a dictionary with action, project, duration, tags, etc.
        """
        prompt = f"""Parse the following natural language log entry into structured JSON format.
Extract:
- action: A brief action description (e.g., "Coding", "Reading", "Meeting", "Exercise")
- project: Project name if mentioned (optional)
- duration: Duration in minutes if mentioned (extract from phrases like "2 hours", "30 minutes", "45m")
- tags: Relevant tags as a list (e.g., ["work", "backend", "bugfix"])

Input: "{text}"

Return ONLY valid JSON in this format:
{{
    "action": "...",
    "project": "...",
    "duration": ...,
    "tags": [...]
}}

If a field cannot be determined, use null. Duration should be in minutes (convert hours to minutes)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that parses natural language into structured JSON. Always return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            parsed = json.loads(content)
            
            # Ensure all fields are present
            result = {
                "action": parsed.get("action", "Unknown"),
                "project": parsed.get("project"),
                "duration": parsed.get("duration"),
                "tags": parsed.get("tags", [])
            }
            
            return result
            
        except Exception as e:
            # Fallback parsing
            return {
                "action": text[:50],  # Use first 50 chars as action
                "project": None,
                "duration": self._extract_duration(text),
                "tags": []
            }
    
    def _extract_duration(self, text: str) -> Optional[float]:
        """Extract duration from text using regex"""
        # Patterns: "2 hours", "30 minutes", "45m", "1.5h"
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*hours?', lambda m: float(m.group(1)) * 60),
            (r'(\d+(?:\.\d+)?)\s*hrs?', lambda m: float(m.group(1)) * 60),
            (r'(\d+(?:\.\d+)?)\s*minutes?', lambda m: float(m.group(1))),
            (r'(\d+(?:\.\d+)?)\s*mins?', lambda m: float(m.group(1))),
            (r'(\d+(?:\.\d+)?)\s*m\b', lambda m: float(m.group(1))),
            (r'(\d+(?:\.\d+)?)\s*h\b', lambda m: float(m.group(1)) * 60),
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return converter(match)
        
        return None
    
    def answer_query(self, query: str, logs: List[Dict]) -> str:
        """
        Answer a natural language query about logs using AI.
        """
        # Format logs for context
        logs_context = "\n".join([
            f"- {log.get('action', 'Unknown')} ({log.get('duration', 0)} min) - {log.get('timestamp', '')}"
            for log in logs[:50]  # Limit to 50 most recent
        ])
        
        prompt = f"""You are analyzing a user's life logs. Answer their question based on the following log entries:

Logs:
{logs_context}

Question: {query}

Provide a concise, helpful answer. If the answer cannot be determined from the logs, say so."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes life logs and answers questions about them."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error processing query: {str(e)}"

