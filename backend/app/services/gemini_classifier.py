"""AI classifier for items using OpenRouter."""

import json
from typing import Optional

import httpx

from ..config import get_settings
from ..schemas import DealClassification

settings = get_settings()

# System prompt for item classification
CLASSIFICATION_PROMPT = """You are an expert at identifying items from marketplace listings.
Analyze the listing text and extract structured information.

Your response must be valid JSON with these fields:
- category: broad category (electronics, furniture, clothing, vehicles, tools, sports, toys, etc.)
- subcategory: specific type within category (gpu, couch, jacket, truck, drill, etc.)
- brand: manufacturer/brand name if identifiable
- model: specific model name/number if identifiable
- item_details: object with any relevant specs/attributes extracted
- condition: "new" if explicitly stated (sealed, BNIB, brand new, unopened, NIB, factory sealed),
             "used" if explicitly stated (used, like new, excellent condition, works great, tested, refurbished),
             "unknown" if condition is not explicitly mentioned
- condition_confidence: "explicit" if condition was clearly stated, "unclear" if you had to guess or couldn't determine

CRITICAL: For condition, only mark as "new" or "used" if it is EXPLICITLY stated in the listing.
If there's any ambiguity or the condition is not mentioned, use "unknown".
Never guess the condition.

Respond with JSON only, no markdown formatting."""


class AIClassifier:
    """Classifies items using OpenRouter API."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.0-flash-001"  # Fast and cheap

    async def classify(self, listing_text: str) -> Optional[DealClassification]:
        """
        Classify an item from its listing text.

        Args:
            listing_text: The raw listing title/description

        Returns:
            DealClassification with extracted fields, or None on error
        """
        if not self.api_key:
            print("OpenRouter API key not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": CLASSIFICATION_PROMPT},
                            {"role": "user", "content": f"Listing to analyze:\n{listing_text}"},
                        ],
                        "temperature": 0.1,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    print(f"OpenRouter error: {response.status_code} - {response.text}")
                    return None

                data = response.json()
                text = data["choices"][0]["message"]["content"].strip()

                # Extract JSON from response (handle markdown code blocks)
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()

                result = json.loads(text)

                return DealClassification(
                    category=result.get("category"),
                    subcategory=result.get("subcategory"),
                    brand=result.get("brand"),
                    model=result.get("model"),
                    item_details=result.get("item_details"),
                    condition=result.get("condition", "unknown"),
                    condition_confidence=result.get("condition_confidence", "unclear"),
                )

        except Exception as e:
            print(f"Error classifying item: {e}")
            return None


# Singleton instance
_classifier: Optional[AIClassifier] = None


def get_classifier() -> AIClassifier:
    """Get or create classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = AIClassifier()
    return _classifier
