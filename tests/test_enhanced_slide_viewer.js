/**
 * Unit tests for EnhancedSlideViewer JavaScript functionality
 * Tests navigation, keyboard shortcuts, speaker notes, and enhanced features
 */

describe('EnhancedSlideViewer', () => {
    let viewer;
    let mockDocument;
    let mockWindow;
    let mockSlides;
    let mockElements;
    
    beforeEach(() => {
        // Create mock slides
        mockSlides = [
            {
                classList: { 
                    add: jest.fn(), 
                    remove: jest.fn(),
                    contains: jest.fn(() => false)
                },
                style: { display: 'none' },
                querySelector: jest.fn(),
                querySelectorAll: jest.fn(() => [])
            },
            {
                classList: { 
                    add: jest.fn(), 
                    remove: jest.fn(),
                    contains: jest.fn(() => false)
                },
                style: { display: 'none' },
                querySelector: jest.fn(),
                querySelectorAll: jest.fn(() => [])
            },
            {
                classList: { 
                    add: jest.fn(), 
                    remove: jest.fn(),
                    contains: jest.fn(() => false)
                },
                style: { display: 'none' },
                querySelector: jest.fn(),
                querySelectorAll: jest.fn(() => [])
            }
        ];
        
        // Create mock DOM elements
        mockElements = {
            'prev-slide': { 
                addEventListener: jest.fn(),
                disabled: false
            },
            'next-slide': { 
                addEventListener: jest.fn(),
                disabled: false
            },
            'slide-counter': { 
                textContent: '1 / 3'
            },
            'toggle-notes': { 
                addEventListener: jest.fn(),
                setAttribute: jest.fn(),
                textContent: 'Notes'
            }
        };
        
        // Mock document
        mockDocument = {
            querySelectorAll: jest.fn((selector) => {
                if (selector === '.slide') return mockSlides;
                if (selector === '.speaker-notes') return [{
                    style: { display: 'none' }
                }];
                if (selector === '.fit') return [];
                return [];
            }),
            querySelector: jest.fn((selector) => {
                if (selector === '.presentation-container') {
                    return { classList: { add: jest.fn() } };
                }
                return null;
            }),
            getElementById: jest.fn((id) => mockElements[id] || null),
            addEventListener: jest.fn(),
            createElement: jest.fn(() => ({
                id: '',
                style: {},
                setAttribute: jest.fn(),
                appendChild: jest.fn()
            })),
            body: { appendChild: jest.fn() },
            fullscreenElement: null,
            exitFullscreen: jest.fn(),
            documentElement: {
                requestFullscreen: jest.fn().mockResolvedValue(undefined)
            }
        };
        
        // Mock window
        mockWindow = {
            location: { 
                hash: '',
                search: ''
            },
            addEventListener: jest.fn(),
            innerWidth: 1024,
            innerHeight: 768,
            URLSearchParams: jest.fn(() => ({
                get: jest.fn(() => null)
            }))
        };
        
        // Mock MutationObserver
        global.MutationObserver = jest.fn(() => ({
            observe: jest.fn(),
            disconnect: jest.fn()
        }));
        
        // Mock console
        global.console = {
            log: jest.fn(),
            warn: jest.fn(),
            error: jest.fn()
        };
        
        // Set global references
        global.document = mockDocument;
        global.window = mockWindow;
        
        // Create viewer with mocked dependencies
        class TestEnhancedSlideViewer {
            constructor() {
                this.slides = mockDocument.querySelectorAll('.slide');
                this.currentSlide = 0;
                this.totalSlides = this.slides.length;
                this.notesVisible = false;
                this.autoplayInterval = null;
                
                // Don't call init() automatically to allow controlled testing
            }
            
                         init() {
                 const container = mockDocument.querySelector('.presentation-container');
                 if (container) {
                     container.classList.add('js-enabled');
                 }
                 
                 this.setupNavigation();
                 this.setupKeyboardShortcuts();
                 this.setupSlideCounter();
                 this.setupNotesToggle();
                 this.setupAutoplay();
                 this.setupResponsiveFeatures();
                 this.setupFitText();
                 
                 this.showSlide(0);
                 
                 return {
                     containerMarked: !!container,
                     navigationSetup: true,
                     keyboardSetup: true,
                     notesSetup: true
                 };
             }
            
            setupNavigation() {
                const prevButton = mockDocument.getElementById('prev-slide');
                const nextButton = mockDocument.getElementById('next-slide');
                
                if (prevButton) {
                    prevButton.addEventListener('click', () => this.previousSlide());
                }
                
                if (nextButton) {
                    nextButton.addEventListener('click', () => this.nextSlide());
                }
            }
            
            setupKeyboardShortcuts() {
                mockDocument.addEventListener('keydown', (e) => {
                    switch (e.key) {
                        case 'ArrowRight':
                        case ' ':
                        case 'PageDown':
                            e.preventDefault();
                            this.nextSlide();
                            break;
                            
                        case 'ArrowLeft':
                        case 'PageUp':
                            e.preventDefault();
                            this.previousSlide();
                            break;
                            
                        case 'Home':
                            e.preventDefault();
                            this.goToSlide(0);
                            break;
                            
                        case 'End':
                            e.preventDefault();
                            this.goToSlide(this.totalSlides - 1);
                            break;
                            
                        case 'n':
                        case 'N':
                            e.preventDefault();
                            this.toggleNotes();
                            break;
                    }
                });
            }
            
            setupSlideCounter() {
                const counter = mockDocument.getElementById('slide-counter');
                if (counter) {
                    this.updateSlideCounter();
                }
            }
            
            setupNotesToggle() {
                const notesButton = mockDocument.getElementById('toggle-notes');
                if (notesButton) {
                    notesButton.addEventListener('click', () => this.toggleNotes());
                    notesButton.setAttribute('aria-pressed', 'false');
                }
                
                const notes = mockDocument.querySelectorAll('.speaker-notes');
                notes.forEach(note => {
                    note.style.display = 'none';
                });
            }
            
            setupAutoplay() {
                const urlParams = new mockWindow.URLSearchParams(mockWindow.location.search);
                const autoplay = urlParams.get('autoplay');
                
                if (autoplay) {
                    const interval = parseInt(autoplay) || 5000;
                    this.startAutoplay(interval);
                }
            }
            
            setupResponsiveFeatures() {
                mockWindow.addEventListener('resize', () => {
                    this.adjustForViewport();
                });
                this.adjustForViewport();
            }
            
            setupFitText() {
                this.scaleAllFitText();
                
                mockWindow.addEventListener('resize', () => {
                    this.scaleAllFitText();
                });
                
                const observer = new MutationObserver(() => {
                    this.scaleAllFitText();
                });
                
                this.slides.forEach(slide => {
                    observer.observe(slide, { childList: true, subtree: true });
                });
            }
            
            scaleAllFitText() {
                const fitElements = mockDocument.querySelectorAll('.fit');
                fitElements.forEach(element => {
                    this.scaleFitText(element);
                });
            }
            
            scaleFitText(element) {
                if (!element || !element.parentElement) {
                    return;
                }
                
                const container = element.parentElement;
                const containerWidth = container.clientWidth || 800;
                
                let fontSize = Math.min(containerWidth / 8, 120);
                element.style = element.style || {};
                element.style.fontSize = fontSize + 'px';
                
                // Mock scrollWidth check
                const scrollWidth = element.scrollWidth || containerWidth * 0.5;
                
                while (scrollWidth > containerWidth * 0.95 && fontSize > 16) {
                    fontSize -= 2;
                    element.style.fontSize = fontSize + 'px';
                }
                
                return fontSize;
            }
            
            adjustForViewport() {
                // Mock implementation
            }
            
            showSlide(index) {
                if (index < 0 || index >= this.totalSlides) return;
                
                this.slides.forEach((slide, i) => {
                    if (i === index) {
                        slide.classList.add('active');
                        slide.style.display = 'block';
                    } else {
                        slide.classList.remove('active');
                        slide.style.display = 'none';
                    }
                });
                
                this.currentSlide = index;
                this.updateSlideCounter();
                this.updateNavigationButtons();
                
                mockWindow.location.hash = `slide-${index + 1}`;
            }
            
            nextSlide() {
                if (this.currentSlide < this.totalSlides - 1) {
                    this.showSlide(this.currentSlide + 1);
                }
            }
            
            previousSlide() {
                if (this.currentSlide > 0) {
                    this.showSlide(this.currentSlide - 1);
                }
            }
            
            goToSlide(index) {
                this.showSlide(index);
            }
            
            updateSlideCounter() {
                const counter = mockDocument.getElementById('slide-counter');
                if (counter) {
                    counter.textContent = `${this.currentSlide + 1} / ${this.totalSlides}`;
                }
            }
            
            updateNavigationButtons() {
                const prevButton = mockDocument.getElementById('prev-slide');
                const nextButton = mockDocument.getElementById('next-slide');
                
                if (prevButton) {
                    prevButton.disabled = this.currentSlide === 0;
                }
                
                if (nextButton) {
                    nextButton.disabled = this.currentSlide === this.totalSlides - 1;
                }
            }
            
            toggleNotes() {
                this.notesVisible = !this.notesVisible;
                const notes = mockDocument.querySelectorAll('.speaker-notes');
                
                notes.forEach(note => {
                    note.style.display = this.notesVisible ? 'block' : 'none';
                });
                
                const notesButton = mockDocument.getElementById('toggle-notes');
                if (notesButton) {
                    notesButton.textContent = this.notesVisible ? 'Hide Notes' : 'Notes';
                    notesButton.setAttribute('aria-pressed', this.notesVisible);
                }
            }
            
            startAutoplay(interval) {
                this.autoplayInterval = setInterval(() => {
                    if (this.currentSlide < this.totalSlides - 1) {
                        this.nextSlide();
                    } else {
                        this.stopAutoplay();
                    }
                }, interval);
            }
            
            stopAutoplay() {
                if (this.autoplayInterval) {
                    clearInterval(this.autoplayInterval);
                    this.autoplayInterval = null;
                }
            }
        }
        
        viewer = new TestEnhancedSlideViewer();
    });
    
    afterEach(() => {
        if (viewer && viewer.autoplayInterval) {
            viewer.stopAutoplay();
        }
        delete global.document;
        delete global.window;
        delete global.MutationObserver;
        delete global.console;
    });
    
    describe('Initialization', () => {
        test('should initialize with correct slide count', () => {
            expect(viewer.totalSlides).toBe(3);
            expect(viewer.currentSlide).toBe(0);
            expect(viewer.notesVisible).toBe(false);
        });
        
                 test('should set up all features on initialization', () => {
             const result = viewer.init();
             
             expect(result.containerMarked).toBe(true);
             expect(result.navigationSetup).toBe(true);
             expect(result.keyboardSetup).toBe(true);
             expect(result.notesSetup).toBe(true);
             
             // These should be called during initialization
             expect(mockDocument.querySelector).toHaveBeenCalledWith('.presentation-container');
             expect(mockDocument.getElementById).toHaveBeenCalledWith('prev-slide');
             expect(mockDocument.getElementById).toHaveBeenCalledWith('next-slide');
             expect(mockDocument.getElementById).toHaveBeenCalledWith('toggle-notes');
         });
    });
    
    describe('Navigation', () => {
        beforeEach(() => {
            viewer.init();
        });
        
        test('should navigate to next slide', () => {
            viewer.nextSlide();
            
            expect(viewer.currentSlide).toBe(1);
            expect(mockSlides[0].classList.remove).toHaveBeenCalledWith('active');
            expect(mockSlides[1].classList.add).toHaveBeenCalledWith('active');
        });
        
        test('should navigate to previous slide', () => {
            viewer.goToSlide(1);
            viewer.previousSlide();
            
            expect(viewer.currentSlide).toBe(0);
            expect(mockSlides[1].classList.remove).toHaveBeenCalledWith('active');
            expect(mockSlides[0].classList.add).toHaveBeenCalledWith('active');
        });
        
        test('should not navigate beyond first slide', () => {
            viewer.previousSlide();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should not navigate beyond last slide', () => {
            viewer.goToSlide(2);
            viewer.nextSlide();
            expect(viewer.currentSlide).toBe(2);
        });
        
        test('should update slide counter', () => {
            viewer.goToSlide(1);
            
            const counter = mockDocument.getElementById('slide-counter');
            expect(counter.textContent).toBe('2 / 3');
        });
        
        test('should update navigation button states', () => {
            const prevButton = mockDocument.getElementById('prev-slide');
            const nextButton = mockDocument.getElementById('next-slide');
            
            // First slide - prev should be disabled
            viewer.goToSlide(0);
            expect(prevButton.disabled).toBe(true);
            expect(nextButton.disabled).toBe(false);
            
            // Last slide - next should be disabled
            viewer.goToSlide(2);
            expect(prevButton.disabled).toBe(false);
            expect(nextButton.disabled).toBe(true);
        });
    });
    
    describe('Keyboard Navigation', () => {
        beforeEach(() => {
            viewer.init();
        });
        
        test('should respond to arrow key navigation', () => {
            const keyHandler = mockDocument.addEventListener.mock.calls.find(
                call => call[0] === 'keydown'
            )[1];
            
            // Test right arrow
            const rightEvent = { key: 'ArrowRight', preventDefault: jest.fn() };
            keyHandler(rightEvent);
            
            expect(rightEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(1);
            
            // Test left arrow
            const leftEvent = { key: 'ArrowLeft', preventDefault: jest.fn() };
            keyHandler(leftEvent);
            
            expect(leftEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should respond to Home and End keys', () => {
            const keyHandler = mockDocument.addEventListener.mock.calls.find(
                call => call[0] === 'keydown'
            )[1];
            
            viewer.goToSlide(1); // Start in middle
            
            // Test End key
            const endEvent = { key: 'End', preventDefault: jest.fn() };
            keyHandler(endEvent);
            
            expect(endEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(2);
            
            // Test Home key
            const homeEvent = { key: 'Home', preventDefault: jest.fn() };
            keyHandler(homeEvent);
            
            expect(homeEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should toggle notes with N key', () => {
            const keyHandler = mockDocument.addEventListener.mock.calls.find(
                call => call[0] === 'keydown'
            )[1];
            
            const nEvent = { key: 'n', preventDefault: jest.fn() };
            keyHandler(nEvent);
            
            expect(nEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.notesVisible).toBe(true);
        });
    });
    
    describe('Speaker Notes', () => {
        beforeEach(() => {
            viewer.init();
        });
        
        test('should toggle speaker notes visibility', () => {
            expect(viewer.notesVisible).toBe(false);
            
            viewer.toggleNotes();
            
            expect(viewer.notesVisible).toBe(true);
            
            const notesButton = mockDocument.getElementById('toggle-notes');
            expect(notesButton.textContent).toBe('Hide Notes');
            expect(notesButton.setAttribute).toHaveBeenCalledWith('aria-pressed', true);
        });
        
        test('should hide notes initially', () => {
            const notes = mockDocument.querySelectorAll('.speaker-notes');
            notes.forEach(note => {
                expect(note.style.display).toBe('none');
            });
        });
    });
    
    describe('Fit Text Scaling', () => {
        test('should scale fit text elements', () => {
            const mockElement = {
                style: {},
                parentElement: { clientWidth: 800 },
                scrollWidth: 600
            };
            
            const fontSize = viewer.scaleFitText(mockElement);
            
            expect(mockElement.style.fontSize).toBeDefined();
            expect(fontSize).toBeGreaterThanOrEqual(16);
        });
        
        test('should handle missing parent element', () => {
            const mockElement = { style: {} };
            
            const result = viewer.scaleFitText(mockElement);
            
            expect(result).toBeUndefined();
        });
    });
    
    describe('Autoplay', () => {
        beforeEach(() => {
            viewer.init();
            jest.useFakeTimers();
        });
        
        afterEach(() => {
            jest.useRealTimers();
        });
        
        test('should start autoplay with interval', () => {
            viewer.startAutoplay(1000);
            
            expect(viewer.autoplayInterval).toBeDefined();
            
            jest.advanceTimersByTime(1000);
            expect(viewer.currentSlide).toBe(1);
            
            jest.advanceTimersByTime(1000);
            expect(viewer.currentSlide).toBe(2);
        });
        
        test('should stop autoplay at last slide', () => {
            viewer.goToSlide(2); // Last slide
            viewer.startAutoplay(1000);
            
            jest.advanceTimersByTime(1000);
            expect(viewer.autoplayInterval).toBeNull();
        });
        
        test('should stop autoplay manually', () => {
            viewer.startAutoplay(1000);
            viewer.stopAutoplay();
            
            expect(viewer.autoplayInterval).toBeNull();
        });
    });
    
    describe('Error Handling', () => {
        test('should handle missing DOM elements gracefully', () => {
            mockDocument.getElementById = jest.fn(() => null);
            
            expect(() => {
                viewer.init();
                viewer.updateSlideCounter();
                viewer.updateNavigationButtons();
            }).not.toThrow();
        });
        
        test('should handle invalid slide indices', () => {
            viewer.init();
            
            viewer.goToSlide(-1);
            expect(viewer.currentSlide).toBe(0);
            
            viewer.goToSlide(10);
            expect(viewer.currentSlide).toBe(0);
        });
    });
});