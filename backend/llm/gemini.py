import google.generativeai as genai
from typing import List, Dict, Any
import json
from .base import LLMProvider
from ..config import settings


class GeminiProvider(LLMProvider):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Convert messages to Gemini format
        prompt = self._format_messages(messages)

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            ),
        )

        return response.text

    async def generate_structured_response(
        self, prompt: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        # For structured responses, we can ask Gemini to return JSON
        full_prompt = f"{prompt}\n\nPlease respond in JSON format: {json.dumps(schema)}"

        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                response_mime_type="application/json",
            ),
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            return {"raw_response": response.text}

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        # Convert OpenAI-style messages to a single prompt for Gemini
        formatted = ""
        for msg in messages:
            if msg["role"] == "user":
                formatted += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                formatted += f"Assistant: {msg['content']}\n"
        return formatted
