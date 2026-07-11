"""Regression harness: build the real repo into a temp site and assert structural invariants.

This is the safety net for every v2 change. The session-scoped fixture runs the
full pipeline once; individual tests check structural properties of the output
via BeautifulSoup. Assertions are intentionally coarse (element counts, attribute
presence) so they survive cosmetic changes but catch dropped features.
"""

import tempfile
import shutil
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from main import DecksetWebsiteGenerator
from models import GeneratorConfig


# ---------------------------------------------------------------------------
# Repo root: walk up from tests/ to the project root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Session fixture: generate the entire site once
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def site_dir():
    """Generate the full site from the repo root into a temp directory."""
    tmp = tempfile.mkdtemp(prefix="regression_site_")
    config = GeneratorConfig(output_dir=tmp)
    config.exclude_folders = [f for f in config.exclude_folders if f != "Examples"]
    generator = DecksetWebsiteGenerator(config)
    result = generator.generate_website(root_path=str(REPO_ROOT), output_dir=tmp)
    assert result["success"], f"Site generation failed: {result.get('errors', [])}"
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def homepage_soup(site_dir):
    index = site_dir / "index.html"
    assert index.exists(), "Homepage index.html not generated"
    return BeautifulSoup(index.read_text(encoding="utf-8"), "html.parser")


def _slug(folder_name: str) -> str:
    """Mirror PresentationInfo.slug logic for test path building."""
    import re
    parts = folder_name.split("/")
    slugged = []
    for part in parts:
        s = part.strip().lower()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s]+", "-", s)
        slugged.append(s)
    return "/".join(slugged)


def _load_homepage(site_dir: Path) -> BeautifulSoup:
    """Load and parse the homepage index.html."""
    html_path = site_dir / "index.html"
    assert html_path.exists(), f"Missing homepage: {html_path}"
    return BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")


def _load_presentation(site_dir: Path, folder_name: str) -> BeautifulSoup:
    slug = _slug(folder_name)
    html_path = site_dir / slug / "index.html"
    assert html_path.exists(), f"Missing presentation page: {html_path}"
    return BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")


# ---------------------------------------------------------------------------
# Homepage tests
# ---------------------------------------------------------------------------
class TestHomepage:
    """Verify the homepage lists all discovered presentations."""

    def test_homepage_exists(self, site_dir):
        assert (site_dir / "index.html").exists()

    def test_homepage_has_presentation_cards(self, homepage_soup):
        cards = homepage_soup.select(".presentation-card")
        assert len(cards) >= 10, (
            f"Expected at least 10 presentation cards, got {len(cards)}"
        )

    def test_homepage_cards_have_titles(self, homepage_soup):
        titles = homepage_soup.select(".presentation-title")
        assert len(titles) >= 10
        for title_el in titles:
            assert title_el.get_text(strip=True), "Empty presentation title found"

    def test_homepage_cards_have_view_links(self, homepage_soup):
        links = homepage_soup.select(".presentation-card a[href]")
        view_links = [a for a in links if a["href"].endswith("/")]
        assert len(view_links) >= 10

    def test_homepage_has_search(self, homepage_soup):
        search = homepage_soup.select_one("#search-input")
        assert search is not None, "Search input not found on homepage"


# ---------------------------------------------------------------------------
# Per-presentation structural tests
# ---------------------------------------------------------------------------
SINGLE_DECKS = [
    "01-fix-messaging",
    "02-powerpoint-karaoke",
    "03-docker-kubernetes-101",
    "04-eks-deployment-101",
    "05-code-to-cloud-native",
    "06-mastering-auth0-with-terraform",
]

EXAMPLE_DECKS = [
    "Examples/10 Deckset basics",
    "Examples/20 Working with images",
    "Examples/30 Big text",
    "Examples/40 Education",
    "Examples/50 Tables",
]


class TestPresentationPages:
    """Every discovered deck must produce a valid presentation page."""

    @pytest.mark.parametrize("deck", SINGLE_DECKS + EXAMPLE_DECKS)
    def test_presentation_html_exists(self, site_dir, deck):
        slug = _slug(deck)
        path = site_dir / slug / "index.html"
        assert path.exists(), f"Presentation page missing for {deck} (slug={slug})"

    @pytest.mark.parametrize("deck", SINGLE_DECKS + EXAMPLE_DECKS)
    def test_slides_present(self, site_dir, deck):
        soup = _load_presentation(site_dir, deck)
        slides = soup.select("section.slide")
        assert len(slides) > 0, f"No slides found in {deck}"

    @pytest.mark.parametrize("deck", SINGLE_DECKS + EXAMPLE_DECKS)
    def test_navigation_controls(self, site_dir, deck):
        soup = _load_presentation(site_dir, deck)
        assert soup.select_one("#prev-slide"), f"No prev button in {deck}"
        assert soup.select_one("#next-slide"), f"No next button in {deck}"
        assert soup.select_one("#slide-counter"), f"No slide counter in {deck}"


# ---------------------------------------------------------------------------
# Chrome tests (footer / slide numbers when configured)
# ---------------------------------------------------------------------------
class TestSlideChrome:
    """Decks with footer/slidenumbers should render that chrome."""

    def test_deckset_basics_has_footer(self, site_dir):
        """10 Deckset basics.md has `footer: © Deckset …`"""
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        footers = soup.select(".slide-footer")
        assert len(footers) > 0, "Expected footer elements in Deckset basics"

    def test_deckset_basics_has_slide_numbers(self, site_dir):
        """10 Deckset basics.md has `slidenumbers: true`"""
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        numbers = soup.select(".slide-number")
        assert len(numbers) > 0, "Expected slide number elements in Deckset basics"


