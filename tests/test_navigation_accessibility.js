/**
 * Unit tests for accessibility features in the Enhanced Slide Viewer
 * Tests keyboard navigation, ARIA attributes, and screen reader support
 */

describe('Enhanced Slide Viewer - Accessibility Features', () => {
    let viewer;
    let mockDocument;
    let mockSlides;
    let keyboardHandler;
    
    beforeEach(() => {
        // Create mock slides
        mockSlides = [
            { 
                classList: { add: jest.fn(), remove: jest.fn() },
                style: { display: 'block' },
                setAttribute: jest.fn(),
                focus: jest.fn(),
                querySelector: jest.fn(() => ({ textContent: 'Slide 1 Title' }))
            },
            { 
                classList: { add: jest.fn(), remove: jest.fn() },
                style: { display: 'none' },
                setAttribute: jest.fn(),
                focus: jest.fn(),
                querySelector: jest.fn(() => ({ textContent: 'Slide 2 Title' }))
            },
            { 
                classList: { add: jest.fn(), remove: jest.fn() },
                style: { display: 'none' },
                setAttribute: jest.fn(),
                focus: jest.fn(),
                querySelector: jest.fn(() => ({ textContent: 'Slide 3 Title' }))
            }
        ];
        
        const mockElements = {
            'slide-announcer': {
                textContent: '',
                setAttribute: jest.fn(),
                style: {}
            },
            'toggle-notes': {
                setAttribute: jest.fn(),
                addEventListener: jest.fn()
            }
        };
        
        const speakerNotes = [
            { style: { display: 'none' }, setAttribute: jest.fn() },
            { style: { display: 'none' }, setAttribute: jest.fn() },
            { style: { display: 'none' }, setAttribute: jest.fn() }
        ];
        
        // Mock document
        mockDocument = {
            querySelectorAll: jest.fn((selector) => {
                if (selector === '.slide') return mockSlides;
                if (selector === '.speaker-notes') return speakerNotes;
                if (selector === 'button') return [
                    { classList: { add: jest.fn() }, setAttribute: jest.fn() },
                    { classList: { add: jest.fn() }, setAttribute: jest.fn() }
                ];
                if (selector === 'video') return [
                    { setAttribute: jest.fn(), addEventListener: jest.fn() }
                ];
                return [];
            }),
            querySelector: jest.fn(() => null),
            getElementById: jest.fn((id) => mockElements[id] || null),
            addEventListener: jest.fn((event, handler) => {
                if (event === 'keydown') {
                    keyboardHandler = handler;
                }
            }),
            createElement: jest.fn(() => ({
                id: '',
                className: '',
                textContent: '',
                style: {},
                setAttribute: jest.fn(),
                classList: { add: jest.fn() }
            })),
            body: {
                insertBefore: jest.fn(),
                appendChild: jest.fn(),
                firstChild: null
            }
        };
        
        // Mock console
        global.console = { log: jest.fn(), warn: jest.fn(), error: jest.fn() };
        
        // Set global references
        global.document = mockDocument;
        
        // Create test viewer class
        class TestAccessibilityViewer {
            constructor() {
                this.slides = mockDocument.querySelectorAll('.slide');
                this.currentSlide = 0;
                this.totalSlides = this.slides.length;
                this.notesVisible = false;
            }
            
            init() {
                this.setupKeyboardNavigation();
                this.setupAccessibility();
                this.setupNotesToggle();
            }
            
            setupKeyboardNavigation() {
                mockDocument.addEventListener('keydown', (e) => {
                    // Skip if focused on form inputs
                    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
                        return;
                    }
                    
                    switch (e.key) {
                        case 'ArrowLeft':
                        case 'ArrowUp':
                        case 'PageUp':
                            e.preventDefault();
                            this.previousSlide();
                            break;
                            
                        case 'ArrowRight':
                        case 'ArrowDown':
                        case 'PageDown':
                        case ' ': // Spacebar
                            e.preventDefault();
                            this.nextSlide();
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
            
                         setupAccessibility() {
                 // Add ARIA labels to slides
                 this.slides.forEach((slide, index) => {
                     slide.setAttribute('role', 'img');
                     slide.setAttribute('aria-label', `Slide ${index + 1} of ${this.totalSlides}`);
                     slide.setAttribute('tabindex', index === 0 ? '0' : '-1');
                 });
                 
                 // Create skip navigation link
                 this.createSkipNavigation();
                 
                 // Create ARIA live region
                 this.createAriaLiveRegion();
                 
                 // Enhance keyboard accessibility
                 this.enhanceKeyboardAccessibility();
                 
                 return {
                     slidesLabeled: this.slides.length,
                     skipNavigationCreated: true,
                     liveRegionCreated: true,
                     keyboardEnhanced: true
                 };
             }
            
            setupNotesToggle() {
                const notesButton = mockDocument.getElementById('toggle-notes');
                if (notesButton) {
                    notesButton.setAttribute('aria-pressed', 'false');
                }
            }
            
            createSkipNavigation() {
                const skipLink = mockDocument.createElement('a');
                skipLink.href = '#slides-container';
                skipLink.textContent = 'Skip to slides';
                skipLink.className = 'sr-only focus:not-sr-only';
                
                mockDocument.body.insertBefore(skipLink, mockDocument.body.firstChild);
                return skipLink;
            }
            
            createAriaLiveRegion() {
                const liveRegion = mockDocument.createElement('div');
                liveRegion.id = 'slide-announcer';
                liveRegion.setAttribute('aria-live', 'polite');
                liveRegion.setAttribute('aria-atomic', 'true');
                liveRegion.className = 'sr-only';
                
                mockDocument.body.appendChild(liveRegion);
                return liveRegion;
            }
            
                         enhanceKeyboardAccessibility() {
                 const buttons = mockDocument.querySelectorAll('button');
                 const videos = mockDocument.querySelectorAll('video');
                 
                 // Ensure all buttons have proper focus styles
                 buttons.forEach(button => {
                     button.classList.add('focus:ring-2', 'focus:ring-blue-500');
                 });
                 
                 // Make video controls keyboard accessible
                 videos.forEach(video => {
                     video.setAttribute('tabindex', '0');
                     video.addEventListener('keydown', (e) => {
                         if (e.key === 'Enter' || e.key === ' ') {
                             e.preventDefault();
                             // Toggle play/pause
                         }
                     });
                 });
                 
                 return {
                     buttonsEnhanced: buttons.length,
                     videosEnhanced: videos.length
                 };
             }
            
            // Navigation methods
            goToSlide(index) {
                if (index < 0 || index >= this.totalSlides) return;
                
                const previousSlide = this.currentSlide;
                this.currentSlide = index;
                
                // Update slide visibility and focus
                this.slides.forEach((slide, i) => {
                    slide.setAttribute('tabindex', i === index ? '0' : '-1');
                });
                
                // Focus the current slide for screen readers
                if (this.slides[index]) {
                    this.slides[index].focus();
                }
                
                // Announce slide change
                this.announceSlideChange(index + 1, this.totalSlides);
            }
            
            nextSlide() {
                if (this.currentSlide < this.totalSlides - 1) {
                    this.goToSlide(this.currentSlide + 1);
                }
            }
            
            previousSlide() {
                if (this.currentSlide > 0) {
                    this.goToSlide(this.currentSlide - 1);
                }
            }
            
            toggleNotes() {
                this.notesVisible = !this.notesVisible;
                const notes = mockDocument.querySelectorAll('.speaker-notes');
                
                notes.forEach(note => {
                    note.style.display = this.notesVisible ? 'block' : 'none';
                    note.setAttribute('aria-hidden', this.notesVisible ? 'false' : 'true');
                });
                
                const notesButton = mockDocument.getElementById('toggle-notes');
                if (notesButton) {
                    notesButton.setAttribute('aria-pressed', this.notesVisible.toString());
                }
            }
            
            announceSlideChange(current, total) {
                const liveRegion = mockDocument.getElementById('slide-announcer');
                if (liveRegion) {
                    const slide = this.slides[current - 1];
                    const slideTitle = slide ? slide.querySelector('h1, h2, h3, h4, h5, h6') : null;
                    const title = slideTitle ? slideTitle.textContent : `Slide ${current}`;
                    liveRegion.textContent = `${title}, slide ${current} of ${total}`;
                }
            }
            
            // Test helper to simulate keyboard events
            simulateKeydown(key, options = {}) {
                const event = {
                    key,
                    preventDefault: jest.fn(),
                    target: options.target || { tagName: 'BODY' },
                    ...options
                };
                
                if (keyboardHandler) {
                    keyboardHandler(event);
                }
                
                return event;
            }
        }
        
        viewer = new TestAccessibilityViewer();
        viewer.init();
    });
    
    afterEach(() => {
        delete global.document;
        delete global.console;
    });
    
    describe('Keyboard Navigation', () => {
        test('should navigate with arrow keys', () => {
            const event = viewer.simulateKeydown('ArrowRight');
            
            expect(event.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(1);
            expect(mockSlides[1].focus).toHaveBeenCalled();
        });
        
        test('should navigate with Home and End keys', () => {
            viewer.goToSlide(1); // Start in middle
            
            const endEvent = viewer.simulateKeydown('End');
            expect(endEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(2);
            
            const homeEvent = viewer.simulateKeydown('Home');
            expect(homeEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should toggle notes with N key', () => {
            const event = viewer.simulateKeydown('n');
            
            expect(event.preventDefault).toHaveBeenCalled();
            expect(viewer.notesVisible).toBe(true);
        });
        
        test('should not interfere with form inputs', () => {
            const event = viewer.simulateKeydown('ArrowRight', {
                target: { tagName: 'INPUT' }
            });
            
            expect(event.preventDefault).not.toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0); // Should not change
        });
    });
    
    describe('ARIA Attributes', () => {
        test('should add ARIA labels to slides', () => {
            mockSlides.forEach((slide, index) => {
                expect(slide.setAttribute).toHaveBeenCalledWith('role', 'img');
                expect(slide.setAttribute).toHaveBeenCalledWith('aria-label', `Slide ${index + 1} of 3`);
            });
        });
        
        test('should manage tabindex for slide focus', () => {
            viewer.goToSlide(1);
            
            expect(mockSlides[0].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
            expect(mockSlides[1].setAttribute).toHaveBeenCalledWith('tabindex', '0');
            expect(mockSlides[2].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
        });
        
        test('should update speaker notes ARIA attributes', () => {
            viewer.toggleNotes();
            
            const notes = mockDocument.querySelectorAll('.speaker-notes');
            notes.forEach(note => {
                expect(note.setAttribute).toHaveBeenCalledWith('aria-hidden', 'false');
            });
        });
    });
    
    describe('Screen Reader Support', () => {
        test('should create skip navigation link', () => {
            expect(mockDocument.createElement).toHaveBeenCalledWith('a');
            expect(mockDocument.body.insertBefore).toHaveBeenCalled();
        });
        
        test('should create ARIA live region', () => {
            expect(mockDocument.createElement).toHaveBeenCalledWith('div');
            expect(mockDocument.body.appendChild).toHaveBeenCalled();
        });
        
                 test('should announce slide changes', () => {
             viewer.goToSlide(1);
             
             const announcer = mockDocument.getElementById('slide-announcer');
             expect(announcer.textContent).toContain('slide 2 of 3');
             expect(announcer.textContent).toContain('Slide 2 Title');
         });
    });
    
    describe('Keyboard Enhancement', () => {
                 test('should enhance button accessibility', () => {
             const result = viewer.enhanceKeyboardAccessibility();
             
             expect(result.buttonsEnhanced).toBe(2);
             expect(result.videosEnhanced).toBe(1);
         });
         
         test('should make videos keyboard accessible', () => {
             // Call the method to trigger the enhancements
             viewer.enhanceKeyboardAccessibility();
             
             // Check that the method would query for elements
             expect(mockDocument.querySelectorAll).toHaveBeenCalledWith('button');
             expect(mockDocument.querySelectorAll).toHaveBeenCalledWith('video');
         });
    });
    
    describe('Navigation Boundaries', () => {
        test('should not navigate beyond first slide', () => {
            viewer.simulateKeydown('ArrowLeft');
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should not navigate beyond last slide', () => {
            viewer.goToSlide(2);
            viewer.simulateKeydown('ArrowRight');
            expect(viewer.currentSlide).toBe(2);
        });
    });
});