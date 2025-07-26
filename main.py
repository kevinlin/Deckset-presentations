"""
Main orchestrator for the Deckset Website Generator.

This module provides the DecksetWebsiteGenerator class that coordinates
the entire website generation process, from scanning presentations to
generating the final HTML output.
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any

from models import (
    GeneratorConfig,
    ProcessedPresentation,
    PresentationInfo,
    GeneratorError,
    PresentationProcessingError,
    TemplateRenderingError,
)
from scanner import PresentationScanner
from enhanced_processor import EnhancedPresentationProcessor
from generator import WebPageGenerator


class DecksetWebsiteGenerator:
    """
    Main orchestrator for generating a complete website from Deckset presentations.

    This class coordinates all components to scan for presentations, process them,
    and generate a complete website with individual presentation pages and a homepage.
    """

    def __init__(self, config: Optional[GeneratorConfig] = None):
        """
        Initialize the website generator with configuration.

        Args:
            config: Optional configuration object. If None, uses default configuration.
        """
        self.config = config or GeneratorConfig()
        self.logger = self._setup_logging()

        # Initialize components
        self.scanner = PresentationScanner(self.config)
        self.processor = EnhancedPresentationProcessor()
        self.logger.info("Using enhanced Deckset processor")
        self.generator = WebPageGenerator(self.config)

        # Statistics tracking
        self.stats = {
            "presentations_found": 0,
            "presentations_processed": 0,
            "presentations_failed": 0,
            "pages_generated": 0,
            "errors": [],
        }

    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging configuration for debugging and monitoring.

        Returns:
            Configured logger instance
        """
        # Create logger
        logger = logging.getLogger("deckset_generator")
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

        # Also set up file logging if output directory exists
        try:
            output_dir = Path(self.config.output_dir)
            if output_dir.exists() or output_dir.parent.exists():
                log_file = output_dir.parent / "generator.log"
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        except Exception:
            # If file logging fails, continue without it
            pass

        return logger

    def generate_website(
        self, root_path: str = ".", output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate the complete website from all presentations in the repository.

        This is the main entry point that orchestrates the entire generation process:
        1. Scan for presentations
        2. Process each presentation
        3. Generate individual presentation pages
        4. Generate homepage
        5. Handle errors gracefully

        Args:
            root_path: Path to scan for presentations (default: current directory)
            output_dir: Optional output directory override

        Returns:
            Dictionary with generation statistics and results
        """
        if output_dir:
            self.config.output_dir = output_dir

        self.logger.info("Starting Deckset website generation")
        self.logger.info(f"Scanning root path: {root_path}")
        self.logger.info(f"Output directory: {self.config.output_dir}")

        try:
            # Step 1: Scan for presentations
            presentations_info = self._scan_presentations(root_path)

            # Step 2: Process presentations
            processed_presentations = self._process_presentations(presentations_info)

            # Step 3: Generate website
            generation_stats = self._generate_website_pages(processed_presentations)

            # Step 4: Compile final statistics
            final_stats = self._compile_final_stats(generation_stats)

            self.logger.info("Website generation completed successfully")
            self._log_final_stats(final_stats)

            return final_stats

        except Exception as e:
            error_msg = f"Website generation failed: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append({"stage": "overall", "error": str(e)})

            # Return partial results even if generation failed
            return {"success": False, "error": error_msg, "stats": self.stats}

    def generate_single_presentation(
        self, folder_path: str, output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a website page for a single presentation.

        Args:
            folder_path: Path to the presentation folder
            output_dir: Optional output directory override

        Returns:
            Dictionary with generation results
        """
        if output_dir:
            self.config.output_dir = output_dir

        self.logger.info(f"Generating single presentation from: {folder_path}")

        try:
            # Check if folder is a valid presentation
            if not self.scanner.is_presentation_folder(folder_path):
                raise GeneratorError(
                    f"Folder is not a valid presentation: {folder_path}"
                )

            # Create presentation info
            folder_path_obj = Path(folder_path)
            presentation_info = self.scanner._create_presentation_info(folder_path_obj)

            if not presentation_info:
                raise GeneratorError(
                    f"Could not create presentation info for: {folder_path}"
                )

            # Process the presentation
            processed_presentation = self.processor.process_presentation(
                presentation_info
            )

            # Generate the page
            generation_stats = self.generator.generate_all_pages(
                [processed_presentation]
            )

            self.logger.info(
                f"Single presentation generated successfully: {presentation_info.title}"
            )

            return {
                "success": True,
                "presentation": presentation_info.title,
                "stats": generation_stats,
            }

        except Exception as e:
            error_msg = f"Failed to generate single presentation: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg, "folder_path": folder_path}

    def _scan_presentations(self, root_path: str) -> List[PresentationInfo]:
        """
        Scan for presentations with error handling.

        Args:
            root_path: Path to scan

        Returns:
            List of discovered presentations
        """
        try:
            presentations = self.scanner.scan_presentations(root_path)
            self.stats["presentations_found"] = len(presentations)

            if not presentations:
                self.logger.warning("No presentations found in the repository")
            else:
                self.logger.info(f"Found {len(presentations)} presentations")
                for p in presentations:
                    self.logger.debug(f"  - {p.title} ({p.folder_name})")

            return presentations

        except GeneratorError as e:
            self.logger.error(f"Failed to scan presentations: {e}")
            self.stats["errors"].append({"stage": "scanning", "error": str(e)})
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during scanning: {e}")
            self.stats["errors"].append(
                {"stage": "scanning", "error": f"Unexpected error: {str(e)}"}
            )
            return []

    def _process_presentations(
        self, presentations_info: List[PresentationInfo]
    ) -> List[ProcessedPresentation]:
        """
        Process presentations with graceful error handling.

        Args:
            presentations_info: List of presentation info objects

        Returns:
            List of successfully processed presentations
        """
        processed_presentations = []

        for presentation_info in presentations_info:
            try:
                self.logger.info(f"Processing presentation: {presentation_info.title}")
                processed = self.processor.process_presentation(presentation_info)
                processed_presentations.append(processed)
                self.stats["presentations_processed"] += 1

                self.logger.debug(f"  - {len(processed.slides)} slides processed")
                if processed.metadata:
                    self.logger.debug(
                        f"  - Metadata: {list(processed.metadata.keys())}"
                    )

            except PresentationProcessingError as e:
                self.logger.error(
                    f"Failed to process presentation '{presentation_info.title}': {e}"
                )
                self.stats["presentations_failed"] += 1
                self.stats["errors"].append(
                    {
                        "stage": "processing",
                        "presentation": presentation_info.title,
                        "error": str(e),
                    }
                )
                # Continue with other presentations (graceful degradation)
                continue

            except Exception as e:
                self.logger.error(
                    f"Unexpected error processing '{presentation_info.title}': {e}"
                )
                self.stats["presentations_failed"] += 1
                self.stats["errors"].append(
                    {
                        "stage": "processing",
                        "presentation": presentation_info.title,
                        "error": f"Unexpected error: {str(e)}",
                    }
                )
                # Continue with other presentations (graceful degradation)
                continue

        self.logger.info(
            f"Successfully processed {len(processed_presentations)} presentations"
        )
        return processed_presentations

    def _generate_website_pages(
        self, processed_presentations: List[ProcessedPresentation]
    ) -> Dict[str, Any]:
        """
        Generate website pages with error handling.

        Args:
            processed_presentations: List of processed presentations

        Returns:
            Generation statistics
        """
        try:
            self.logger.info("Generating website pages...")
            generation_stats = self.generator.generate_all_pages(processed_presentations)

            self.stats["pages_generated"] = generation_stats.get("successful", 0)

            # Add any generation errors to our stats
            if generation_stats.get("errors"):
                for error in generation_stats["errors"]:
                    self.stats["errors"].append(
                        {
                            "stage": "generation",
                            "presentation": error.get("presentation", "unknown"),
                            "error": error.get("error", "unknown error"),
                        }
                    )

            self.logger.info(
                f"Generated {generation_stats.get('successful', 0)} pages successfully"
            )
            if generation_stats.get("failed", 0) > 0:
                self.logger.warning(
                    f"{generation_stats.get('failed', 0)} pages failed to generate"
                )

            return generation_stats

        except TemplateRenderingError as e:
            self.logger.error(f"Template rendering failed: {e}")
            self.stats["errors"].append({"stage": "generation", "error": str(e)})
            return {
                "successful": 0,
                "failed": len(processed_presentations),
                "errors": [str(e)],
            }

        except Exception as e:
            self.logger.error(f"Unexpected error during page generation: {e}")
            self.stats["errors"].append(
                {"stage": "generation", "error": f"Unexpected error: {str(e)}"}
            )
            return {
                "successful": 0,
                "failed": len(processed_presentations),
                "errors": [str(e)],
            }

    def _compile_final_stats(self, generation_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile final statistics for the generation process.

        Args:
            generation_stats: Statistics from page generation

        Returns:
            Complete statistics dictionary
        """
        return {
            "success": True,
            "presentations_found": self.stats["presentations_found"],
            "presentations_processed": self.stats["presentations_processed"],
            "presentations_failed": self.stats["presentations_failed"],
            "pages_generated": self.stats["pages_generated"],
            "total_errors": len(self.stats["errors"]),
            "errors": self.stats["errors"],
            "generation_details": generation_stats,
        }

    def _log_final_stats(self, stats: Dict[str, Any]) -> None:
        """
        Log final statistics in a readable format.

        Args:
            stats: Final statistics dictionary
        """
        self.logger.info("=== Generation Summary ===")
        self.logger.info(f"Presentations found: {stats['presentations_found']}")
        self.logger.info(f"Presentations processed: {stats['presentations_processed']}")
        self.logger.info(f"Presentations failed: {stats['presentations_failed']}")
        self.logger.info(f"Pages generated: {stats['pages_generated']}")
        self.logger.info(f"Total errors: {stats['total_errors']}")

        if stats["errors"]:
            self.logger.info("=== Errors ===")
            for error in stats["errors"]:
                stage = error.get("stage", "unknown")
                presentation = error.get("presentation", "")
                error_msg = error.get("error", "unknown error")
                if presentation:
                    self.logger.info(f"[{stage}] {presentation}: {error_msg}")
                else:
                    self.logger.info(f"[{stage}] {error_msg}")

    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration and return any issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check template directory
        template_dir = Path(self.config.template_dir)
        if not template_dir.exists():
            issues.append(f"Template directory does not exist: {template_dir}")
        # Note: No longer checking for specific template files as the system
        # uses hardcoded templates in enhanced_templates.py

        # Check output directory parent exists
        output_dir = Path(self.config.output_dir)
        if not output_dir.parent.exists():
            issues.append(
                f"Output directory parent does not exist: {output_dir.parent}"
            )



        return issues


def main():
    """
    Command-line interface for the Deckset Website Generator.
    """
    parser = argparse.ArgumentParser(
        description="Generate a website from Deckset presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Generate website from current directory
  %(prog)s --root /path/to/repo     # Generate from specific directory
  %(prog)s --output docs            # Specify output directory
  %(prog)s --single presentation1   # Generate single presentation
        """,
    )

    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to scan for presentations (default: current directory)",
    )

    parser.add_argument(
        "--output", help="Output directory for generated website (default: docs)"
    )

    parser.add_argument(
        "--single", help="Generate only a single presentation from the specified folder"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration and exit"
    )

    args = parser.parse_args()

    # Create configuration
    config = GeneratorConfig()
    if args.output:
        config.output_dir = args.output

    # Create generator
    generator = DecksetWebsiteGenerator(config)

    # Set logging level
    if args.verbose:
        logging.getLogger("deckset_generator").setLevel(logging.DEBUG)

    # Validate configuration if requested
    if args.validate:
        issues = generator.validate_configuration()
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("Configuration is valid")
            sys.exit(0)

    # Generate website
    try:
        if args.single:
            # Generate single presentation
            result = generator.generate_single_presentation(args.single, args.output)
        else:
            # Generate complete website
            result = generator.generate_website(args.root, args.output)

        # Exit with appropriate code
        if result.get("success", False):
            sys.exit(0)
        else:
            print(f"Generation failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nGeneration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
