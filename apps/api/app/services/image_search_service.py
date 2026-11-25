import io
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
import httpx
from PIL import Image
from app.core.config import settings
from app.core.exceptions import ExternalProviderError, FileParseError
from app.models.vault import GalleryAsset
from app.services.storage_service import StorageService


class ImageSearchService:
    """
    Tier-2 External Technical Image Discovery & Local Caching Service.
    Queries Tavily Search (`include_images=True`, `include_image_descriptions=True`) to discover
    relevant geological maps, survey vessels, drill rigs, and HDD diagrams when no local photo exists
    in the Knowledge Vault, and caches selected images locally as validated PNG/JPEG files so Typst
    and Word compilation never break due to hotlink blocking or dead URLs.
    """

    BROWSER_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()

    def _require_tavily_key(self, tavily_key_override: str = "") -> str:
        api_key = (tavily_key_override or settings.TAVILY_API_KEY or "").strip()
        if not api_key:
            raise ExternalProviderError(
                "External image search requires TAVILY_API_KEY in your root .env file."
            )
        return api_key

    async def search_external_images(
        self,
        query: str,
        max_results: int = 8,
        tavily_key_override: str = "",
    ) -> list[dict[str, Any]]:
        api_key = self._require_tavily_key(tavily_key_override)
        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            async with httpx.AsyncClient(timeout=24.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": clean_q,
                        "search_depth": "advanced",
                        "include_images": True,
                        "include_image_descriptions": True,
                        "max_results": max(5, max_results),
                    },
                )
        except Exception as exc:
            raise ExternalProviderError(
                f"External image search failed: {exc}"
            ) from exc

        if resp.status_code in (401, 403):
            raise ExternalProviderError(
                "External image search authentication failed. Verify TAVILY_API_KEY in .env."
            )
        if resp.status_code != 200:
            raise ExternalProviderError(
                f"External image search returned HTTP {resp.status_code}."
            )

        data = resp.json()
        raw_images = data.get("images") or []
        text_results = data.get("results") or []

        fallback_source_url = text_results[0].get("url", "") if text_results else ""
        items: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for idx, img_entry in enumerate(raw_images):
            if isinstance(img_entry, dict):
                img_url = str(img_entry.get("url") or "").strip()
                desc = str(img_entry.get("description") or "").strip()
            else:
                img_url = str(img_entry or "").strip()
                desc = ""

            if not img_url.startswith(("http://", "https://")) or img_url in seen_urls:
                continue
            if any(bad in img_url.lower() for bad in (".svg", "logo", "icon", "avatar", "sprite", "1x1")):
                continue
            seen_urls.add(img_url)

            parsed_img = urlparse(img_url)
            domain = parsed_img.netloc.replace("www.", "") or "external-source"
            matched_page = (
                text_results[idx % len(text_results)] if text_results else {}
            )
            source_page_url = str(matched_page.get("url") or fallback_source_url or img_url)
            source_domain = urlparse(source_page_url).netloc.replace("www.", "") or domain

            title = desc[:140] if desc else f"{clean_q.title()} ({source_domain})"
            items.append(
                {
                    "id": f"ext-img-{idx + 1}",
                    "image_url": img_url,
                    "title": title,
                    "description": desc or f"Technical reference visual sourced via {source_domain}",
                    "source_domain": source_domain,
                    "source_url": source_page_url,
                }
            )
            if len(items) >= max_results:
                break

        return items

    async def cache_external_image(
        self,
        image_url: str,
        title: str,
        caption: str = "",
        category: str = "map",
        source_url: str = "",
    ) -> tuple[GalleryAsset, Path]:
        """Download external image, normalize to high-compatibility PNG/JPEG, and cache in equipment-gallery."""
        if not image_url.startswith(("http://", "https://")):
            raise FileParseError("Invalid external image URL.")

        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                follow_redirects=True,
                headers=self.BROWSER_HEADERS,
            ) as client:
                resp = await client.get(image_url)
                if resp.status_code != 200 or len(resp.content) < 1500:
                    raise FileParseError(
                        f"Remote image host returned HTTP {resp.status_code} or an empty image."
                    )
                raw_bytes = resp.content
        except FileParseError:
            raise
        except Exception as exc:
            raise FileParseError(
                f"Could not download external image for local caching: {exc}"
            ) from exc

        # Validate & convert to clean RGB PNG/JPEG so Typst and python-docx never fail
        try:
            with Image.open(io.BytesIO(raw_bytes)) as im:
                width, height = im.size
                if width < 120 or height < 90:
                    raise FileParseError(
                        f"Image resolution ({width}x{height}) is too small for A4 engineering publication."
                    )
                out_buf = io.BytesIO()
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.split()[3])
                    bg.save(out_buf, format="PNG", optimize=True)
                    ext = ".png"
                else:
                    rgb = im.convert("RGB")
                    rgb.save(out_buf, format="JPEG", quality=92)
                    ext = ".jpg"
                normalized_bytes = out_buf.getvalue()
        except FileParseError:
            raise
        except Exception as exc:
            raise FileParseError(
                f"Downloaded file is not a valid raster image: {exc}"
            ) from exc

        src_domain = urlparse(source_url or image_url).netloc.replace("www.", "") or "External Technical Source"
        safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", title)[:42].strip("_") or "external_visual"
        local_url, saved_path = self.storage.save_bytes(
            "equipment-gallery", f"{safe_stem}{ext}", normalized_bytes
        )

        clean_title = title.strip()[:220] or f"Technical Figure ({src_domain})"
        base_cap = (caption or clean_title).strip()
        attributed_caption = (
            base_cap
            if "source:" in base_cap.lower()
            else f"{base_cap} (Source: {src_domain})"
        )
        valid_cat = (
            category
            if category in ("vessel", "drill_rig", "lab_equipment", "map", "field_photo")
            else "map"
        )
        asset = GalleryAsset(
            title=clean_title,
            default_caption=attributed_caption,
            category=valid_cat,
            file_url=local_url,
            tags=["external_cached", valid_cat, src_domain]
            + ([source_url[:180]] if source_url else []),
        )
        return asset, saved_path

    async def find_and_cache_best_visual(
        self,
        query: str,
        fallback_title: str,
        category: str = "map",
        tavily_key_override: str = "",
    ) -> GalleryAsset | None:
        """Used autonomously by the Drafting Agent when no Vault visual matches a required figure."""
        try:
            candidates = await self.search_external_images(
                query=query, max_results=5, tavily_key_override=tavily_key_override
            )
        except Exception:
            return None

        for cand in candidates:
            try:
                asset, _ = await self.cache_external_image(
                    image_url=cand["image_url"],
                    title=cand["title"] or fallback_title,
                    caption=f"{fallback_title} — {cand['description'][:140]}",
                    category=category,
                    source_url=cand.get("source_url", ""),
                )
                return asset
            except Exception:
                continue
        return None
