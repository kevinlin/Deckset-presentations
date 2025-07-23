"""
Repository scanner for discovering Deckset presentations.

This module provides functionality to scan a repository for presentation folders
and identify markdown files that represent Deckset presentations.
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import PresentationInfo, GeneratorConfig, GeneratorError


class PresentationScanner:
    """Scans repository for presentation folders and markdown files."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
    
    def scan_presentations(self, root_path: str) -> List[PresentationInfo]:
        """
        Scan all folders in the repository root directory for presentations.
        
        Args:
            root_path: Path to the repository root directory
            
        Returns:
            List of discovered presentations
            
        Raises:
            GeneratorError: If scanning fails
        """
        presentations = []
        root_path = Path(root_path)
        
        if not root_path.exists():
            raise GeneratorError(f"Root path does not exist: {root_path}")
        
        for item in root_path.iterdir():
            if item.is_dir() and self.is_presentation_folder(str(item)):
                try:
                    presentation_info = self._create_presentation_info(item)
                    if presentation_info:
                        presentations.append(presentation_info)
                except Exception as e:
                    # Log error but continue processing other folders
                    print(f"Warning: Failed to process folder {item.name}: {e}")
                    continue
        
        return presentations
    
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
        
        # Look for file with same name as folder
        preferred_file = folder_path / f"{folder_name}.md"
        if preferred_file.exists():
            return str(preferred_file)
        
        # Find all markdown files and return first alphabetically
        markdown_files = sorted(folder_path.glob("*.md"))
        if markdown_files:
            return str(markdown_files[0])
        
        return None
    
    def extract_presentation_title(self, markdown_path: str) -> str:
        """
        Extract presentation title from markdown file or use folder name as fallback.
        
        Args:
            markdown_path: Path to the markdown file
            
        Returns:
            Presentation title
        """
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to extract title from first line if it's a header
            lines = content.strip().split('\n')
            if lines and lines[0].startswith('#'):
                return lines[0].lstrip('#').strip()
            
            # Fallback to folder name
            return Path(markdown_path).parent.name
            
        except Exception:
            # Fallback to folder name if reading fails
            return Path(markdown_path).parent.name
    
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
            return False
        
        # Skip hidden folders
        if folder_name.startswith('.'):
            return False
        
        # Check if folder contains markdown files
        markdown_files = list(folder_path.glob("*.md"))
        return len(markdown_files) > 0
    
    def _create_presentation_info(self, folder_path: Path) -> Optional[PresentationInfo]:
        """Create PresentationInfo object for a discovered folder."""
        markdown_path = self.find_markdown_file(str(folder_path))
        if not markdown_path:
            return None
        
        title = self.extract_presentation_title(markdown_path)
        
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
            last_modified=last_modified
        )