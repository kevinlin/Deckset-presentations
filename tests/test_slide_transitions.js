/**
 * @jest-environment jsdom
 */

function buildDOM(transition) {
    document.body.innerHTML = `
        <div class="presentation-container">
            <div class="slides-container"${transition ? ` data-transition="${transition}"` : ''}>
                <section class="slide" id="slide-1">Slide 1</section>
                <section class="slide" id="slide-2">Slide 2</section>
                <section class="slide" id="slide-3">Slide 3</section>
            </div>
            <div class="navigation">
                <button id="prev-slide">Prev</button>
                <span id="slide-counter">1 / 3</span>
                <button id="next-slide">Next</button>
                <button id="toggle-notes">Notes</button>
            </div>
        </div>
    `;
}

function createViewer(reducedMotion) {
    window.matchMedia = jest.fn().mockImplementation(q => ({
        matches: reducedMotion && q === '(prefers-reduced-motion: reduce)',
        media: q,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
    }));
    jest.resetModules();
    const { EnhancedSlideViewer } = require('../templates/assets/js/slide-viewer.js');
    return new EnhancedSlideViewer();
}

describe('Slide Transitions', () => {
    afterEach(() => { document.body.innerHTML = ''; });

    test('no transition attr: instant switch', () => {
        buildDOM();
        const viewer = createViewer(false);
        viewer.nextSlide();
        const slides = document.querySelectorAll('.slide');
        expect(slides[0].classList.contains('active')).toBe(false);
        expect(slides[1].classList.contains('active')).toBe(true);
    });

    test('fade: slide 2 becomes active on next', () => {
        buildDOM('fade');
        const viewer = createViewer(false);
        viewer.nextSlide();
        const slides = document.querySelectorAll('.slide');
        expect(slides[1].classList.contains('active')).toBe(true);
    });

    test('push: slide 2 becomes active on next', () => {
        buildDOM('push');
        const viewer = createViewer(false);
        viewer.nextSlide();
        const slides = document.querySelectorAll('.slide');
        expect(slides[1].classList.contains('active')).toBe(true);
        expect(slides[0].classList.contains('active')).toBe(false);
    });

    test('push: previousSlide uses reverse direction', () => {
        buildDOM('push');
        const viewer = createViewer(false);
        viewer.showSlide(2);
        viewer.previousSlide();
        const slides = document.querySelectorAll('.slide');
        expect(slides[1].classList.contains('active')).toBe(true);
    });

    test('prefers-reduced-motion disables fade transition', () => {
        buildDOM('fade');
        const viewer = createViewer(true);
        viewer.nextSlide();
        const slides = document.querySelectorAll('.slide');
        // Should be instant — no fade classes
        expect(slides[0].classList.contains('slide-fade-out')).toBe(false);
        expect(slides[1].classList.contains('slide-fade-in')).toBe(false);
        expect(slides[1].classList.contains('active')).toBe(true);
    });
});
