"""Tests for FileManager — new output layout.

Layout under test::

    site/
    ├── index.html
    ├── assets/
    ├── <slug>/
    │   ├── index.html
    │   └── media/<relative path>
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from models import (
    GeneratorConfig, PresentationInfo, EnhancedPresentation,
    ProcessedSlide, ProcessedImage, ProcessedVideo, ProcessedAudio,
    DecksetConfig, SlideConfig, ImageModifiers, MediaModifiers,
)
from file_manager import FileManager


class TestPresentationSlug(unittest.TestCase):
    """PresentationInfo.slug property."""

    def test_simple(self):
        info = _info("01-fix-messaging")
        self.assertEqual(info.slug, "01-fix-messaging")

    def test_nested(self):
        info = _info("Examples/10 Deckset basics")
        self.assertEqual(info.slug, "examples/10-deckset-basics")

    def test_special_chars(self):
        info = _info("RAG Workshop!")
        self.assertEqual(info.slug, "rag-workshop")


class TestDeckOutputPaths(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = GeneratorConfig(output_dir=self.tmpdir)
        self.fm = FileManager(self.config)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_deck_output_dir(self):
        info = _info("01-foo")
        self.assertEqual(self.fm.deck_output_dir(info), Path(self.tmpdir) / "01-foo")

    def test_deck_media_dir(self):
        info = _info("01-foo")
        self.assertEqual(self.fm.deck_media_dir(info), Path(self.tmpdir) / "01-foo" / "media")


class TestMediaCopy(unittest.TestCase):
    """Media files are copied preserving sub-paths."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.src_dir = Path(self.tmpdir) / "src" / "deck"
        self.src_dir.mkdir(parents=True)
        self.out_dir = Path(self.tmpdir) / "site"
        self.config = GeneratorConfig(output_dir=str(self.out_dir))
        self.fm = FileManager(self.config)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, rel: str) -> Path:
        p = self.src_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
        return p

    def _pres(self, images):
        info = _info("deck", folder_path=str(self.src_dir))
        slide = ProcessedSlide(index=1, content="", body_html="", slide_config=SlideConfig())
        for img in images:
            slide.inline_images.append(img)
        return EnhancedPresentation(info=info, slides=[slide], config=DecksetConfig())

    def test_flat_image_copied(self):
        self._write("photo.jpg")
        img = _image("photo.jpg")
        pres = self._pres([img])
        self.fm.process_presentation_files(pres)
        self.assertTrue((self.out_dir / "deck" / "media" / "photo.jpg").exists())
        self.assertEqual(img.web_path, "media/photo.jpg")

    def test_subpath_preserved(self):
        self._write("sub/deep/pic.png")
        img = _image("sub/deep/pic.png")
        pres = self._pres([img])
        self.fm.process_presentation_files(pres)
        self.assertTrue((self.out_dir / "deck" / "media" / "sub" / "deep" / "pic.png").exists())
        self.assertEqual(img.web_path, "media/sub/deep/pic.png")

    def test_collision_avoided_by_subpath(self):
        """Two images named 1.png in different sub-folders don't collide."""
        self._write("a/1.png")
        self._write("b/1.png")
        img_a = _image("a/1.png")
        img_b = _image("b/1.png")
        pres = self._pres([img_a, img_b])
        self.fm.process_presentation_files(pres)
        self.assertTrue((self.out_dir / "deck" / "media" / "a" / "1.png").exists())
        self.assertTrue((self.out_dir / "deck" / "media" / "b" / "1.png").exists())

    def test_missing_file_warns(self):
        img = _image("nonexistent.png")
        pres = self._pres([img])
        with self.assertLogs("file_manager", level="WARNING") as log:
            self.fm.process_presentation_files(pres)
        self.assertTrue(any("not found" in m for m in log.output))


class TestCleanup(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = GeneratorConfig(output_dir=self.tmpdir)
        self.fm = FileManager(self.config)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stale_deck_removed(self):
        stale = Path(self.tmpdir) / "old-deck"
        stale.mkdir()
        (stale / "index.html").write_text("old")
        pres = _minimal_pres("new-deck")
        self.fm.cleanup_output_directory([pres])
        self.assertFalse(stale.exists())

    def test_assets_preserved(self):
        assets = Path(self.tmpdir) / "assets"
        assets.mkdir()
        self.fm.cleanup_output_directory([])
        self.assertTrue(assets.exists())

    def test_single_mode_skips_cleanup(self):
        stale = Path(self.tmpdir) / "old-deck"
        stale.mkdir()
        pres = _minimal_pres("new-deck")
        self.fm.cleanup_output_directory([pres], single="new-deck")
        self.assertTrue(stale.exists())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _info(name: str, **kw) -> PresentationInfo:
    defaults = dict(
        folder_name=name,
        folder_path=kw.pop("folder_path", f"/tmp/{name}"),
        markdown_path=f"/tmp/{name}/{name}.md",
        title=name.replace("-", " ").title(),
    )
    defaults.update(kw)
    return PresentationInfo(**defaults)


def _image(src: str) -> ProcessedImage:
    mods = ImageModifiers(placement="inline", scaling="fit", filter="original")
    return ProcessedImage(src_path=src, web_path=src, modifiers=mods, alt_text="")


def _minimal_pres(name: str) -> EnhancedPresentation:
    info = _info(name)
    return EnhancedPresentation(info=info, slides=[], config=DecksetConfig())
