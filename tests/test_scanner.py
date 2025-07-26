"""
Tests for the repository scanner functionality.

This module contains tests for the PresentationScanner class that discovers
presentation folders and markdown files in the repository.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from scanner import PresentationScanner
from models import GeneratorConfig, GeneratorError


class TestPresentationScanner:
    """Test cases for the PresentationScanner class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return GeneratorConfig(
            exclude_folders=[".git", ".kiro", "node_modules", "__pycache__"]
        )

    @pytest.fixture
    def test_repo(self):
        """Create a temporary test repository structure."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Create test folder structure
            folders = [
                # Regular presentation folders
                "presentation1",
                "presentation2",
                "presentation-with-hyphen",
                # Excluded folders
                ".git",
                ".kiro",
                # Empty folder
                "empty-folder",
                # Folder with non-markdown files only
                "no-markdown",
            ]

            for folder in folders:
                os.makedirs(os.path.join(temp_dir, folder), exist_ok=True)

            # Create markdown files
            with open(
                os.path.join(temp_dir, "presentation1", "presentation1.md"), "w"
            ) as f:
                f.write("# Presentation 1\n\nContent")

            with open(
                os.path.join(temp_dir, "presentation2", "different-name.md"), "w"
            ) as f:
                f.write("# Presentation 2\n\nContent")

            with open(
                os.path.join(temp_dir, "presentation2", "another-file.md"), "w"
            ) as f:
                f.write("# Another File\n\nContent")

            with open(
                os.path.join(
                    temp_dir, "presentation-with-hyphen", "presentation-with-hyphen.md"
                ),
                "w",
            ) as f:
                f.write("Content without title")

            # Create non-markdown file
            with open(os.path.join(temp_dir, "no-markdown", "document.txt"), "w") as f:
                f.write("Not a markdown file")

            yield temp_dir
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def test_scan_presentations(self, test_repo, config):
        """Test scanning for presentations in the repository."""
        scanner = PresentationScanner(config)
        presentations = scanner.scan_presentations(test_repo)

        # Should find 3 presentations
        assert len(presentations) == 3

        # Check that presentation names are correct
        presentation_names = [p.folder_name for p in presentations]
        assert "presentation1" in presentation_names
        assert "presentation2" in presentation_names
        assert "presentation-with-hyphen" in presentation_names

        # Excluded folders should not be included
        assert not any(p.folder_name == ".git" for p in presentations)
        assert not any(p.folder_name == ".kiro" for p in presentations)

        # Empty folder should not be included
        assert not any(p.folder_name == "empty-folder" for p in presentations)

        # Folder with no markdown should not be included
        assert not any(p.folder_name == "no-markdown" for p in presentations)

    def test_find_markdown_file(self, test_repo, config):
        """Test finding the appropriate markdown file in a folder."""
        scanner = PresentationScanner(config)

        # Should find file with same name as folder
        markdown_path = scanner.find_markdown_file(
            os.path.join(test_repo, "presentation1")
        )
        assert os.path.basename(markdown_path) == "presentation1.md"

        # Should find first alphabetical file when no matching name
        markdown_path = scanner.find_markdown_file(
            os.path.join(test_repo, "presentation2")
        )
        assert os.path.basename(markdown_path) == "another-file.md"

        # Should return None for folder with no markdown files
        markdown_path = scanner.find_markdown_file(
            os.path.join(test_repo, "no-markdown")
        )
        assert markdown_path is None

    def test_extract_presentation_title(self, test_repo, config):
        """Test extracting presentation title from markdown file."""
        scanner = PresentationScanner(config)

        # Should extract title from header
        title = scanner.extract_presentation_title(
            os.path.join(test_repo, "presentation1", "presentation1.md")
        )
        assert title == "Presentation 1"

        # Should fallback to folder name when no header
        title = scanner.extract_presentation_title(
            os.path.join(
                test_repo, "presentation-with-hyphen", "presentation-with-hyphen.md"
            )
        )
        assert title == "presentation-with-hyphen"

    def test_is_presentation_folder(self, test_repo, config):
        """Test checking if a folder is a presentation folder."""
        scanner = PresentationScanner(config)

        # Should identify folders with markdown files
        assert scanner.is_presentation_folder(os.path.join(test_repo, "presentation1"))
        assert scanner.is_presentation_folder(os.path.join(test_repo, "presentation2"))

        # Should exclude specified folders
        assert not scanner.is_presentation_folder(os.path.join(test_repo, ".git"))
        assert not scanner.is_presentation_folder(os.path.join(test_repo, ".kiro"))

        # Should exclude folders without markdown files
        assert not scanner.is_presentation_folder(
            os.path.join(test_repo, "no-markdown")
        )
        assert not scanner.is_presentation_folder(
            os.path.join(test_repo, "empty-folder")
        )

    def test_scan_nonexistent_path(self, config):
        """Test scanning a non-existent path."""
        scanner = PresentationScanner(config)
        with pytest.raises(GeneratorError):
            scanner.scan_presentations("/path/that/does/not/exist")
