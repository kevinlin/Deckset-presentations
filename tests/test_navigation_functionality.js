/**
 * Functional tests for presentation navigation
 * Tests the actual slide counter and notes toggle functionality
 */

const { JSDOM } = require('jsdom');

describe('Enhanced Slide Viewer - Navigation Functionality', () => {
    let dom;
    let document;
    let window;
    let EnhancedSlideViewer;
    
    beforeEach(() => {
        // Create a mock DOM environment with real presentation structure
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Presentation</title>
                <style>
                    .slide { display: none; }
                    .slide.active { display: block; }
                    .presentation-container.js-enabled .slide { display: none; }
                    .speaker-notes { display: none; }
                </style>
            </head>
            <body>
                <div class="presentation-container" data-presentation-title="Test Presentation">
                    <div class="slides-container">
                        <section class="slide" id="slide-1">
                            <div class="slide-content">
                                <h1>Slide 1</h1>
                                <p>First slide content</p>
                            </div>
                            <aside class="speaker-notes">
                                <p>Notes for slide 1</p>
                            </aside>
                        </section>
                        <section class="slide" id="slide-2">
                            <div class="slide-content">
                                <h1>Slide 2</h1>
                                <p>Second slide content</p>
                            </div>
                            <aside class="speaker-notes">
                                <p>Notes for slide 2</p>
                            </aside>
                        </section>
                        <section class="slide" id="slide-3">
                            <div class="slide-content">
                                <h1>Slide 3</h1>
                                <p>Third slide content</p>
                            </div>
                            <aside class="speaker-notes">
                                <p>Notes for slide 3</p>
                            </aside>
                        </section>
                    </div>
                    
                    <div class="navigation">
                        <button id="prev-slide" class="nav-button">Previous</button>
                        <span id="slide-counter">1 / 3</span>
                        <button id="next-slide" class="nav-button">Next</button>
                        <button id="toggle-notes" class="nav-button">Notes</button>
                    </div>
                </div>
            </body>
            </html>
        `, { 
            url: 'http://localhost',
            pretendToBeVisual: true,
            resources: 'usable'
        });
        
        document = dom.window.document;
        window = dom.window;
        
        // Set up global environment
        global.window = window;
        global.document = document;
        global.console = { log: jest.fn(), warn: jest.fn(), error: jest.fn() };
        
        // Mock MutationObserver
        global.MutationObserver = class MutationObserver {
            constructor(callback) {
                this.callback = callback;
            }
            observe() {}
            disconnect() {}
        };
        
        // Load the EnhancedSlideViewer class
        delete require.cache[require.resolve('../docs/assets/js/enhanced-slide-viewer.js')];
        const { EnhancedSlideViewer: ESV } = require('../docs/assets/js/enhanced-slide-viewer.js');
        EnhancedSlideViewer = ESV;
    });
    
    afterEach(() => {
        dom.window.close();
        delete global.document;
        delete global.window;
        delete global.MutationObserver;
    });
    
    describe('Slide Counter Functionality', () => {
        test('should initialize with slide 1 of total', () => {
            // Verify slides exist in DOM first
            const slides = document.querySelectorAll('.slide');
            expect(slides.length).toBe(3);
            
            const viewer = new EnhancedSlideViewer();
            const counter = document.getElementById('slide-counter');
            
            expect(counter.textContent).toBe('1 / 3');
            expect(viewer.currentSlide).toBe(0);
            expect(viewer.totalSlides).toBe(3);
        });
        
        test('should update counter when navigating to next slide', () => {
            const viewer = new EnhancedSlideViewer();
            const counter = document.getElementById('slide-counter');
            const nextButton = document.getElementById('next-slide');
            
            // Navigate to next slide
            nextButton.click();
            
            expect(counter.textContent).toBe('2 / 3');
            expect(viewer.currentSlide).toBe(1);
        });
        
        test('should update counter when navigating to previous slide', () => {
            const viewer = new EnhancedSlideViewer();
            const counter = document.getElementById('slide-counter');
            const prevButton = document.getElementById('prev-slide');
            const nextButton = document.getElementById('next-slide');
            
            // Go to slide 2 first
            nextButton.click();
            expect(counter.textContent).toBe('2 / 3');
            
            // Then go back to slide 1
            prevButton.click();
            expect(counter.textContent).toBe('1 / 3');
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should update counter when using goToSlide method', () => {
            const viewer = new EnhancedSlideViewer();
            const counter = document.getElementById('slide-counter');
            
            viewer.goToSlide(2);
            
            expect(counter.textContent).toBe('3 / 3');
            expect(viewer.currentSlide).toBe(2);
        });
        
        test('should update counter with keyboard navigation', () => {
            const viewer = new EnhancedSlideViewer();
            const counter = document.getElementById('slide-counter');
            
            // Simulate right arrow key press
            const rightArrowEvent = new window.KeyboardEvent('keydown', { key: 'ArrowRight' });
            document.dispatchEvent(rightArrowEvent);
            
            expect(counter.textContent).toBe('2 / 3');
            expect(viewer.currentSlide).toBe(1);
        });
    });
    
    describe('Notes Toggle Functionality', () => {
        test('should initialize with notes hidden', () => {
            const viewer = new EnhancedSlideViewer();
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
            });
            expect(viewer.notesVisible).toBe(false);
        });
        
        test('should show notes when toggle button is clicked', () => {
            const viewer = new EnhancedSlideViewer();
            const toggleButton = document.getElementById('toggle-notes');
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            
            toggleButton.click();
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('block');
            });
            expect(viewer.notesVisible).toBe(true);
            expect(toggleButton.textContent).toBe('Hide Notes');
        });
        
        test('should hide notes when toggle button is clicked again', () => {
            const viewer = new EnhancedSlideViewer();
            const toggleButton = document.getElementById('toggle-notes');
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            
            // Show notes first
            toggleButton.click();
            expect(viewer.notesVisible).toBe(true);
            
            // Hide notes
            toggleButton.click();
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
            });
            expect(viewer.notesVisible).toBe(false);
            expect(toggleButton.textContent).toBe('Notes');
        });
        
        test('should toggle notes with N key', () => {
            const viewer = new EnhancedSlideViewer();
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            
            // Press 'n' key to toggle notes
            const nKeyEvent = new window.KeyboardEvent('keydown', { key: 'n' });
            document.dispatchEvent(nKeyEvent);
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('block');
            });
            expect(viewer.notesVisible).toBe(true);
            
            // Press 'n' key again to hide notes
            document.dispatchEvent(nKeyEvent);
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
            });
            expect(viewer.notesVisible).toBe(false);
        });
        
        test('should set aria-pressed attribute on toggle button', () => {
            const viewer = new EnhancedSlideViewer();
            const toggleButton = document.getElementById('toggle-notes');
            
            expect(toggleButton.getAttribute('aria-pressed')).toBe('false');
            
            toggleButton.click();
            expect(toggleButton.getAttribute('aria-pressed')).toBe('true');
            
            toggleButton.click();
            expect(toggleButton.getAttribute('aria-pressed')).toBe('false');
        });
    });
    
    describe('Slide Display Management', () => {
        test('should mark presentation container as js-enabled', () => {
            const viewer = new EnhancedSlideViewer();
            const container = document.querySelector('.presentation-container');
            
            expect(container.classList.contains('js-enabled')).toBe(true);
        });
        
        test('should show only the active slide', () => {
            const viewer = new EnhancedSlideViewer();
            const slides = document.querySelectorAll('.slide');
            
            // Check initial state - only first slide should be active
            expect(slides[0].classList.contains('active')).toBe(true);
            expect(slides[0].style.display).toBe('block');
            expect(slides[1].classList.contains('active')).toBe(false);
            expect(slides[1].style.display).toBe('none');
            expect(slides[2].classList.contains('active')).toBe(false);
            expect(slides[2].style.display).toBe('none');
        });
        
        test('should update active slide when navigating', () => {
            const viewer = new EnhancedSlideViewer();
            const slides = document.querySelectorAll('.slide');
            const nextButton = document.getElementById('next-slide');
            
            nextButton.click();
            
            // Check that slide 2 is now active
            expect(slides[0].classList.contains('active')).toBe(false);
            expect(slides[0].style.display).toBe('none');
            expect(slides[1].classList.contains('active')).toBe(true);
            expect(slides[1].style.display).toBe('block');
            expect(slides[2].classList.contains('active')).toBe(false);
            expect(slides[2].style.display).toBe('none');
        });
    });
    
    describe('Navigation Button States', () => {
        test('should disable previous button on first slide', () => {
            const viewer = new EnhancedSlideViewer();
            const prevButton = document.getElementById('prev-slide');
            
            expect(prevButton.disabled).toBe(true);
        });
        
        test('should enable both buttons on middle slides', () => {
            const viewer = new EnhancedSlideViewer();
            const prevButton = document.getElementById('prev-slide');
            const nextButton = document.getElementById('next-slide');
            
            viewer.goToSlide(1); // Go to middle slide
            
            expect(prevButton.disabled).toBe(false);
            expect(nextButton.disabled).toBe(false);
        });
        
        test('should disable next button on last slide', () => {
            const viewer = new EnhancedSlideViewer();
            const nextButton = document.getElementById('next-slide');
            
            viewer.goToSlide(2); // Go to last slide
            
            expect(nextButton.disabled).toBe(true);
        });
    });
}); 