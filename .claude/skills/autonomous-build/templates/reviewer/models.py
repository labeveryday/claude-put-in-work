"""
Model factory for the build reviewer.

Anthropic direct API only - trimmed from the strands-agents-template models module.
Requires ANTHROPIC_API_KEY. Override the model with REVIEWER_MODEL_ID.
"""

import os

from dotenv import load_dotenv
from strands.models.anthropic import AnthropicModel

# Load environment variables
load_dotenv()


def anthropic_model(api_key: str = os.getenv("ANTHROPIC_API_KEY"),
    model_id: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4000,
    temperature: float = 1,
    thinking: bool = True,
    budget_tokens: int = 1024) -> AnthropicModel:
    """
    Anthropic direct API model.
    Args:
        api_key: The API key to use (default: os.getenv("ANTHROPIC_API_KEY"))
        model_id: The model ID to use (default: claude-haiku-4-5-20251001)
        max_tokens: The maximum number of tokens to generate (default: 4000)
        temperature: The temperature to use (default: 1)
        thinking: Whether to use thinking (default: True)
        budget_tokens: The budget tokens to use (default: 1024)
    Returns:
        AnthropicModel

    Available models:
    - claude-haiku-4-5-20251001 - 200k context - 64k max_output tokens - input $1/M - output $5/M
    - claude-sonnet-4-5-20250929 - 200k context (1M beta) - 64k max_output tokens - input $3/M - output $15/M
    """
    if thinking:
        if budget_tokens >= max_tokens:
            raise ValueError("Budget tokens cannot be greater than max tokens")
        thinking = {"type": "enabled", "budget_tokens": budget_tokens}
    else:
        thinking = {"type": "disabled"}

    return AnthropicModel(
        client_args={"api_key": api_key},
        max_tokens=max_tokens,
        model_id=model_id,
        params={"temperature": temperature, "thinking": thinking},
    )
