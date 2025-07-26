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

        # Should fallback to folder name when no header (default behavior)
        title = scanner.extract_presentation_title(
            os.path.join(
                test_repo, "presentation-with-hyphen", "presentation-with-hyphen.md"
            )
        )
        assert title == "presentation-with-hyphen"

    def test_extract_presentation_title_with_filename_fallback(self, test_repo, config):
        """Test extracting presentation title with filename fallback for multiple presentations scenario."""
        scanner = PresentationScanner(config)

        # Create test markdown files with numeric prefixes (like Examples folder)
        examples_dir = os.path.join(test_repo, "examples_test")
        os.makedirs(examples_dir, exist_ok=True)
        
        # Test file with numeric prefix and header
        test_file1 = os.path.join(examples_dir, "10 Deckset basics.md")
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write("# Deckset Basics\n\nContent here")
        
        # Should extract title from header (not filename)
        title = scanner.extract_presentation_title(test_file1, use_filename_fallback=True)
        assert title == "Deckset Basics"
        
        # Test file with numeric prefix but no header
        test_file2 = os.path.join(examples_dir, "20 Working with images.md")
        with open(test_file2, 'w', encoding='utf-8') as f:
            f.write("Some content without header")
        
        # Should use filename fallback and remove numeric prefix
        title = scanner.extract_presentation_title(test_file2, use_filename_fallback=True)
        assert title == "Working with images"
        
        # Test file with complex numeric prefix
        test_file3 = os.path.join(examples_dir, "100 Advanced Topics.md")
        with open(test_file3, 'w', encoding='utf-8') as f:
            f.write("Content without header")
        
        # Should handle multi-digit prefixes
        title = scanner.extract_presentation_title(test_file3, use_filename_fallback=True)
        assert title == "Advanced Topics"
        
        # Test file without numeric prefix
        test_file4 = os.path.join(examples_dir, "Special Presentation.md")
        with open(test_file4, 'w', encoding='utf-8') as f:
            f.write("Content without header")
        
        # Should use full filename when no numeric prefix
        title = scanner.extract_presentation_title(test_file4, use_filename_fallback=True)
        assert title == "Special Presentation"
        
        # Test file with frontmatter title
        test_file5 = os.path.join(examples_dir, "30 Big text.md")
        with open(test_file5, 'w', encoding='utf-8') as f:
            f.write("---\ntitle: Custom Title from Frontmatter\n---\n\nContent here")
        
        # Should prefer frontmatter title over filename
        title = scanner.extract_presentation_title(test_file5, use_filename_fallback=True)
        assert title == "Custom Title from Frontmatter"

    def test_format_filename_as_title(self, config):
        """Test the filename formatting logic."""
        scanner = PresentationScanner(config)
        
        # Test numeric prefix removal
        assert scanner._format_filename_as_title("10 Deckset basics") == "Deckset basics"
        assert scanner._format_filename_as_title("20 Working with images") == "Working with images"
        assert scanner._format_filename_as_title("100 Advanced Topics") == "Advanced Topics"
        assert scanner._format_filename_as_title("5 Quick Start") == "Quick Start"
        
        # Test files without numeric prefix
        assert scanner._format_filename_as_title("Special Presentation") == "Special Presentation"
        assert scanner._format_filename_as_title("presentation-name") == "presentation-name"
        assert scanner._format_filename_as_title("README") == "README"
        
        # Test edge cases
        assert scanner._format_filename_as_title("10") == "10"  # Just number
        assert scanner._format_filename_as_title("10 ") == "10 "  # Number with space but no content
        assert scanner._format_filename_as_title("") == ""  # Empty string

    def test_multiple_presentations_folder_title_extraction(self, test_repo, config):
        """Test title extraction for folders with multiple independent presentations."""
        scanner = PresentationScanner(config)
        
        # Create an Examples-like folder
        examples_dir = os.path.join(test_repo, "Examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        # Create multiple markdown files similar to the real Examples folder
        files_and_titles = [
            ("10 Deckset basics.md", "# Deckset Basics"),
            ("20 Working with images.md", "# Working with images"),
            ("30 Big text.md", "# [fit] Do you like your text really"),
            ("40 Education.md", "# Education Template"),
            ("50 Tables.md", "# Using Tables in Deckset"),
        ]
        
        for filename, header in files_and_titles:
            file_path = os.path.join(examples_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{header}\n\nContent here")
        
        # Test that scanner correctly identifies this as a multiple presentations folder
        folder_path = Path(examples_dir)
        assert scanner._has_multiple_independent_presentations(folder_path)
        
        # Test title extraction for each file
        expected_titles = {
            "10 Deckset basics.md": "Deckset Basics",
            "20 Working with images.md": "Working with images", 
            "30 Big text.md": "[fit] Do you like your text really",
            "40 Education.md": "Education Template",
            "50 Tables.md": "Using Tables in Deckset",
        }
        
        for filename, expected_title in expected_titles.items():
            file_path = os.path.join(examples_dir, filename)
            title = scanner.extract_presentation_title(file_path, use_filename_fallback=True)
            assert title == expected_title, f"Expected '{expected_title}' for {filename}, got '{title}'"

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
