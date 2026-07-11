"""
File and asset management for the Deckset Website Generator.

New output layout::

    site/
    ├── index.html
    ├── assets/              (CSS, JS, icons — copied from templates/)
    │   ├── css/
    │   ├── js/
    │   └── favicon.png
    ├── <deck-slug>/
    │   ├── index.html
    │   └── media/           (preserve source sub-paths)
    │       ├── image.jpg
    │       └── subfolder/
    │           └── image.png
    └── ...
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from models import GeneratorConfig, EnhancedPresentation, PresentationInfo, FileOperationError


class FileManager:
    """Manages file operations for the website generator."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Directory setup
    # ------------------------------------------------------------------

    def setup_output_directories(self) -> None:
        """Create the top-level output structure and copy template assets."""
        output_dir = Path(self.config.output_dir)

        for sub in [
            output_dir,
            output_dir / "assets",
            output_dir / "assets" / "css",
            output_dir / "assets" / "js",
        ]:
            try:
                sub.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise FileOperationError(
                    f"Failed to create directory {sub}: {e}",
                    context={"directory_path": str(sub)},
                )

        self.logger.info(f"Set up output directory structure in {output_dir}")
        self.copy_template_assets()

    # ------------------------------------------------------------------
    # Template asset copying
    # ------------------------------------------------------------------

    def copy_template_assets(self) -> None:
        """Copy CSS, JS, and icon files from *templates/* to *site/assets/*."""
        output_dir = Path(self.config.output_dir)

        css_files = ["code_highlighting_styles.css", "slide_styles.css"]
        for css_file in css_files:
            source = Path(self.config.template_dir) / css_file
            if source.exists():
                try:
                    shutil.copy2(source, output_dir / css_file)
                except Exception as e:
                    self.logger.warning(f"Failed to copy CSS {css_file}: {e}")

        css_src = Path(self.config.template_dir) / "assets" / "css"
        css_dst = output_dir / "assets" / "css"
        if css_src.exists():
            css_dst.mkdir(parents=True, exist_ok=True)
            for f in css_src.rglob("*.css"):
                rel = f.relative_to(css_src)
                dest = css_dst / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(f, dest)
                except Exception as e:
                    self.logger.warning(f"Failed to copy CSS asset {rel}: {e}")

        js_src = Path(self.config.template_dir) / "assets" / "js"
        js_dst = output_dir / "assets" / "js"
        if js_src.exists():
            js_dst.mkdir(parents=True, exist_ok=True)
            for js_file in js_src.glob("*.js"):
                try:
                    shutil.copy2(js_file, js_dst / js_file.name)
                except Exception as e:
                    self.logger.warning(f"Failed to copy JS {js_file.name}: {e}")

        self._copy_favicon_assets()
        self._copy_vendor_assets()

    def _copy_favicon_assets(self) -> None:
        assets_src = Path(self.config.template_dir) / "assets"
        assets_dst = Path(self.config.output_dir) / "assets"
        assets_dst.mkdir(parents=True, exist_ok=True)

        for icon in ["favicon.png", "apple-touch-icon.png", "deckset-icon.png"]:
            src = assets_src / icon
            if src.exists():
                try:
                    shutil.copy2(src, assets_dst / icon)
                except Exception as e:
                    self.logger.warning(f"Failed to copy icon {icon}: {e}")

    def _copy_vendor_assets(self) -> None:
        """Copy vendored libraries (highlight.js, MathJax) to *site/assets/vendor/*."""
        vendor_src = Path(self.config.template_dir) / "assets" / "vendor"
        vendor_dst = Path(self.config.output_dir) / "assets" / "vendor"
        if vendor_src.exists():
            try:
                if vendor_dst.exists():
                    shutil.rmtree(vendor_dst)
                shutil.copytree(vendor_src, vendor_dst)
                self.logger.debug(f"Copied vendor assets: {vendor_src} -> {vendor_dst}")
            except Exception as e:
                self.logger.warning(f"Failed to copy vendor assets: {e}")

    # ------------------------------------------------------------------
    # Per-deck media handling
    # ------------------------------------------------------------------

    def deck_output_dir(self, info: PresentationInfo) -> Path:
        """Return ``site/<slug>/``."""
        return Path(self.config.output_dir) / info.slug

    def deck_media_dir(self, info: PresentationInfo) -> Path:
        """Return ``site/<slug>/media/``."""
        return self.deck_output_dir(info) / "media"

    def process_presentation_files(self, presentation: EnhancedPresentation) -> None:
        """Copy all media for *presentation* into ``site/<slug>/media/``."""
        media_dir = self.deck_media_dir(presentation.info)
        media_dir.mkdir(parents=True, exist_ok=True)

        folder = Path(presentation.info.folder_path)

        for slide in presentation.slides:
            for img in slide.background_images:
                self._copy_media(img, folder, media_dir, presentation.info)
            for img in slide.inline_images:
                self._copy_media(img, folder, media_dir, presentation.info)
            for vid in slide.videos:
                if vid.embed_type == "local":
                    self._copy_media(vid, folder, media_dir, presentation.info)
            for aud in slide.audio:
                self._copy_media(aud, folder, media_dir, presentation.info)

        self.copy_preview_image(presentation.info)
        self._copy_custom_css(presentation.info)
        self.logger.info(f"Processed media for: {presentation.info.title}")

    def _copy_media(self, media_obj, source_folder: Path, media_dir: Path, info: PresentationInfo) -> None:
        """Copy a single media file preserving its relative sub-path.

        ``src_path`` is typically relative to the presentation folder.  We
        preserve any sub-directories so that two files named ``1.png`` in
        different sub-folders don't collide.
        """
        src = Path(media_obj.src_path)
        if not src.is_absolute():
            src = source_folder / src

        if not src.exists():
            self.logger.warning(f"Media source not found: {src}")
            return

        try:
            rel = src.relative_to(source_folder)
        except ValueError:
            rel = Path(src.name)

        dest = media_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(src, dest)
        except Exception as e:
            self.logger.warning(f"Failed to copy media {src}: {e}")
            return

        media_obj.web_path = f"media/{rel.as_posix()}"
        self.logger.debug(f"Copied media: {src} -> {dest}")

    def _copy_custom_css(self, info: PresentationInfo) -> None:
        """Copy ``custom.css`` from the deck folder into ``site/<slug>/custom.css``."""
        src = Path(info.folder_path) / "custom.css"
        if not src.exists():
            return
        dest = self.deck_output_dir(info) / "custom.css"
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
            self.logger.debug(f"Copied custom CSS for {info.title}")
        except Exception as e:
            self.logger.warning(f"Failed to copy custom.css for {info.title}: {e}")

    # ------------------------------------------------------------------
    # Preview images
    # ------------------------------------------------------------------

    def copy_preview_image(self, info: PresentationInfo) -> None:
        if not info.preview_image:
            return

        src = Path(info.preview_image)
        if not src.is_absolute():
            src = Path(info.folder_path) / src

        if not src.exists():
            self.logger.warning(f"Preview image not found: {src}")
            info.preview_image = None
            return

        dest_dir = self.deck_output_dir(info)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"preview{src.suffix}"

        try:
            shutil.copy2(src, dest)
            info.preview_image = f"{info.slug}/preview{src.suffix}"
        except Exception as e:
            self.logger.warning(f"Failed to copy preview: {e}")
            info.preview_image = None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup_output_directory(
        self, presentations: List[EnhancedPresentation], *, single: Optional[str] = None
    ) -> None:
        """Remove deck directories that no longer exist in source.

        When *single* is set, only that deck's directory is touched.
        """
        output = Path(self.config.output_dir)
        valid_slugs = {p.info.slug for p in presentations}

        if single:
            return

        for item in output.iterdir():
            if not item.is_dir():
                continue
            if item.name == "assets":
                continue
            if item.name not in valid_slugs and not any(
                slug.startswith(item.name + "/") for slug in valid_slugs
            ):
                try:
                    shutil.rmtree(item)
                    self.logger.info(f"Removed stale deck directory: {item}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {item}: {e}")

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def process_all_presentations(self, presentations: List[EnhancedPresentation]) -> None:
        self.setup_output_directories()
        for p in presentations:
            self.process_presentation_files(p)
        self.cleanup_output_directory(presentations)
