"""
Tests for the template management system.

This module contains tests for the TemplateManager class and its functionality.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from templates import TemplateManager
from models import GeneratorConfig, PresentationInfo, ProcessedPresentation, Slide, TemplateRenderingError


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create a temporary template directory with test templates."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    # Create a base template
    base_template = template_dir / "base.html"
    base_template.write_text("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{% block title %}Default Title{% endblock %}</title>
    </head>
    <body>
        {% block content %}{% endblock %}
    </body>
    </html>
    """)
    
    # Create a presentation template
    presentation_template = template_dir / "presentation.html"
    presentation_template.write_text("""
    {% extends "base.html" %}
    {% block title %}{{ presentation.info.title }}{% endblock %}
    {% block content %}
    <h1>{{ presentation.info.title }}</h1>
    <div class="slides">
        {% for slide in presentation.slides %}
        <div class="slide">
            <h2>Slide {{ slide.index }}</h2>
            <div class="content">{{ slide.content }}</div>
            {% if slide.notes %}
            <div class="notes">{{ slide.notes }}</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """)
    
    # Create a homepage template
    homepage_template = template_dir / "homepage.html"
    homepage_template.write_text("""
    {% extends "base.html" %}
    {% block title %}Presentations{% endblock %}
    {% block content %}
    <h1>Presentations</h1>
    <div class="presentations">
        {% for presentation in presentations %}
        <div class="presentation">
            <h2>{{ presentation.title }}</h2>
            <p>{{ presentation.slide_count }} slides</p>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """)
    
    return template_dir


@pytest.fixture
def template_manager(temp_template_dir):
    """Create a template manager with the temporary template directory."""
    config = GeneratorConfig(template_dir=str(temp_template_dir))
    return TemplateManager(config)


@pytest.fixture
def sample_presentation():
    """Create a sample presentation for testing."""
    info = PresentationInfo(
        folder_name="test-presentation",
        folder_path="/path/to/test-presentation",
        markdown_path="/path/to/test-presentation/test-presentation.md",
        title="Test Presentation",
        preview_image="images/test-preview.png",
        slide_count=2,
        last_modified=None
    )
    
    slides = [
        Slide(index=1, content="# Slide 1 Content", notes="Notes for slide 1", image_path="slides/1.png"),
        Slide(index=2, content="# Slide 2 Content", notes="Notes for slide 2", image_path="slides/2.png")
    ]
    
    return ProcessedPresentation(info=info, slides=slides)


@pytest.fixture
def sample_presentations():
    """Create a list of sample presentation infos for testing."""
    return [
        PresentationInfo(
            folder_name="test-presentation-1",
            folder_path="/path/to/test-presentation-1",
            markdown_path="/path/to/test-presentation-1/test-presentation-1.md",
            title="Test Presentation 1",
            preview_image="images/test-preview-1.png",
            slide_count=2,
            last_modified=None
        ),
        PresentationInfo(
            folder_name="test-presentation-2",
            folder_path="/path/to/test-presentation-2",
            markdown_path="/path/to/test-presentation-2/test-presentation-2.md",
            title="Test Presentation 2",
            preview_image="images/test-preview-2.png",
            slide_count=3,
            last_modified=None
        )
    ]


def test_template_manager_initialization(temp_template_dir):
    """Test that the template manager initializes correctly."""
    config = GeneratorConfig(template_dir=str(temp_template_dir))
    manager = TemplateManager(config)
    
    assert manager.config == config
    assert manager.template_dir == Path(temp_template_dir)
    assert manager.env is not None


def test_load_template(template_manager):
    """Test loading a template by name."""
    template = template_manager.load_template("base.html")
    assert template is not None
    
    # Test loading a non-existent template
    with pytest.raises(TemplateRenderingError):
        template_manager.load_template("non-existent.html")


