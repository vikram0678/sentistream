import os
import json
import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from transformers import pipeline

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Unified interface for sentiment analysis using local Transformers or External LLMs.
    """
    def __init__(self, model_type: str = 'local', model_name: str = None):
        self.model_type = model_type.lower()
        self.device = -1  # Default to CPU
        
        if self.model_type == 'local':
            # Load Sentiment Model
            sent_model = model_name or os.getenv("HUGGINGFACE_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
            self.sentiment_pipe = pipeline("text-classification", model=sent_model, device=self.device)
            
            # Load Emotion Model
            emot_model = os.getenv("EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")
            self.emotion_pipe = pipeline("text-classification", model=emot_model, device=self.device)
            logger.info(f"Local models loaded on device: {self.device}")
            
        else:
            # External LLM Setup (Groq example)
            self.api_key = os.getenv("EXTERNAL_LLM_API_KEY")
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.llm_model = os.getenv("EXTERNAL_LLM_MODEL", "llama-3.1-8b-instant")
            self.client = httpx.AsyncClient(timeout=30.0)
            logger.info(f"External LLM configured using model: {self.llm_model}")

    async def analyze_sentiment(self, text: str) -> Dict:
        """Analyze text sentiment: returns positive, negative, or neutral."""
        if not text or text.strip() == "":
            return {"sentiment_label": "neutral", "confidence_score": 0.0, "model_name": "none"}

        if self.model_type == 'local':
            # Local Inference
            result = self.sentiment_pipe(text[:512])[0] # Truncate to max tokens
            label = result['label'].lower()
            
            # Map labels (DistilBERT uses 'POSITIVE'/'NEGATIVE')
            mapped_label = "positive" if "pos" in label else "negative" if "neg" in label else "neutral"
            
            return {
                "sentiment_label": mapped_label,
                "confidence_score": round(result['score'], 4),
                "model_name": self.sentiment_pipe.model.config._name_or_path
            }
        else:
            # External API Inference
            return await self._call_external_llm(text, task="sentiment")

    async def analyze_emotion(self, text: str) -> Dict:
        """Detect primary emotion: joy, sadness, anger, fear, surprise, neutral."""
        if not text or len(text.strip()) < 10:
            return {"emotion": "neutral", "confidence_score": 1.0, "model_name": "static_rule"}

        if self.model_type == 'local':
            result = self.emotion_pipe(text[:512])[0]
            return {
                "emotion": result['label'].lower(),
                "confidence_score": round(result['score'], 4),
                "model_name": self.emotion_pipe.model.config._name_or_path
            }
        else:
            return await self._call_external_llm(text, task="emotion")

    async def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Process multiple texts efficiently."""
        if not texts:
            return []
            
        if self.model_type == 'local':
            # Pipelines handle lists natively and efficiently
            results = self.sentiment_pipe(texts, batch_size=len(texts))
            return [
                {
                    "sentiment_label": "positive" if "pos" in r['label'].lower() else "negative",
                    "confidence_score": round(r['score'], 4),
                    "model_name": "batch_local"
                } for r in results
            ]
        else:
            # Concurrent API calls for External LLM
            tasks = [self.analyze_sentiment(t) for t in texts]
            return await asyncio.gather(*tasks)

    async def _call_external_llm(self, text: str, task: str) -> Dict:
        """Helper to handle External API calls with structured prompts."""
        prompt = f"Analyze the following text and return ONLY a JSON object with 'label' and 'confidence' (0-1). Task: {task}. Text: {text}"
        
        try:
            payload = {
                "model": self.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = await self.client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = json.loads(data['choices'][0]['message']['content'])
            
            key = "sentiment_label" if task == "sentiment" else "emotion"
            return {
                key: content.get('label', 'neutral').lower(),
                "confidence_score": content.get('confidence', 0.5),
                "model_name": self.llm_model
            }
        except Exception as e:
            logger.error(f"External API Error: {e}")
            return {"sentiment_label": "neutral", "confidence_score": 0.0, "model_name": "fallback"}