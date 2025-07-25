"""
Test script to verify the enhanced project structure and core interfaces.

This script tests that all the enhanced models and interfaces are properly set up
and can be imported and instantiated correctly.
"""

import sys
import os

# Add parent directory to path for standalone execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_enhanced_models_import():
    """Test that enhanced models can be imported."""
    try:
        from models import (
            DecksetConfig,
            SlideConfig,
            ImageModifiers,
            ProcessedImage,
            MediaModifiers,
            ProcessedVideo,
            ProcessedAudio,
            ColumnContent,
            ProcessedSlide,
            EnhancedPresentation,
            SlideContext,
            DecksetParsingError,
            MediaProcessingError,
            SlideProcessingError,
        )

        print("✅ Enhanced models imported successfully")
        assert True
    except ImportError as e:
        print(f"❌ Failed to import enhanced models: {e}")
        assert False, f"Failed to import enhanced models: {e}"


def test_interfaces_import():
    """Test that interfaces can be imported."""
    try:
        from models import (
            DecksetParserInterface,
            MediaProcessorInterface,
            SlideProcessorInterface,
        )

        print("✅ Interfaces imported successfully")
        assert True
    except ImportError as e:
        print(f"❌ Failed to import interfaces: {e}")
        assert False, f"Failed to import interfaces: {e}"


def test_implementations_import():
    """Test that implementations can be imported."""
    try:
        from deckset_parser import DecksetParser
        from media_processor import MediaProcessor
        from slide_processor import SlideProcessor

        print("✅ Implementations imported successfully")
        assert True
    except ImportError as e:
        print(f"❌ Failed to import implementations: {e}")
        assert False, f"Failed to import implementations: {e}"


def test_basic_instantiation():
    """Test that classes can be instantiated."""
    try:
        from models import DecksetConfig, SlideConfig
        from deckset_parser import DecksetParser
        from media_processor import MediaProcessor
        from slide_processor import SlideProcessor

        # Test model instantiation
        config = DecksetConfig()
        slide_config = SlideConfig()

        # Test implementation instantiation
        parser = DecksetParser()
        media_processor = MediaProcessor()
        slide_processor = SlideProcessor()

        print("✅ Basic instantiation successful")
        assert True
    except Exception as e:
        print(f"❌ Failed basic instantiation: {e}")
        assert False, f"Failed basic instantiation: {e}"


def test_basic_functionality():
    """Test basic functionality of the components."""
    try:
        from deckset_parser import DecksetParser
        from models import DecksetConfig

        parser = DecksetParser()

        # Test global command parsing
        test_content = """
theme: Next
autoscale: true
slidenumbers: true
footer: My Presentation

# Slide 1
Content here
        """

        config = parser.parse_global_commands(test_content)
        assert config.theme == "Next"
        assert config.autoscale == True
        assert config.slide_numbers == True
        assert config.footer == "My Presentation"

        # Test slide separation
        slides = parser.extract_slide_separators("Slide 1\n---\nSlide 2\n---\nSlide 3")
        assert len(slides) == 3

        print("✅ Basic functionality tests passed")
        assert True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        assert False, f"Basic functionality test failed: {e}"


def run_all_tests():
    """Run all setup verification tests."""
    print("🧪 Testing Enhanced Project Structure Setup")
    print("=" * 50)

    tests = [
        test_enhanced_models_import,
        test_interfaces_import,
        test_implementations_import,
        test_basic_instantiation,
        test_basic_functionality,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Enhanced project structure is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
