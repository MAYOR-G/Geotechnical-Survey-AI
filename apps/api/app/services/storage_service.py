from pathlib import Path
import re
import time
import uuid
from app.core.config import settings
from app.core.exceptions import ExternalProviderError


def sanitize_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    clean_stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", stem).strip("_") or "file"
    return f"{clean_stem}{suffix}"


def validate_supabase_config() -> None:
    has_url = bool((settings.SUPABASE_URL or "").strip())
    has_key = bool((settings.SUPABASE_SERVICE_ROLE_KEY or "").strip())
    if has_url != has_key:
        missing = "SUPABASE_SERVICE_ROLE_KEY" if has_url else "SUPABASE_URL"
        raise ExternalProviderError(
            f"Partial Supabase configuration detected: {missing} is missing in .env. "
            "Configure both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY, or leave both empty for local disk storage."
        )


class StorageService:
    """Manages local storage buckets with clean HTTP paths, deterministic export overwrite, and orphan cleanup."""

    VALID_BUCKETS = {
        "branding-assets",
        "equipment-gallery",
        "project-inputs",
        "compiled-exports",
    }

    def save_bytes(
        self,
        bucket: str,
        filename: str,
        content: bytes,
        deterministic: bool = False,
    ) -> tuple[str, Path]:
        validate_supabase_config()
        if bucket not in self.VALID_BUCKETS:
            raise ValueError(f"Invalid bucket: {bucket}")
        clean_name = sanitize_filename(filename)
        safe_name = clean_name if deterministic else f"{uuid.uuid4().hex[:8]}_{clean_name}"
        target_dir = settings.STORAGE_ROOT / bucket
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / safe_name
        target_path.write_bytes(content)
        if deterministic:
            stamp = int(time.time() * 1000)
            url = f"/api/v1/storage/{bucket}/{safe_name}?v={stamp}"
        else:
            url = f"/api/v1/storage/{bucket}/{safe_name}"
        return url, target_path

    def resolve_path(self, url_or_rel: str | None) -> Path | None:
        if not url_or_rel:
            return None
        clean_url = url_or_rel.split("?", 1)[0].split("#", 1)[0]
        prefix = "/api/v1/storage/"
        if prefix in clean_url:
            rel = clean_url.split(prefix, 1)[1]
            candidate = (settings.STORAGE_ROOT / rel).resolve()
            if candidate.exists() and settings.STORAGE_ROOT.resolve() in candidate.parents:
                return candidate
        return None

    def delete_by_url(self, url_or_rel: str | None) -> bool:
        resolved = self.resolve_path(url_or_rel)
        if resolved and resolved.exists() and resolved.is_file():
            try:
                resolved.unlink()
                return True
            except OSError:
                return False
        return False
