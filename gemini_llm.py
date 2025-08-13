# gemini_llm.py
from langchain_core.language_models import LLM
import google.generativeai as genai
from typing import List, Optional
import os

class GeminiLLM(LLM):
    model: str = "models/gemini-1.5-flash"
    temperature: float = 0.2
    max_output_tokens: int = 512

    def __init__(self, **kwargs):
        super().__init__()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY env var is not set.")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self.model)

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = self._model.generate_content(prompt)
        return response.text

    @property
    def _llm_type(self) -> str:
        return "gemini"
