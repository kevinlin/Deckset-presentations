/**
 * Tests for theme-switcher.js — theme dropdown with localStorage persistence.
 */

const fs = require('fs');
const path = require('path');

const SWITCHER_PATH = path.resolve(__dirname, '../templates/assets/js/theme-switcher.js');

function setupDOM(manifest, defaultHref) {
    document.body.innerHTML = `
        <link id="theme-css" rel="stylesheet"
              href="${defaultHref}"
              data-default-href="${defaultHref}">
        <select id="theme-select" aria-label="Theme"></select>
        <script type="application/json" id="theme-manifest">${JSON.stringify(manifest)}</script>
    `;
    window.localStorage.clear();
}

function loadSwitcher() {
    const code = fs.readFileSync(SWITCHER_PATH, 'utf-8');
    eval(code);
    document.dispatchEvent(new Event('DOMContentLoaded'));
}

const MANIFEST = [
    { slug: 'light', name: 'Light', swatches: ['#fff', '#3b82f6'] },
    { slug: 'dark', name: 'Dark', swatches: ['#1a1a2e', '#4a90d9'] },
    { slug: 'minimal', name: 'Minimal', swatches: ['#fff', '#3b82f6'] },
    { slug: 'linear-app', name: 'Linear App', swatches: ['#010102', '#5e6ad2'] },
    { slug: 'notion', name: 'Notion', swatches: ['#fff', '#5645d4'] },
];

const DEFAULT_HREF = 'assets/css/themes/light.css';

describe('ThemeSwitcher', () => {
    beforeEach(() => {
        setupDOM(MANIFEST, DEFAULT_HREF);
    });

    test('populates options from inline manifest', () => {
        loadSwitcher();
        const select = document.getElementById('theme-select');
        const options = Array.from(select.options);
        expect(options.length).toBe(MANIFEST.length + 1);
        expect(options[0].value).toBe('');
        expect(options[0].text).toBe('Page default');
        expect(options[1].text).toBe('Light');
        expect(options[2].text).toBe('Dark');
    });

    test('selecting notion swaps href and persists', () => {
        loadSwitcher();
        const select = document.getElementById('theme-select');
        const link = document.getElementById('theme-css');

        select.value = 'notion';
        select.dispatchEvent(new Event('change'));

        expect(link.href).toContain('themes/notion.css');
        expect(window.localStorage.getItem('deckset-site-theme')).toBe('notion');
    });

    test('stored value applied on load', () => {
        window.localStorage.setItem('deckset-site-theme', 'dark');
        loadSwitcher();

        const link = document.getElementById('theme-css');
        const select = document.getElementById('theme-select');

        expect(link.href).toContain('themes/dark.css');
        expect(select.value).toBe('dark');
    });

    test('Page default clears storage and restores data-default-href', () => {
        window.localStorage.setItem('deckset-site-theme', 'notion');
        loadSwitcher();

        const select = document.getElementById('theme-select');
        const link = document.getElementById('theme-css');

        select.value = '';
        select.dispatchEvent(new Event('change'));

        expect(window.localStorage.getItem('deckset-site-theme')).toBeNull();
        expect(link.href).toContain(DEFAULT_HREF);
    });

    test('missing manifest script is a no-op', () => {
        document.getElementById('theme-manifest').remove();
        loadSwitcher();
        const select = document.getElementById('theme-select');
        expect(select.options.length).toBe(0);
    });
});
