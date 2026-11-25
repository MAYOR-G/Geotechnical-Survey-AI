import math
import re
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agents.llm_router import llm_router
from app.models.vault import GalleryAsset, VaultChunk, VaultDocument


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class VaultRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_documents(self) -> list[VaultDocument]:
        res = await self.session.execute(
            select(VaultDocument)
            .options(selectinload(VaultDocument.chunks))
            .order_by(VaultDocument.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_document(self, doc_id: str) -> Optional[VaultDocument]:
        res = await self.session.execute(
            select(VaultDocument)
            .options(selectinload(VaultDocument.chunks))
            .where(VaultDocument.id == doc_id)
        )
        return res.scalar_one_or_none()

    async def create_document(
        self,
        doc: VaultDocument,
        chunks: list[VaultChunk],
        openrouter_key: str = "",
    ) -> VaultDocument:
        pending_chunks = [c for c in chunks if not c.embedding_json]
        if pending_chunks:
            texts = [f"{c.heading_title}\n{c.content_text}"[:6000] for c in pending_chunks]
            vectors: list[list[float]] = []
            for start in range(0, len(texts), 24):
                batch = texts[start : start + 24]
                vectors.extend(
                    await llm_router.embed(batch, api_key_override=openrouter_key)
                )
            for chunk, vec in zip(pending_chunks, vectors):
                chunk.embedding_json = vec

        if not doc.id:
            doc.id = f"vdoc-{uuid.uuid4().hex[:10]}"
        self.session.add(doc)
        await self.session.flush()
        for chunk in chunks:
            chunk.vault_document_id = doc.id
            self.session.add(chunk)
        await self.session.flush()
        return await self.get_document(doc.id) or doc

    async def delete_document(self, doc_id: str) -> bool:
        doc = await self.get_document(doc_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.flush()
        return True

    async def search_similar_chunks(
        self,
        query: str,
        section_type: Optional[str] = None,
        top_k: int = 4,
        openrouter_key: str = "",
    ) -> list[tuple[VaultChunk, str, float]]:
        stmt = select(VaultChunk, VaultDocument.filename).join(
            VaultDocument, VaultChunk.vault_document_id == VaultDocument.id
        )
        if section_type:
            stmt = stmt.where(VaultChunk.section_type == section_type)
        res = await self.session.execute(stmt)
        rows = res.all()
        if not rows:
            return []

        q_vec = (await llm_router.embed([query], api_key_override=openrouter_key))[0]
        q_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))

        scored: list[tuple[VaultChunk, str, float]] = []
        for chunk, filename in rows:
            emb = chunk.embedding_json or []
            cos = cosine_similarity(q_vec, emb)
            c_terms = set(
                re.findall(
                    r"[a-z0-9_]+",
                    f"{chunk.heading_title} {chunk.content_text}".lower(),
                )
            )
            overlap = len(q_terms & c_terms) / max(len(q_terms), 1)
            score = 0.80 * cos + 0.20 * overlap
            scored.append((chunk, filename, score))

        scored.sort(key=lambda item: item[2], reverse=True)
        return scored[:top_k]

    async def list_gallery(self) -> list[GalleryAsset]:
        res = await self.session.execute(
            select(GalleryAsset).order_by(GalleryAsset.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_gallery_asset(self, asset_id: str) -> Optional[GalleryAsset]:
        res = await self.session.execute(
            select(GalleryAsset).where(GalleryAsset.id == asset_id)
        )
        return res.scalar_one_or_none()

    async def create_gallery_asset(self, asset: GalleryAsset) -> GalleryAsset:
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def delete_gallery_asset(self, asset_id: str) -> bool:
        asset = await self.get_gallery_asset(asset_id)
        if not asset:
            return False
        await self.session.delete(asset)
        await self.session.flush()
        return True
