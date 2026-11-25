from pathlib import Path
import time
from typing import Any, Awaitable, Callable, Optional
from urllib.parse import urlparse
import httpx
import yaml
from app.agents.llm_router import llm_router
from app.core.config import settings
from app.core.exceptions import ExternalProviderError
from app.repositories.vault_repo import VaultRepository

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "research_agent.yaml"

ResearchStepCallback = Optional[Callable[[dict[str, Any]], Awaitable[None]]]


def _load_research_prompt() -> str:
    if PROMPT_PATH.exists():
        data = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
        if data.get("system_prompt"):
            return str(data["system_prompt"]).strip()
    return (
        "You are a Senior Geoscientist & International Geotechnical Standards Specialist. "
        "Synthesize dense, citation-anchored findings using [1], [2], etc."
    )


class ResearchAgent:
    """
    Autonomous Geological, Maritime & Standards Researcher.
    Queries the internal Knowledge Vault semantic index and live external technical sources
    (via Tavily Search API) with 100% real-time SSE telemetry and zero canned fallbacks.
    """

    async def query(
        self,
        query: str,
        scope: str,
        vault_repo: VaultRepository,
        openrouter_key: str = "",
        tavily_key: str = "",
        step_callback: ResearchStepCallback = None,
    ) -> dict[str, Any]:
        sources: list[dict[str, Any]] = []
        steps: list[dict[str, Any]] = []

        # Validate both keys upfront when hybrid search is requested so we fail fast & cleanly
        if scope in ("web", "both", ""):
            self._require_tavily_key(tavily_key)
        llm_router._require_api_key(openrouter_key)

        # Step 1: Internal Knowledge Vault Retrieval
        if scope in ("vault", "both", ""):
            t0 = time.perf_counter()
            vault_running = {
                "id": "vault-rag",
                "kind": "query",
                "status": "running",
                "title": "Searching Knowledge Vault for matching engineering reports & boilerplate...",
                "detail": query[:72],
            }
            if step_callback:
                await step_callback(vault_running)

            matches = await vault_repo.search_similar_chunks(
                query, top_k=4, openrouter_key=openrouter_key
            )
            for chunk, filename, score in matches:
                if score <= 0.02:
                    continue
                sources.append(
                    {
                        "kind": "vault",
                        "site": "Knowledge Vault",
                        "label": chunk.section_type.replace("_", " "),
                        "title": f"{filename} — {chunk.heading_title}",
                        "meta": f"Match {score:.2f}",
                        "snippet": chunk.content_text[:450],
                    }
                )
            vault_ms = max(1, int((time.perf_counter() - t0) * 1000))
            vault_done = {
                "id": "vault-rag",
                "kind": "query",
                "status": "done",
                "title": "Searched Knowledge Vault semantic index",
                "detail": (
                    f"Retrieved {len(sources)} internal report excerpt(s)"
                    if sources
                    else "0 Vault reports indexed — proceeding with live external research"
                ),
                "duration": vault_ms,
            }
            steps.append(vault_done)
            if step_callback:
                await step_callback(vault_done)

        # Step 2: Live External Web & Technical Standards Search via Tavily
        if scope in ("web", "both", ""):
            t1 = time.perf_counter()
            web_running = {
                "id": "web-search",
                "kind": "search",
                "status": "running",
                "title": "Searching external geotechnical standards, regional geology & technical literature...",
                "detail": "Live web & standards verification",
            }
            if step_callback:
                await step_callback(web_running)

            web_sources = await self._search_tavily(query, tavily_key)
            sources.extend(web_sources)
            web_ms = max(1, int((time.perf_counter() - t1) * 1000))
            web_done = {
                "id": "web-search",
                "kind": "search",
                "status": "done",
                "title": "Retrieved live external geotechnical & standards references",
                "detail": f"{len(web_sources)} verified web source(s)",
                "duration": web_ms,
                "results": [
                    {"title": s["title"], "site": s["site"], "url": s.get("url")}
                    for s in web_sources
                ],
            }
            steps.append(web_done)
            if step_callback:
                await step_callback(web_done)

        # Step 3: Grounded Technical Synthesis
        t2 = time.perf_counter()
        synth_running = {
            "id": "synthesize-answer",
            "kind": "thought",
            "status": "running",
            "title": "Synthesizing citation-anchored geotechnical response...",
            "detail": f"Cross-referencing {len(sources)} verified source(s)",
        }
        if step_callback:
            await step_callback(synth_running)

        answer = await self._synthesize_answer(query, sources, openrouter_key)
        synth_ms = max(1, int((time.perf_counter() - t2) * 1000))
        synth_done = {
            "id": "synthesize-answer",
            "kind": "thought",
            "status": "done",
            "title": "Synthesized grounded engineering answer with inline citations",
            "detail": f"{len(sources)} citation source(s) verified",
            "duration": synth_ms,
        }
        steps.append(synth_done)
        if step_callback:
            await step_callback(synth_done)

        return {"sources": sources, "answer": answer, "steps": steps}

    def _require_tavily_key(self, tavily_key_override: str = "") -> str:
        api_key = (tavily_key_override or settings.TAVILY_API_KEY or "").strip()
        if not api_key:
            raise ExternalProviderError(
                "Required search key (TAVILY_API_KEY) is missing in your root .env file. "
                "Add TAVILY_API_KEY to .env and restart the backend server to enable live external research."
            )
        return api_key

    async def _search_tavily(
        self, query: str, tavily_key_override: str = "", max_results: int = 5
    ) -> list[dict[str, Any]]:
        api_key = self._require_tavily_key(tavily_key_override)

        last_err = "Unknown Tavily error"
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": api_key,
                            "query": f"{query} geotechnical engineering standards",
                            "search_depth": "advanced",
                            "max_results": max_results,
                        },
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    parsed: list[dict[str, Any]] = []
                    for r in data.get("results", []):
                        url = (r.get("url") or "").strip()
                        content = (r.get("content") or "").strip()
                        if not url or not content:
                            continue
                        host = urlparse(url).netloc.replace("www.", "") or "web"
                        parsed.append(
                            {
                                "kind": "web",
                                "site": host,
                                "label": "External Technical Reference",
                                "title": (r.get("title") or host).strip(),
                                "meta": f"Score {float(r.get('score', 0.9)):.2f}",
                                "snippet": content[:460],
                                "url": url,
                            }
                        )
                    return parsed
                if resp.status_code in (401, 403):
                    raise ExternalProviderError(
                        "External search authentication failed (HTTP 401/403). Verify TAVILY_API_KEY in your root .env file."
                    )
                last_err = f"HTTP {resp.status_code}"
            except ExternalProviderError:
                raise
            except Exception as exc:
                last_err = str(exc)

        raise ExternalProviderError(
            f"Live external web search failed ({last_err}). Check TAVILY_API_KEY and network connection."
        )

    async def _synthesize_answer(
        self,
        query: str,
        sources: list[dict[str, Any]],
        openrouter_key: str,
    ) -> str:
        context = (
            "\n".join(
                f"[{idx + 1}] ({src['site']} | {src.get('url', 'Internal Vault')}) {src['title']}: {src['snippet']}"
                for idx, src in enumerate(sources)
            )
            if sources
            else "No matching internal Knowledge Vault chunks or external web sources were returned for this query."
        )
        sys_prompt = _load_research_prompt()
        return await llm_router.complete_tier2(
            messages=[
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Question: {query}\n\n"
                        f"Verified Numbered Sources:\n{context}\n\n"
                        "Cite ONLY from the numbered sources above using [1], [2], etc. Never invent citations."
                    ),
                },
            ],
            temperature=0.2,
            api_key_override=openrouter_key,
            max_tokens=3200,
        )
