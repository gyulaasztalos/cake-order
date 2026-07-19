"""Gallery listing: newest-first order, thumbnails, placeholder + hero fallback."""

from __future__ import annotations

from app.routers import orders as orders_router


def _use_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(orders_router, "_GALLERY_DIR", tmp_path)
    orders_router._gallery_cache.clear()
    orders_router._hero_cache = None


def test_gallery_lists_photos_newest_first(tmp_path, monkeypatch):
    cakes = tmp_path / "cakes"
    cakes.mkdir()
    for name in ("IMG_0001.jpeg", "IMG_0002.jpeg", "IMG_0010.jpeg"):
        (cakes / name).write_bytes(b"x")
    _use_dir(monkeypatch, tmp_path)

    photos = orders_router._gallery("cakes")
    assert [p.full for p in photos] == [
        "/static/img/gallery/cakes/IMG_0010.jpeg",
        "/static/img/gallery/cakes/IMG_0002.jpeg",
        "/static/img/gallery/cakes/IMG_0001.jpeg",
    ]
    assert all(not p.placeholder for p in photos)


def test_gallery_uses_thumbnail_when_present_else_full(tmp_path, monkeypatch):
    cakes = tmp_path / "cakes"
    (cakes / "thumbs").mkdir(parents=True)
    (cakes / "IMG_0001.jpeg").write_bytes(b"x")
    (cakes / "IMG_0002.jpeg").write_bytes(b"x")
    (cakes / "thumbs" / "IMG_0002.jpeg").write_bytes(b"t")  # only one has a thumb
    _use_dir(monkeypatch, tmp_path)

    by_full = {p.full: p for p in orders_router._gallery("cakes")}
    assert by_full["/static/img/gallery/cakes/IMG_0002.jpeg"].thumb == (
        "/static/img/gallery/cakes/thumbs/IMG_0002.jpeg"
    )
    # Missing thumb → grid falls back to the full image.
    assert by_full["/static/img/gallery/cakes/IMG_0001.jpeg"].thumb == (
        "/static/img/gallery/cakes/IMG_0001.jpeg"
    )


def test_gallery_falls_back_to_placeholders_when_empty(tmp_path, monkeypatch):
    (tmp_path / "desserts").mkdir()
    _use_dir(monkeypatch, tmp_path)

    photos = orders_router._gallery("desserts")
    assert photos == orders_router._PLACEHOLDER_PHOTOS
    assert all(p.placeholder for p in photos)


def test_hero_image_returns_newest_or_none(tmp_path, monkeypatch):
    _use_dir(monkeypatch, tmp_path)
    # No hero dir at all → None (template shows the SVG).
    assert orders_router._hero_image() is None

    hero = tmp_path / "hero"
    hero.mkdir()
    (hero / "IMG_0005.jpeg").write_bytes(b"x")
    (hero / "IMG_0009.jpeg").write_bytes(b"x")
    orders_router._hero_cache = None
    assert orders_router._hero_image() == "/static/img/gallery/hero/IMG_0009.jpeg"
