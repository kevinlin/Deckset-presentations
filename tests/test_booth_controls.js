/**
 * @jest-environment jsdom
 *
 * Tests for the booth controls: blackout shutter (B) and the
 * keyboard-shortcuts card (?), added by slide-viewer.js.
 */

function buildDOM() {
    document.body.innerHTML = `
        <div class="presentation-container">
            <div class="slides-container">
                <section class="slide" id="slide-1">Slide 1</section>
                <section class="slide" id="slide-2">Slide 2</section>
                <section class="slide" id="slide-3">Slide 3</section>
            </div>
            <div class="navigation">
                <button id="prev-slide">Prev</button>
                <span id="slide-counter">1 / 3</span>
                <button id="next-slide">Next</button>
                <button id="toggle-notes">Notes</button>
                <button id="show-help" aria-haspopup="dialog" aria-expanded="false">?</button>
            </div>
        </div>
    `;
}

function createViewer() {
    window.matchMedia = jest.fn().mockImplementation(q => ({
        matches: false,
        media: q,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
    }));
    jest.resetModules();
    const { EnhancedSlideViewer } = require('../templates/assets/js/slide-viewer.js');
    return new EnhancedSlideViewer();
}

function pressKey(key) {
    document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
}

describe('Blackout shutter (B)', () => {
    afterEach(() => { document.body.innerHTML = ''; });

    test('B toggles blackout on', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('b');
        expect(viewer.blackoutActive).toBe(true);
        expect(document.querySelector('.booth-blackout').classList.contains('is-active')).toBe(true);
    });

    test('any key exits blackout without navigating', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('b');
        pressKey('ArrowRight');
        expect(viewer.blackoutActive).toBe(false);
        expect(viewer.currentSlide).toBe(0);
    });

    test('clicking the shutter exits blackout', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('B');
        const shutter = document.querySelector('.booth-blackout');
        shutter.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(viewer.blackoutActive).toBe(false);
        expect(shutter.classList.contains('is-active')).toBe(false);
    });

    test('blackout is announced to screen readers', () => {
        buildDOM();
        createViewer();
        pressKey('b');
        const announcer = document.getElementById('slide-announcer');
        expect(announcer.textContent).toContain('Press any key to resume');
    });
});

describe('Booth controls card (?)', () => {
    afterEach(() => { document.body.innerHTML = ''; });

    test('? opens the card, Escape closes it', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('?');
        const card = document.querySelector('.booth-help');
        expect(viewer.helpVisible).toBe(true);
        expect(card.classList.contains('is-open')).toBe(true);

        pressKey('Escape');
        expect(viewer.helpVisible).toBe(false);
        expect(card.classList.contains('is-open')).toBe(false);
    });

    test('navigation keys are inert while the card is open', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('?');
        pressKey('ArrowRight');
        expect(viewer.currentSlide).toBe(0);
        expect(viewer.helpVisible).toBe(true);
    });

    test('card lists the blackout shortcut', () => {
        buildDOM();
        createViewer();
        pressKey('?');
        const card = document.querySelector('.booth-help');
        expect(card.textContent).toContain('Blackout');
    });

    test('nav ? button toggles the card and aria-expanded', () => {
        buildDOM();
        createViewer();
        const button = document.getElementById('show-help');
        button.click();
        expect(document.querySelector('.booth-help').classList.contains('is-open')).toBe(true);
        expect(button.getAttribute('aria-expanded')).toBe('true');

        button.click();
        expect(document.querySelector('.booth-help').classList.contains('is-open')).toBe(false);
        expect(button.getAttribute('aria-expanded')).toBe('false');
    });

    test('backdrop click closes the card', () => {
        buildDOM();
        const viewer = createViewer();
        pressKey('?');
        document.querySelector('.booth-help-backdrop')
            .dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(viewer.helpVisible).toBe(false);
    });
});
