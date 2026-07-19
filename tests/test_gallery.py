"""Gallery listing: newest-first order + placeholder fallback."""

from __future__ import annotations

from app.routers import orders as orders_router


def test_gallery_lists_photos_newest_first(tmp_path, monkeypatch):
    cakes = tmp_path / "cakes"
    cakes.mkdir()
    for name in ("IMG_0001.jpeg", "IMG_0002.jpeg", "IMG_0010.jpeg"):
        (cakes / name).write_bytes(b"x")
    monkeypatch.setattr(orders_router, "_GALLERY_DIR", tmp_path)
    orders_router._gallery_cache.clear()

    urls = orders_router._gallery("cakes")
    assert urls == [
        "/static/img/gallery/cakes/IMG_0010.jpeg",
        "/static/img/gallery/cakes/IMG_0002.jpeg",
        "/static/img/gallery/cakes/IMG_0001.jpeg",
    ]


def test_gallery_falls_back_to_placeholders_when_empty(tmp_path, monkeypatch):
    (tmp_path / "desserts").mkdir()
    monkeypatch.setattr(orders_router, "_GALLERY_DIR", tmp_path)
    orders_router._gallery_cache.clear()

    urls = orders_router._gallery("desserts")
    assert urls == orders_router._PLACEHOLDERS