# ---------------------------------------------------------------------------
# Feature element tests for Examples/ decks
# ---------------------------------------------------------------------------
class TestExamplesFeatures:
    """Verify that Examples/ decks render their characteristic feature elements."""

    def test_basics_has_headings(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        headings = soup.find_all(["h1", "h2", "h3", "h4"])
        assert len(headings) > 0, "No headings in Deckset basics"

    def test_basics_has_code_blocks(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        code = soup.select(".code-container, pre, code")
        assert len(code) > 0, "No code blocks in Deckset basics"

    def test_basics_has_images(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        images = soup.find_all("img")
        slide_images = [
            img for img in images
            if img.find_parent("section", class_="slide")
        ]
        assert len(slide_images) > 0, "No images in Deckset basics slides"

    def test_basics_has_speaker_notes(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        notes = soup.select("aside.speaker-notes")
        assert len(notes) > 0, "No speaker notes in Deckset basics"

    def test_images_deck_has_images(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/20 Working with images")
        images = soup.find_all("img")
        slide_images = [
            img for img in images
            if img.find_parent("section", class_="slide")
        ]
        assert len(slide_images) > 0, "No images in Working with images deck"

    def test_images_deck_has_background_images(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/20 Working with images")
        bg_imgs = soup.select(".background-image")
        assert len(bg_imgs) > 0, "No background images in Working with images deck"

    def test_big_text_has_fit_headings(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/30 Big text")
        headings = soup.find_all(["h1", "h2", "h3"])
        assert len(headings) > 0, "No headings in Big text deck"

    def test_education_has_math(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/40 Education")
        math = soup.select(".math-display, .math-inline, [data-formula-type]")
        assert len(math) > 0, "No math elements in Education deck"

    def test_education_has_footnote_content(self, site_dir):
        """40 Education.md uses [^1] footnotes — v1 may render them as raw text
        or as proper footnote elements. Either way the content should be present."""
        soup = _load_presentation(site_dir, "Examples/40 Education")
        full_text = soup.get_text()
        has_footnote_elements = len(soup.select(".footnotes, .footnote")) > 0
        has_footnote_markers = "[^" in full_text or "footnote" in full_text.lower()
        assert has_footnote_elements or has_footnote_markers, (
            "No footnote content found in Education deck"
        )

    def test_tables_deck_has_tables(self, site_dir):
        """50 Tables.md contains pipe tables — at minimum we should see
        table-like output (actual <table> is a v2 goal; v1 may render differently)."""
        soup = _load_presentation(site_dir, "Examples/50 Tables")
        slides = soup.select("section.slide")
        assert len(slides) > 0, "No slides in Tables deck"
        full_text = soup.get_text()
        assert "|" in full_text or soup.find("table") is not None, (
            "No table content found in Tables deck"
        )


# ---------------------------------------------------------------------------
# Slide count sanity
# ---------------------------------------------------------------------------
class TestSlideCounts:
    """Spot-check slide counts for known decks."""

    def test_basics_slide_count(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/10 Deckset basics")
        slides = soup.select("section.slide")
        assert len(slides) >= 5, (
            f"Deckset basics should have many slides, got {len(slides)}"
        )

    def test_big_text_slide_count(self, site_dir):
        soup = _load_presentation(site_dir, "Examples/30 Big text")
        slides = soup.select("section.slide")
        assert len(slides) >= 2, (
            f"Big text should have at least 2 slides, got {len(slides)}"
        )


# ---------------------------------------------------------------------------
# Theme system (Task 4+)
# ---------------------------------------------------------------------------
class TestThemeSystem:
    """Verify theme compilation, manifest, and CSS links."""

    def test_themes_manifest_exists(self, site_dir):
        manifest = site_dir / "assets" / "css" / "themes" / "themes.json"
        assert manifest.exists(), "themes.json manifest missing"

    def test_themes_manifest_has_16_entries(self, site_dir):
        import json
        manifest = site_dir / "assets" / "css" / "themes" / "themes.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert len(data) >= 16, f"Expected >=16 manifest entries, got {len(data)}"

    def test_theme_css_files_compiled(self, site_dir):
        css_dir = site_dir / "assets" / "css" / "themes"
        css_files = list(css_dir.glob("*.css"))
        assert len(css_files) >= 16, f"Expected >=16 theme CSS files, got {len(css_files)}"

    def test_homepage_links_theme_css(self, site_dir):
        soup = _load_homepage(site_dir)
        link = soup.find("link", id="theme-css")
        assert link is not None, "Homepage missing #theme-css link"
        assert "themes/light.css" in link["href"]

    def test_presentation_page_links_theme_css(self, site_dir):
        soup = _load_presentation(site_dir, "01-fix-messaging")
        link = soup.find("link", id="theme-css")
        assert link is not None, "Presentation page missing #theme-css link"

    def test_homepage_header_has_site_header_class(self, site_dir):
        soup = _load_homepage(site_dir)
        header = soup.find("header")
        assert header is not None
        assert "site-header" in header.get("class", [])
        assert "bg-white" not in header.get("class", [])

    def test_presentation_header_has_site_header_class(self, site_dir):
        soup = _load_presentation(site_dir, "01-fix-messaging")
        header = soup.find("header")
        assert header is not None
        assert "site-header" in header.get("class", [])
