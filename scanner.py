"""
Repository scanner for discovering Deckset presentations.

This module provides functionality to scan a repository for presentation folders
and identify markdown files that represent Deckset presentations.

Implementation follows requirements:
1.1: Scan all folders in the repository root directory
1.2: Identify folders containing markdown files as presentation folders
1.3: When multiple markdown files exist, use file with same name as folder
1.4: If no markdown file matches folder name, use first alphabetically
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import re

from models import PresentationInfo, GeneratorConfig, GeneratorError, ScanningError


# Set up logging
logger = logging.getLogger(__name__)


class PresentationScanner:
    """Scans repository for presentation folders and markdown files."""

    def __init__(self, config: GeneratorConfig):
        """
        Initialize the scanner with configuration.
        
        Args:
            config: Generator configuration with exclude folders and other settings
        """
        self.config = config

    def scan_presentations(self, root_path: str) -> List[PresentationInfo]:
        """
        Scan repository for presentation folders and markdown files.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            List of PresentationInfo objects for discovered presentations
            
        Raises:
            GeneratorError: If scanning fails due to invalid path or permissions
        """
        try:
            root_path = Path(root_path).resolve()
            logger.info(f"Scanning presentations in: {root_path}")

            if not root_path.exists():
                raise ScanningError(f"Root path does not exist: {root_path}")

            if not root_path.is_dir():
                raise ScanningError(f"Root path is not a directory: {root_path}")

            presentations = []

            # Get all items in directory, excluding hidden and system files
            try:
                items = [item for item in root_path.iterdir() if not item.name.startswith('.')]
                items.sort(key=lambda x: x.name.lower())  # Sort for consistent results
            except OSError as e:
                raise ScanningError(f"Failed to read directory {root_path}: {e}")

            for item in items:
                if item.is_dir() and self.is_presentation_folder(str(item)):
                    try:
                        # Check if this folder contains multiple independent presentations
                        if self._has_multiple_independent_presentations(item):
                            # Handle each markdown file as a separate presentation
                            markdown_files = sorted(item.glob("*.md"))
                            for markdown_file in markdown_files:
                                presentation_info = self._create_presentation_info_from_file(item, markdown_file)
                                if presentation_info:
                                    presentations.append(presentation_info)
                                    logger.info(f"Found presentation: {presentation_info.title} in {item.name}/{markdown_file.name}")
                        else:
                            # Handle as single presentation folder (existing behavior)
                            presentation_info = self._create_presentation_info(item)
                            if presentation_info:
                                presentations.append(presentation_info)
                                logger.info(f"Found presentation: {presentation_info.title} in {item.name}")
                    except Exception as e:
                        # Log error with context but continue processing other folders (graceful degradation)
                        logger.warning(
                            f"Failed to process folder {item.name}: {e}",
                            extra={
                                "folder_path": str(item),
                                "folder_name": item.name,
                                "error_type": type(e).__name__
                            }
                        )
                        continue

            logger.info(f"Found {len(presentations)} presentations")
            return presentations
        except ScanningError:
            raise
        except Exception as e:
            raise ScanningError(f"Unexpected error during scanning: {e}")

    def find_markdown_file(self, folder_path: str) -> Optional[str]:
        """
        Find the appropriate markdown file in a presentation folder.
        
        Priority:
        1. File with same name as folder
        2. First markdown file alphabetically
        
        Args:
            folder_path: Path to the presentation folder
            
        Returns:
            Path to the markdown file, or None if not found
        """
        folder_path = Path(folder_path)
        folder_name = folder_path.name

        # Look for file with same name as folder (Requirement 1.3)
        preferred_file = folder_path / f"{folder_name}.md"
        if preferred_file.exists():
            logger.debug(f"Found matching markdown file: {preferred_file}")
            return str(preferred_file)

        # Find all markdown files and return first alphabetically (Requirement 1.4)
        markdown_files = sorted(folder_path.glob("*.md"))
        if markdown_files:
            logger.debug(f"Using first alphabetical markdown file: {markdown_files[0]}")
            return str(markdown_files[0])

        logger.debug(f"No markdown files found in {folder_path}")
        return None

    def extract_presentation_title(self, markdown_path: str, use_filename_fallback: bool = False) -> str:
        """
        Extract presentation title from markdown filename.
        
        Args:
            markdown_path: Path to the markdown file
            use_filename_fallback: Legacy parameter, kept for compatibility but now ignored since we always use filename
            
        Returns:
            Presentation title formatted from the filename
        """
        try:
            # Always use filename-based title extraction
            return self._format_filename_as_title(Path(markdown_path).stem)

        except Exception as e:
            # Fallback to basic filename if formatting fails
            logger.error(
                f"Failed to format filename as title for {markdown_path}: {e}",
                extra={
                    "markdown_path": markdown_path,
                    "error_type": type(e).__name__,
                    "fallback_used": True
                }
            )
            return Path(markdown_path).stem

    def _extract_title_from_frontmatter(self, content: str) -> Optional[str]:
        """
        Extract title from YAML frontmatter if present.
        
        Args:
            content: Markdown content
            
        Returns:
            Title from frontmatter or None if not found
        """
        try:
            # Check if content has standard frontmatter (between --- markers)
            if content.startswith('---'):
                end_idx = content.find('---', 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx].strip()
                    for line in frontmatter.split('\n'):
                        if line.startswith('title:'):
                            return line.split('title:', 1)[1].strip().strip('"\'')

            # Check for Deckset-style frontmatter (no --- delimiters, just key: value at start)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or ':' not in line:
                    # If we hit an empty line or line without colon, we're done with frontmatter
                    if line.startswith('#'):
                        # Found first header, stop looking
                        break
                    continue

                if line.startswith('title:'):
                    return line.split('title:', 1)[1].strip().strip('"\'')

        except Exception:
            pass
        return None

    def is_presentation_folder(self, folder_path: str) -> bool:
        """
        Check if a folder is a presentation folder.
        
        Args:
            folder_path: Path to check
            
        Returns:
            True if folder contains markdown files and is not excluded
        """
        folder_path = Path(folder_path)
        folder_name = folder_path.name

        # Skip excluded folders
        if folder_name in self.config.exclude_folders:
            logger.debug(f"Skipping excluded folder: {folder_name}")
            return False

        # Skip hidden folders
        if folder_name.startswith('.'):
            logger.debug(f"Skipping hidden folder: {folder_name}")
            return False

        # Check if folder contains markdown files (Requirement 1.2)
        markdown_files = list(folder_path.glob("*.md"))
        has_markdown = len(markdown_files) > 0

        if has_markdown:
            logger.debug(f"Found presentation folder: {folder_name} with {len(markdown_files)} markdown files")

        return has_markdown

    def count_slides(self, markdown_path: str) -> int:
        """
        Count the number of slides in a markdown file.
        
        Args:
            markdown_path: Path to the markdown file
            
        Returns:
            Number of slides (separated by "---")
        """
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count slide separators and add 1 for the first slide
            slide_count = content.count('\n---\n') + 1
            return slide_count
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.warning(
                f"Failed to count slides in {markdown_path}: {e}",
                extra={
                    "markdown_path": markdown_path,
                    "error_type": type(e).__name__,
                    "fallback_count": 0
                }
            )
            return 0
        except Exception as e:
            logger.error(
                f"Unexpected error counting slides in {markdown_path}: {e}",
                extra={
                    "markdown_path": markdown_path,
                    "error_type": type(e).__name__,
                    "fallback_count": 0
                }
            )
            return 0

    def find_preview_image(self, folder_path: str) -> Optional[str]:
        """
        Find a suitable preview image for the presentation.
        
        Args:
            folder_path: Path to the presentation folder
            
        Returns:
            Path to the preview image, or None if not found
        """
        folder_path = Path(folder_path)

        # Look for slides folder
        slides_folder = folder_path / "slides"
        if slides_folder.exists() and slides_folder.is_dir():
            # Look for first slide image (typically named 1.png or similar)
            for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                first_slide = slides_folder / f"1{ext}"
                if first_slide.exists():
                    return str(first_slide)

            # If no numbered slide found, use first image in folder
            image_files = []
            for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                image_files.extend(slides_folder.glob(f"*{ext}"))

            if image_files:
                return str(sorted(image_files)[0])

        # Look for images directly in presentation folder
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.gif']:
            image_files.extend(folder_path.glob(f"*{ext}"))

        if image_files:
            return str(sorted(image_files)[0])

        return None

    def extract_first_image_from_markdown(self, markdown_path: str) -> Optional[str]:
        """
        Extract the first image reference from markdown content.
        
        Args:
            markdown_path: Path to the markdown file
            
        Returns:
            Path to the first image found in the content, or None if no images found
        """
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract image references using regex pattern: ![alt](path)
            import re
            image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpe?g|gif|bmp|webp|svg))\)', re.IGNORECASE)
            matches = image_pattern.findall(content)

            if matches:
                # Return the path of the first image found
                first_image_path = matches[0][1]  # matches[0] is (alt_text, path)

                # Resolve relative to presentation folder
                markdown_folder = Path(markdown_path).parent
                if not Path(first_image_path).is_absolute():
                    full_path = markdown_folder / first_image_path
                    if full_path.exists():
                        return str(full_path)

                return first_image_path

            return None

        except Exception as e:
            logger.warning(f"Failed to extract first image from {markdown_path}: {e}")
            return None

    def _create_presentation_info(self, folder_path: Path) -> Optional[PresentationInfo]:
        """
        Create PresentationInfo object for a discovered folder.
        
        Args:
            folder_path: Path to the presentation folder
            
        Returns:
            PresentationInfo object or None if no markdown file found
        """
        markdown_path = self.find_markdown_file(str(folder_path))
        if not markdown_path:
            return None

        title = self.extract_presentation_title(markdown_path)
        # First try to extract image from markdown content, then fallback to folder images
        preview_image = self.extract_first_image_from_markdown(markdown_path)
        if not preview_image:
            preview_image = self.find_preview_image(str(folder_path))
        slide_count = self.count_slides(markdown_path)

        # Get last modified time
        try:
            last_modified = datetime.fromtimestamp(os.path.getmtime(markdown_path))
        except OSError:
            last_modified = None

        return PresentationInfo(
            folder_name=folder_path.name,
            folder_path=str(folder_path),
            markdown_path=markdown_path,
            title=title,
            preview_image=preview_image,
            slide_count=slide_count,
            last_modified=last_modified
        )

    def _has_multiple_independent_presentations(self, folder_path: Path) -> bool:
        """
        Determine if a folder contains multiple independent presentations.
        
        This is true when:
        1. The folder contains multiple markdown files, AND
        2. No markdown file matches the folder name (indicating they are not meant to be one presentation), AND
        
        Args:
            folder_path: Path to the folder to check
            
        Returns:
            True if folder contains multiple independent presentations
        """
        markdown_files = list(folder_path.glob("*.md"))

        # Must have multiple markdown files
        if len(markdown_files) <= 1:
            return False

        # Check if any markdown file matches the folder name (single presentation indicator)
        folder_name = folder_path.name
        folder_markdown = folder_path / f"{folder_name}.md"
        if folder_markdown.exists():
            return False

        return True

    def _create_presentation_info_from_file(self, folder_path: Path, markdown_file: Path) -> Optional[PresentationInfo]:
        """
        Create PresentationInfo object for a specific markdown file within a folder.
        
        This is used when a folder contains multiple independent presentations.
        
        Args:
            folder_path: Path to the folder containing the presentation
            markdown_file: Path to the specific markdown file
            
        Returns:
            PresentationInfo object or None if creation fails
        """
        try:
            # Extract title from the markdown file with folder name inclusion
            title = self._create_title_with_folder_name(folder_path, markdown_file)

            # For multiple presentations in one folder, use the markdown filename (without extension) as a unique identifier
            markdown_name = markdown_file.stem
            unique_folder_name = f"{folder_path.name}/{markdown_name}"

            # Look for preview image - first try markdown content, then markdown-specific, then any image in folder
            preview_image = self.extract_first_image_from_markdown(str(markdown_file))
            if not preview_image:
                preview_image = self._find_preview_image_for_file(folder_path, markdown_file)
            if not preview_image:
                preview_image = self.find_preview_image(str(folder_path))

            slide_count = self.count_slides(str(markdown_file))

            # Get last modified time
            try:
                last_modified = datetime.fromtimestamp(markdown_file.stat().st_mtime)
            except OSError:
                last_modified = None

            return PresentationInfo(
                folder_name=unique_folder_name,  # Use combined path to make it unique
                folder_path=str(folder_path),
                markdown_path=str(markdown_file),
                title=title,
                preview_image=preview_image,
                slide_count=slide_count,
                last_modified=last_modified
            )
        except Exception as e:
            logger.warning(f"Failed to create presentation info for {markdown_file}: {e}")
            return None

    def _find_preview_image_for_file(self, folder_path: Path, markdown_file: Path) -> Optional[str]:
        """
        Find a preview image specifically for a markdown file.
        
        Looks for images with the same base name as the markdown file.
        
        Args:
            folder_path: Path to the folder
            markdown_file: Path to the markdown file
            
        Returns:
            Path to preview image or None if not found
        """
        markdown_stem = markdown_file.stem

        # Look for image with same base name as markdown file
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            potential_image = folder_path / f"{markdown_stem}{ext}"
            if potential_image.exists():
                return str(potential_image)

        return None

    def _format_filename_as_title(self, filename_stem: str) -> str:
        """
        Format a markdown filename stem as a presentation title.
        
        This removes numeric prefixes and applies basic formatting:
        - "10 Deckset basics" → "Deckset Basics"
        - "30 Big text" → "Big Text"
        - "Docker Kubernetes 101" → "Docker Kubernetes 101"
        - "fix-messaging" → "Fix Messaging"
        - "01-fix-messaging" → "Fix Messaging"
        
        Args:
            filename_stem: The filename without extension
            
        Returns:
            Formatted title string
        """
        # Remove leading numeric prefixes (like "10 ", "20 ", "01-", etc.)
        # Pattern matches: optional digits, optional separator (space or dash), then captures the rest
        match = re.match(r'^\d+[-\s]*(.*)', filename_stem)
        if match and match.group(1):
            title = match.group(1)
        else:
            title = filename_stem

        # Apply title case formatting
        # Replace dashes and underscores with spaces, then apply title case
        title = re.sub(r'[-_]+', ' ', title)
        title = title.title()

        return title

    def _create_title_with_folder_name(self, folder_path: Path, markdown_file: Path) -> str:
        """
        Create a presentation title that includes the folder name for multiple presentations.
        
        For multiple presentations in a single folder, includes the folder name:
        - "Examples/10 Deckset basics.md" → "Example - Deckset Basics"
        - "Examples/30 Big text.md" → "Example - Big Text"
        
        Args:
            folder_path: Path to the folder containing the presentation
            markdown_file: Path to the markdown file
            
        Returns:
            Formatted title with folder name prefix for multiple presentations
        """
        # Get the formatted filename title
        filename_title = self._format_filename_as_title(markdown_file.stem)

        # Get the folder name and singularize it
        folder_name = folder_path.name
        folder_title = self._singularize_folder_name(folder_name)

        # Combine folder name with filename title
        return f"{folder_title} - {filename_title}"

    def _singularize_folder_name(self, folder_name: str) -> str:
        """
        Convert plural folder names to singular for title display.
        
        Args:
            folder_name: The folder name (e.g., "Examples", "Demos")
            
        Returns:
            Singularized folder name (e.g., "Example", "Demo")
        """
        # Basic singularization rules
        if folder_name.endswith('s') and len(folder_name) > 1:
            return folder_name[:-1]
        return folder_name
