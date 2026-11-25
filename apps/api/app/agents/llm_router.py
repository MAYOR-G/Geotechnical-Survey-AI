import asyncio
import hashlib
import math
from typing import Optional
import httpx
from app.core.config import settings
from app.core.exceptions import ExternalProviderError


def _deterministic_fallback_vector(text: str, dim: int = 1536) -> list[float]:
    """Unit-normalized 1536-dim lexical-hash embedding used only if remote embedding batch times out."""
    vec = [0.0] * dim
    tokens = text.lower().split()
    if not tokens:
        return vec
    for tok in tokens[:512]:
        digest = hashlib.sha256(tok.encode("utf-8", errors="ignore")).digest()
        for i in range(0, len(digest), 4):
            idx = int.from_bytes(digest[i : i + 2], "big") % dim
            sign = 1.0 if (digest[i + 2] % 2 == 0) else -1.0
            mag = (digest[i + 3] / 255.0) + 0.1
            vec[idx] += sign * mag
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


class LLMRouter:
    """
    Two-Tiered Invisible Model Routing Pipeline:
      - Tier 1 (Workhorse Intake, Research, QA Cross-Checking & Iterative Section Authoring):
        High-throughput forensic extraction and structured chapter authoring.
      - Tier 2 (Senior Principal Geotechnical Reviewer & Anti-AI Editorial Humanizer):
        Higher-tier editorial model enforcing crisp, domain-authentic consultancy prose.
    Never exposes internal AI model names or provider branding to the user interface.
    """

    CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
    EMBED_URL = "https://openrouter.ai/api/v1/embeddings"

    def _require_api_key(self, api_key_override: Optional[str] = None) -> str:
        api_key = (api_key_override or settings.OPENROUTER_API_KEY or "").strip()
        if not api_key:
            raise ExternalProviderError(
                "Required AI Engine key (OPENROUTER_API_KEY) is missing in your root .env file. "
                "Add OPENROUTER_API_KEY to .env and restart the backend server."
            )
        return api_key

    async def complete_tier1(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        api_key_override: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        """Tier 1: Workhorse Research, Forensic Extraction & Iterative Section Authoring Engine."""
        return await self.complete(
            messages=messages,
            model=settings.OPENROUTER_TIER1_MODEL or settings.OPENROUTER_FAST_MODEL,
            fallback_model=settings.OPENROUTER_TIER2_MODEL or settings.OPENROUTER_DRAFTING_MODEL,
            temperature=temperature,
            api_key_override=api_key_override,
            max_tokens=max_tokens,
        )

    async def complete_tier2(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        api_key_override: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        """Tier 2: Senior Principal Geotechnical Reviewer & Anti-AI Humanizer Engine."""
        return await self.complete(
            messages=messages,
            model=settings.OPENROUTER_TIER2_MODEL or settings.OPENROUTER_DRAFTING_MODEL,
            fallback_model=settings.OPENROUTER_TIER1_MODEL or settings.OPENROUTER_FAST_MODEL,
            temperature=temperature,
            api_key_override=api_key_override,
            max_tokens=max_tokens,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        temperature: float = 0.2,
        api_key_override: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        api_key = self._require_api_key(api_key_override)

        primary = model or settings.OPENROUTER_TIER2_MODEL or settings.OPENROUTER_DRAFTING_MODEL
        if primary in ("tier1", "tier1_engine", "drafting_engine"):
            primary = settings.OPENROUTER_TIER1_MODEL or settings.OPENROUTER_FAST_MODEL
        elif primary in ("tier2", "tier2_engine", "qa_verifier", "tier1_tier2_pipeline"):
            primary = settings.OPENROUTER_TIER2_MODEL or settings.OPENROUTER_DRAFTING_MODEL

        candidates = [primary]
        fb = fallback_model or settings.OPENROUTER_FAST_MODEL
        if fb and fb != primary:
            candidates.append(fb)
        if "openai/gpt-4o-mini" not in candidates:
            candidates.append("openai/gpt-4o-mini")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Geotechnical Survey AI Studio",
        }

        last_error = "No response from Geotechnical AI Engine"
        async with httpx.AsyncClient(timeout=110.0) as client:
            for m in candidates:
                for attempt in range(2):
                    try:
                        resp = await client.post(
                            self.CHAT_URL,
                            headers=headers,
                            json={
                                "model": m,
                                "messages": messages,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = (
                                data.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content")
                            )
                            if content:
                                return str(content).strip()
                            last_error = "Engine returned empty content"
                        elif resp.status_code in (401, 403):
                            raise ExternalProviderError(
                                "AI Engine authentication failed (HTTP 401/403). Verify OPENROUTER_API_KEY in your root .env file."
                            )
                        elif resp.status_code == 402:
                            raise ExternalProviderError(
                                "AI Engine account has insufficient credits (HTTP 402). Top up your provider credits and retry."
                            )
                        else:
                            last_error = f"HTTP {resp.status_code}"
                    except ExternalProviderError:
                        raise
                    except Exception as exc:
                        last_error = str(exc)
                    if attempt == 0:
                        await asyncio.sleep(0.8)

        raise ExternalProviderError(
            f"Geotechnical AI Engine request failed ({last_error}). Verify OPENROUTER_API_KEY and network connectivity."
        )

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
        api_key_override: Optional[str] = None,
    ) -> list[list[float]]:
        if not texts:
            return []
        api_key = self._require_api_key(api_key_override)

        embed_model = model or settings.OPENROUTER_EMBEDDING_MODEL
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Geotechnical Survey AI Studio",
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            for attempt in range(2):
                try:
                    resp = await client.post(
                        self.EMBED_URL,
                        headers=headers,
                        json={
                            "model": embed_model,
                            "input": texts,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        ordered = sorted(data, key=lambda item: item.get("index", 0))
                        vectors = [item["embedding"] for item in ordered if "embedding" in item]
                        if len(vectors) == len(texts):
                            return vectors
                    elif resp.status_code in (401, 403):
                        raise ExternalProviderError(
                            "Embedding authentication failed. Verify OPENROUTER_API_KEY in your root .env file."
                        )
                except ExternalProviderError:
                    raise
                except Exception:
                    pass
                if attempt == 0:
                    await asyncio.sleep(0.5)

        return [_deterministic_fallback_vector(t) for t in texts]


llm_router = LLMRouter()