def test_render_template(template_manager):
    """Test rendering a template with data."""
    # The base.html template uses block title, not a direct title variable
    # So we need to create a simple template for this test
    simple_template = template_manager.template_dir / "simple.html"
    simple_template.write_text("Title: {{ title }}, Content: {{ content }}")
    
    data = {"title": "Test Title", "content": "Test Content"}
    rendered = template_manager.render_template("simple.html", data)
    
    assert "Test Title" in rendered
    assert "Test Content" in rendered
    
    # Test rendering with invalid data - this won't actually raise an error with Jinja2
    # as it silently ignores missing variables
    rendered = template_manager.render_template("simple.html", {"invalid_var": "value"})
    assert "Title: " in rendered  # The title variable will be empty


def test_render_presentation(template_manager, sample_presentation, tmp_path):
    """Test rendering a presentation."""
    # Test rendering to string
    rendered = template_manager.render_presentation(sample_presentation)
    assert "Test Presentation" in rendered
    assert "Slide 1 Content" in rendered
    assert "Notes for slide 1" in rendered
    
    # Test rendering to file
    output_path = tmp_path / "presentation.html"
    template_manager.render_presentation(sample_presentation, str(output_path))
    assert output_path.exists()
    content = output_path.read_text()
    assert "Test Presentation" in content


def test_render_homepage(template_manager, sample_presentations, tmp_path):
    """Test rendering the homepage."""
    # Test rendering to string
    rendered = template_manager.render_homepage(sample_presentations)
    assert "Presentations" in rendered
    assert "Test Presentation 1" in rendered
    assert "Test Presentation 2" in rendered
    
    # Test rendering to file
    output_path = tmp_path / "index.html"
    template_manager.render_homepage(sample_presentations, str(output_path))
    assert output_path.exists()
    content = output_path.read_text()
    assert "Test Presentation 1" in content
    assert "Test Presentation 2" in content


def test_template_exists(template_manager):
    """Test checking if a template exists."""
    assert template_manager.template_exists("base.html")
    assert template_manager.template_exists("presentation.html")
    assert template_manager.template_exists("homepage.html")
    assert not template_manager.template_exists("non-existent.html")


def test_ensure_template_dir(tmp_path):
    """Test ensuring the template directory exists."""
    new_template_dir = tmp_path / "new_templates"
    config = GeneratorConfig(template_dir=str(new_template_dir))
    
    # Directory should not exist initially
    assert not new_template_dir.exists()
    
    # Creating TemplateManager should create the directory
    manager = TemplateManager(config)
    assert new_template_dir.exists()
    
    # ensure_template_dir should work even if directory already exists
    manager.ensure_template_dir()
    assert new_template_dir.exists()


def test_get_all_templates(template_manager):
    """Test getting all available templates."""
    templates = template_manager.get_all_templates()
    assert "base.html" in templates
    assert "presentation.html" in templates
    assert "homepage.html" in templates
    assert len(templates) == 3


def test_markdown_filter(template_manager):
    """Test the markdown filter."""
    markdown_text = "# Heading\n\nParagraph with **bold** and *italic* text."
    html = template_manager._markdown_filter(markdown_text)
    
    assert "<h1>Heading</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


@patch('templates.JINJA2_AVAILABLE', False)
def test_template_manager_without_jinja2():
    """Test that the template manager handles missing Jinja2 gracefully."""
    config = GeneratorConfig(template_dir="templates")
    manager = TemplateManager(config)
    
    assert manager.env is None
    
    with pytest.raises(TemplateRenderingError, match="Jinja2 is not available"):
        manager.load_template("base.html")


def test_render_presentation_with_error(template_manager, sample_presentation):
    """Test error handling when rendering a presentation."""
    # Create a mock template that raises an exception
    mock_template = MagicMock()
    mock_template.render.side_effect = Exception("Template rendering error")
    
    with patch.object(template_manager, 'load_template', return_value=mock_template):
        with pytest.raises(TemplateRenderingError, match="Failed to render presentation template"):
            template_manager.render_presentation(sample_presentation)


def test_render_homepage_with_error(template_manager, sample_presentations):
    """Test error handling when rendering the homepage."""
    # Create a mock template that raises an exception
    mock_template = MagicMock()
    mock_template.render.side_effect = Exception("Template rendering error")
    
    with patch.object(template_manager, 'load_template', return_value=mock_template):
        with pytest.raises(TemplateRenderingError, match="Failed to render homepage template"):
            template_manager.render_homepage(sample_presentations)