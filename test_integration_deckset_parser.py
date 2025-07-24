#!/usr/bin/env python3
"""
Simple integration test to verify DecksetParser works with existing system.
"""

from deckset_parser import DecksetParser, DecksetConfig, SlideConfig

def test_integration():
    """Test that DecksetParser integrates well with the existing system."""
    
    # Sample Deckset content
    content = """
theme: Zurich
autoscale: true
slidenumbers: true
footer: My Presentation

# [fit] Welcome :smile:
This is the introduction slide.

^ Speaker note for intro

---

[.column]
## Column 1
Content with footnote[^1]

[.column]  
## Column 2
More content :fire:

[^1]: This is a footnote

---

[.background-image: final.jpg]
# Thank You!
Final slide content

^ Final speaker note
    """
    
    parser = DecksetParser()
    
    # Test global commands
    print("Testing global commands...")
    global_config = parser.parse_global_commands(content)
    print(f"Theme: {global_config.theme}")
    print(f"Autoscale: {global_config.autoscale}")
    print(f"Slide numbers: {global_config.slide_numbers}")
    print(f"Footer: {global_config.footer}")
    
    # Test slide extraction
    print("\nTesting slide extraction...")
    slides = parser.extract_slide_separators(content)
    print(f"Found {len(slides)} slides")
    
    # Test processing each slide
    for i, slide_content in enumerate(slides):
        print(f"\n--- Slide {i+1} ---")
        
        # Test slide commands
        slide_config = parser.parse_slide_commands(slide_content)
        if slide_config.columns:
            print("Has columns")
        if slide_config.background_image:
            print(f"Background image: {slide_config.background_image}")
        
        # Test speaker notes
        cleaned_content, notes = parser.process_speaker_notes(slide_content)
        if notes:
            print(f"Speaker notes: {notes[:50]}...")
        
        # Test footnotes
        cleaned_content, footnotes = parser.process_footnotes(cleaned_content)
        if footnotes:
            print(f"Footnotes: {footnotes}")
        
        # Test fit headers and emojis
        processed = parser.process_fit_headers(cleaned_content, global_config)
        processed = parser.process_emoji_shortcodes(processed)
        
        print(f"Processed content: {processed[:100]}...")
    
    print("\n✅ Integration test completed successfully!")

if __name__ == "__main__":
    test_integration()