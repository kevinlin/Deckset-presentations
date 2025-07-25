/**
 * Unit tests for EnhancedSlideViewer JavaScript functionality
 * Tests fit text scaling, MathJax integration, video autoplay, and navigation
 */

// Mock DOM environment for testing
const { JSDOM } = require('jsdom');

describe('EnhancedSlideViewer', () => {
    let dom;
    let document;
    let window;
    let EnhancedSlideViewer;
    
    beforeEach(() => {
        // Create a mock DOM environment
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test</title>
                <style>
                    .slide { width: 800px; height: 600px; display: block; }
                    .fit-text { font-size: 48px; }
                    .hidden { display: none !important; }
                    .sr-only { position: absolute; left: -10000px; }
                </style>
            </head>
            <body>
                <div id="slides-container">
                    <div class="slide" id="slide-1">
                        <h1 class="fit-text">Test Slide 1</h1>
                        <video data-autoplay="true" src="test.mp4"></video>
                        <div class="speaker-notes">Speaker notes for slide 1</div>
                    </div>
                    <div class="slide" id="slide-2">
                        <h1>Test Slide 2</h1>
                        <div class="math-display">$$E = mc^2$$</div>
                    </div>
                    <div class="slide" id="slide-3">
                        <h1>Test Slide 3</h1>
                    </div>
                </div>
                <div class="sticky top-16">
                    <div class="flex space-x-2">
                        <button id="prev-slide">Previous</button>
                        <button id="next-slide">Next</button>
                    </div>
                </div>
                <span id="current-slide">1</span>
                <button id="fullscreen-button">Fullscreen</button>
            </body>
            </html>
        `, {
            url: 'http://localhost',
            pretendToBeVisual: true,
            resources: 'usable'
        });
        
        document = dom.window.document;
        window = dom.window;
        
        // Mock global objects
        global.document = document;
        global.window = window;
        global.IntersectionObserver = class {
            constructor(callback) {
                this.callback = callback;
            }
            observe() {}
            unobserve() {}
            disconnect() {}
        };
        
        // Mock MathJax
        global.MathJax = {
            config: {},
            typesetPromise: jest.fn().mockResolvedValue(undefined)
        };
        
        // Load the EnhancedSlideViewer class after setting up globals
        delete require.cache[require.resolve('../docs/assets/js/enhanced-slide-viewer.js')];
        
        // Ensure the module uses our mocked document
        const originalDocument = global.document;
        global.document = document;
        
        EnhancedSlideViewer = require('../docs/assets/js/enhanced-slide-viewer.js');
    });
    
    afterEach(() => {
        dom.window.close();
        delete global.document;
        delete global.window;
        delete global.IntersectionObserver;
        delete global.MathJax;
    });
    
    describe('Initialization', () => {
        test('should initialize with correct slide count', () => {
            // Verify slides exist in DOM first
            const slides = document.querySelectorAll('.slide');
            expect(slides.length).toBe(3);
            
            const viewer = new EnhancedSlideViewer();
            expect(viewer.totalSlides).toBe(3);
            expect(viewer.currentSlide).toBe(0);
            expect(viewer.speakerNotesVisible).toBe(false);
        });
        
        test('should set up all features on initialization', () => {
            const viewer = new EnhancedSlideViewer();
            
            // Check that fit text elements are processed
            const fitElements = document.querySelectorAll('.fit-text');
            expect(fitElements.length).toBe(1);
            
            // Check that speaker notes are hidden initially
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
                expect(note.getAttribute('aria-hidden')).toBe('true');
            });
        });
    });
    
    describe('Fit Text Scaling', () => {
        test('should scale fit text to container width', () => {
            const viewer = new EnhancedSlideViewer();
            const fitElement = document.querySelector('.fit-text');
            
            // Mock element dimensions
            Object.defineProperty(fitElement, 'scrollWidth', {
                value: 900, // Wider than container
                configurable: true
            });
            Object.defineProperty(fitElement.parentElement, 'offsetWidth', {
                value: 800,
                configurable: true
            });
            
            viewer.scaleFitText(fitElement);
            
            // Font size should be reduced
            const fontSize = parseInt(fitElement.style.fontSize);
            expect(fontSize).toBeLessThan(48);
            expect(fontSize).toBeGreaterThanOrEqual(12);
        });
        
        test('should set minimum font size and word break for very long text', () => {
            const viewer = new EnhancedSlideViewer();
            const fitElement = document.querySelector('.fit-text');
            
            // Mock very wide text
            Object.defineProperty(fitElement, 'scrollWidth', {
                value: 2000,
                configurable: true
            });
            Object.defineProperty(fitElement.parentElement, 'offsetWidth', {
                value: 400,
                configurable: true
            });
            
            viewer.scaleFitText(fitElement);
            
            expect(fitElement.style.fontSize).toBe('16px');
            expect(fitElement.style.wordBreak).toBe('break-word');
        });
    });
    
    describe('MathJax Integration', () => {
        test('should initialize MathJax with correct configuration', () => {
            const viewer = new EnhancedSlideViewer();
            
            expect(MathJax.config.tex).toBeDefined();
            expect(MathJax.config.tex.inlineMath).toEqual([['$', '$']]);
            expect(MathJax.config.tex.displayMath).toEqual([['$$', '$$']]);
            expect(MathJax.typesetPromise).toHaveBeenCalled();
        });
        
        test('should handle MathJax errors gracefully', () => {
            // Mock MathJax failure
            MathJax.typesetPromise = jest.fn().mockRejectedValue(new Error('MathJax failed'));
            
            const viewer = new EnhancedSlideViewer();
            const mathElement = document.querySelector('.math-display');
            
            // Simulate error handling
            viewer.handleMathJaxError();
            
            expect(mathElement.style.fontFamily).toBe('monospace');
            expect(mathElement.style.backgroundColor).toBe('#f3f4f6');
            expect(mathElement.dataset.fallbackShown).toBe('true');
        });
    });
    
    describe('Video Autoplay', () => {
        test('should set up intersection observer for autoplay videos', () => {
            const mockObserver = {
                observe: jest.fn(),
                unobserve: jest.fn(),
                disconnect: jest.fn()
            };
            
            global.IntersectionObserver = jest.fn().mockImplementation(() => mockObserver);
            
            const viewer = new EnhancedSlideViewer();
            const video = document.querySelector('video[data-autoplay="true"]');
            
            expect(global.IntersectionObserver).toHaveBeenCalled();
            expect(mockObserver.observe).toHaveBeenCalledWith(video);
        });
        
        test('should show play button when autoplay fails', () => {
            const viewer = new EnhancedSlideViewer();
            const video = document.querySelector('video[data-autoplay="true"]');
            
            // Mock video parent element
            video.parentElement = document.createElement('div');
            
            viewer.showVideoPlayButton(video);
            
            const overlay = video.parentElement.querySelector('.video-play-overlay');
            expect(overlay).toBeTruthy();
            expect(overlay.innerHTML).toBe('▶');
            expect(overlay.getAttribute('aria-label')).toBe('Play video');
        });
        
        test('should show error message for failed video loading', () => {
            const viewer = new EnhancedSlideViewer();
            const video = document.querySelector('video[data-autoplay="true"]');
            
            // Mock video parent element
            video.parentElement = document.createElement('div');
            
            viewer.showVideoError(video);
            
            const errorDiv = video.parentElement.querySelector('.video-error');
            expect(errorDiv).toBeTruthy();
            expect(errorDiv.textContent).toBe('Video could not be loaded');
            expect(video.style.display).toBe('none');
        });
    });
    
    describe('Speaker Notes', () => {
        test('should toggle speaker notes visibility', () => {
            const viewer = new EnhancedSlideViewer();
            const speakerNotes = document.querySelectorAll('.speaker-notes');
            
            // Initially hidden
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
                expect(note.getAttribute('aria-hidden')).toBe('true');
            });
            
            // Toggle to show
            viewer.toggleSpeakerNotes();
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('block');
                expect(note.getAttribute('aria-hidden')).toBe('false');
            });
            
            // Toggle to hide
            viewer.toggleSpeakerNotes();
            
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
                expect(note.getAttribute('aria-hidden')).toBe('true');
            });
        });
        
        test('should create speaker notes toggle button', () => {
            const viewer = new EnhancedSlideViewer();
            
            const toggleButton = document.getElementById('speaker-notes-toggle');
            expect(toggleButton).toBeTruthy();
            expect(toggleButton.getAttribute('aria-label')).toBe('Toggle speaker notes');
            expect(toggleButton.getAttribute('aria-pressed')).toBe('false');
        });
    });
    
    describe('Keyboard Navigation', () => {
        test('should navigate slides with arrow keys', () => {
            const viewer = new EnhancedSlideViewer();
            const goToSlideSpy = jest.spyOn(viewer, 'goToSlide');
            
            // Test right arrow
            const rightEvent = new window.KeyboardEvent('keydown', { key: 'ArrowRight' });
            document.dispatchEvent(rightEvent);
            expect(goToSlideSpy).toHaveBeenCalledWith(1);
            
            // Test left arrow
            viewer.currentSlide = 1;
            const leftEvent = new window.KeyboardEvent('keydown', { key: 'ArrowLeft' });
            document.dispatchEvent(leftEvent);
            expect(goToSlideSpy).toHaveBeenCalledWith(0);
        });
        
        test('should toggle speaker notes with N key', () => {
            const viewer = new EnhancedSlideViewer();
            const toggleSpy = jest.spyOn(viewer, 'toggleSpeakerNotes');
            
            const nEvent = new window.KeyboardEvent('keydown', { key: 'n' });
            document.dispatchEvent(nEvent);
            
            expect(toggleSpy).toHaveBeenCalled();
        });
        
        test('should navigate to first/last slide with Home/End keys', () => {
            const viewer = new EnhancedSlideViewer();
            const goToSlideSpy = jest.spyOn(viewer, 'goToSlide');
            
            // Test Home key
            const homeEvent = new window.KeyboardEvent('keydown', { key: 'Home' });
            document.dispatchEvent(homeEvent);
            expect(goToSlideSpy).toHaveBeenCalledWith(0);
            
            // Test End key
            const endEvent = new window.KeyboardEvent('keydown', { key: 'End' });
            document.dispatchEvent(endEvent);
            expect(goToSlideSpy).toHaveBeenCalledWith(2);
        });
    });
    
    describe('Slide Navigation', () => {
        test('should navigate to specific slide', () => {
            const viewer = new EnhancedSlideViewer();
            
            viewer.goToSlide(1);
            
            expect(viewer.currentSlide).toBe(1);
            expect(document.getElementById('current-slide').textContent).toBe('2');
            expect(window.location.hash).toBe('#slide-2');
            
            // Check slide visibility
            const slides = document.querySelectorAll('.slide');
            expect(slides[0].classList.contains('hidden')).toBe(true);
            expect(slides[1].classList.contains('hidden')).toBe(false);
            expect(slides[2].classList.contains('hidden')).toBe(true);
        });
        
        test('should update navigation button states', () => {
            const viewer = new EnhancedSlideViewer();
            const prevButton = document.getElementById('prev-slide');
            const nextButton = document.getElementById('next-slide');
            
            // First slide - prev should be disabled
            viewer.goToSlide(0);
            expect(prevButton.disabled).toBe(true);
            expect(nextButton.disabled).toBe(false);
            
            // Last slide - next should be disabled
            viewer.goToSlide(2);
            expect(prevButton.disabled).toBe(false);
            expect(nextButton.disabled).toBe(true);
        });
        
        test('should initialize from URL hash', () => {
            window.location.hash = '#slide-2';
            const viewer = new EnhancedSlideViewer();
            
            expect(viewer.currentSlide).toBe(1);
        });
    });
    
    describe('Accessibility', () => {
        test('should add ARIA labels to slides', () => {
            const viewer = new EnhancedSlideViewer();
            const slides = document.querySelectorAll('.slide');
            
            slides.forEach((slide, index) => {
                expect(slide.getAttribute('role')).toBe('img');
                expect(slide.getAttribute('aria-label')).toBe(`Slide ${index + 1} of 3`);
            });
        });
        
        test('should create skip navigation link', () => {
            const viewer = new EnhancedSlideViewer();
            
            const skipLink = document.querySelector('a[href="#slides-container"]');
            expect(skipLink).toBeTruthy();
            expect(skipLink.textContent).toBe('Skip to slides');
        });
        
        test('should create ARIA live region', () => {
            const viewer = new EnhancedSlideViewer();
            
            const liveRegion = document.getElementById('slide-announcements');
            expect(liveRegion).toBeTruthy();
            expect(liveRegion.getAttribute('aria-live')).toBe('polite');
            expect(liveRegion.getAttribute('aria-atomic')).toBe('true');
        });
        
        test('should announce slide changes', () => {
            const viewer = new EnhancedSlideViewer();
            
            viewer.announceSlideChange(2, 3);
            
            const liveRegion = document.getElementById('slide-announcements');
            expect(liveRegion.textContent).toBe('Slide 2 of 3');
        });
    });
    
    describe('Fullscreen', () => {
        test('should toggle fullscreen mode', () => {
            // Mock fullscreen API
            document.fullscreenElement = null;
            const mockRequestFullscreen = jest.fn().mockResolvedValue(undefined);
            const slidesContainer = document.getElementById('slides-container');
            slidesContainer.requestFullscreen = mockRequestFullscreen;
            
            const viewer = new EnhancedSlideViewer();
            
            viewer.toggleFullscreen();
            
            expect(mockRequestFullscreen).toHaveBeenCalled();
        });
        
        test('should exit fullscreen when already in fullscreen', () => {
            // Mock fullscreen API
            document.fullscreenElement = document.getElementById('slides-container');
            document.exitFullscreen = jest.fn().mockResolvedValue(undefined);
            
            const viewer = new EnhancedSlideViewer();
            
            viewer.toggleFullscreen();
            
            expect(document.exitFullscreen).toHaveBeenCalled();
        });
    });
    
    describe('Error Handling', () => {
        test('should handle missing elements gracefully', () => {
            // Remove elements to test error handling
            document.getElementById('prev-slide').remove();
            document.getElementById('next-slide').remove();
            document.getElementById('current-slide').remove();
            
            expect(() => {
                const viewer = new EnhancedSlideViewer();
                viewer.goToSlide(1);
            }).not.toThrow();
        });
        
        test('should handle invalid slide indices', () => {
            const viewer = new EnhancedSlideViewer();
            
            // Should not change slide for invalid indices
            viewer.goToSlide(-1);
            expect(viewer.currentSlide).toBe(0);
            
            viewer.goToSlide(10);
            expect(viewer.currentSlide).toBe(0);
        });
    });
});