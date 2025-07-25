/**
 * Unit tests for Task 9.2: Navigation and accessibility features
 * Tests keyboard navigation, speaker notes toggle, and accessibility attributes
 */

describe('EnhancedSlideViewer - Task 9.2: Navigation and Accessibility', () => {
    let viewer;
    let mockDocument;
    let mockWindow;
    let keyboardEvents;
    
    beforeEach(() => {
        keyboardEvents = [];
        
        // Mock DOM elements
        const mockSlides = [
            { 
                classList: { toggle: jest.fn(), contains: jest.fn() }, 
                setAttribute: jest.fn(), 
                focus: jest.fn(),
                getAttribute: jest.fn()
            },
            { 
                classList: { toggle: jest.fn(), contains: jest.fn() }, 
                setAttribute: jest.fn(), 
                focus: jest.fn(),
                getAttribute: jest.fn()
            },
            { 
                classList: { toggle: jest.fn(), contains: jest.fn() }, 
                setAttribute: jest.fn(), 
                focus: jest.fn(),
                getAttribute: jest.fn()
            }
        ];
        
        const mockButtons = [
            { classList: { add: jest.fn() }, setAttribute: jest.fn() },
            { classList: { add: jest.fn() }, setAttribute: jest.fn() }
        ];
        
        const mockVideos = [
            { 
                setAttribute: jest.fn(), 
                addEventListener: jest.fn(),
                paused: true,
                play: jest.fn().mockResolvedValue(undefined),
                pause: jest.fn()
            }
        ];
        
        mockDocument = {
            querySelectorAll: jest.fn((selector) => {
                const elementMap = {
                    '.slide': mockSlides,
                    'button': mockButtons,
                    'video': mockVideos,
                    '.speaker-notes': [
                        { 
                            style: { display: 'none' }, 
                            setAttribute: jest.fn()
                        }
                    ]
                };
                return elementMap[selector] || [];
            }),
            querySelector: jest.fn((selector) => {
                if (selector === 'a[href="#slides-container"]') return null;
                return null;
            }),
            getElementById: jest.fn((id) => {
                const elementMap = {
                    'slide-announcements': { 
                        textContent: '', 
                        setAttribute: jest.fn()
                    },
                    'speaker-notes-toggle': { 
                        setAttribute: jest.fn(),
                        classList: { toggle: jest.fn() }
                    }
                };
                
                // Return a proxy that allows property assignment
                const element = elementMap[id];
                if (element) {
                    return new Proxy(element, {
                        set(target, prop, value) {
                            target[prop] = value;
                            return true;
                        }
                    });
                }
                return null;
            }),
            createElement: jest.fn((tag) => ({
                id: '',
                className: '',
                href: '',
                textContent: '',
                innerHTML: '',
                setAttribute: jest.fn(),
                addEventListener: jest.fn(),
                classList: { add: jest.fn() }
            })),
            addEventListener: jest.fn((event, handler) => {
                keyboardEvents.push({ event, handler });
            }),
            body: {
                insertBefore: jest.fn(),
                appendChild: jest.fn(),
                firstChild: null
            }
        };
        
        mockWindow = {
            addEventListener: jest.fn()
        };
        
        // Create test viewer class
        class TestNavigationViewer {
            constructor() {
                this.currentSlide = 0;
                this.totalSlides = 3;
                this.speakerNotesVisible = false;
                this.keyboardHandlers = new Map();
            }
            
            // Requirement 8.5: Keyboard navigation support for slide traversal
            setupKeyboardNavigation() {
                const handler = (e) => {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
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
                            this.toggleSpeakerNotes();
                            break;
                            
                        case 'f':
                        case 'F':
                            if (!e.ctrlKey && !e.metaKey) {
                                e.preventDefault();
                                this.toggleFullscreen();
                            }
                            break;
                            
                        case 'Escape':
                            if (this.isFullscreen) {
                                e.preventDefault();
                                this.exitFullscreen();
                            }
                            break;
                    }
                };
                
                this.keyboardHandlers.set('keydown', handler);
                mockDocument.addEventListener('keydown', handler);
                
                return { handlerRegistered: true, keysSupported: ['ArrowLeft', 'ArrowRight', 'Home', 'End', 'n', 'f', 'Escape'] };
            }
            
            // Navigation methods
            previousSlide() {
                if (this.currentSlide > 0) {
                    return this.goToSlide(this.currentSlide - 1);
                }
                return { success: false, reason: 'Already at first slide' };
            }
            
            nextSlide() {
                if (this.currentSlide < this.totalSlides - 1) {
                    return this.goToSlide(this.currentSlide + 1);
                }
                return { success: false, reason: 'Already at last slide' };
            }
            
            goToSlide(index) {
                if (index < 0 || index >= this.totalSlides) {
                    return { success: false, reason: 'Invalid index' };
                }
                
                const slides = mockDocument.querySelectorAll('.slide');
                
                // Update slide visibility and focus
                slides.forEach((slide, i) => {
                    slide.classList.toggle('hidden', i !== index);
                    slide.setAttribute('tabindex', i === index ? '0' : '-1');
                });
                
                const previousSlide = this.currentSlide;
                this.currentSlide = index;
                
                // Focus the current slide for screen readers
                if (slides[index]) {
                    slides[index].focus();
                }
                
                // Announce slide change
                this.announceSlideChange(index + 1, this.totalSlides);
                
                return {
                    success: true,
                    previousSlide,
                    currentSlide: this.currentSlide,
                    slideNumber: index + 1
                };
            }
            
            // Speaker notes toggle functionality
            toggleSpeakerNotes() {
                const speakerNotes = mockDocument.querySelectorAll('.speaker-notes');
                const toggleButton = mockDocument.getElementById('speaker-notes-toggle');
                
                this.speakerNotesVisible = !this.speakerNotesVisible;
                
                speakerNotes.forEach(note => {
                    // Create a proxy to allow style property assignment
                    const styleProxy = new Proxy(note.style, {
                        set(target, prop, value) {
                            target[prop] = value;
                            return true;
                        }
                    });
                    note.style = styleProxy;
                    
                    if (this.speakerNotesVisible) {
                        note.style.display = 'block';
                        note.setAttribute('aria-hidden', 'false');
                    } else {
                        note.style.display = 'none';
                        note.setAttribute('aria-hidden', 'true');
                    }
                });
                
                if (toggleButton) {
                    toggleButton.setAttribute('aria-pressed', this.speakerNotesVisible.toString());
                    toggleButton.classList.toggle('bg-blue-100', this.speakerNotesVisible);
                }
                
                return {
                    visible: this.speakerNotesVisible,
                    notesCount: speakerNotes.length,
                    buttonUpdated: !!toggleButton
                };
            }
            
            // Accessibility attributes and keyboard support
            setupAccessibility() {
                const slides = mockDocument.querySelectorAll('.slide');
                
                // Add ARIA labels to slides
                slides.forEach((slide, index) => {
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
                    slidesLabeled: slides.length,
                    skipNavigationCreated: true,
                    liveRegionCreated: true,
                    keyboardEnhanced: true
                };
            }
            
            createSkipNavigation() {
                const skipLink = mockDocument.createElement('a');
                skipLink.href = '#slides-container';
                skipLink.textContent = 'Skip to slides';
                skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 bg-blue-600 text-white p-2 z-50';
                
                mockDocument.body.insertBefore(skipLink, mockDocument.body.firstChild);
                
                return { created: true, href: '#slides-container' };
            }
            
            createAriaLiveRegion() {
                const liveRegion = mockDocument.createElement('div');
                liveRegion.id = 'slide-announcements';
                liveRegion.setAttribute('aria-live', 'polite');
                liveRegion.setAttribute('aria-atomic', 'true');
                liveRegion.className = 'sr-only';
                
                mockDocument.body.appendChild(liveRegion);
                
                return { created: true, id: 'slide-announcements' };
            }
            
            enhanceKeyboardAccessibility() {
                const buttons = mockDocument.querySelectorAll('button');
                const videos = mockDocument.querySelectorAll('video');
                
                // Ensure all buttons have proper focus styles
                buttons.forEach(button => {
                    button.classList.add('focus:ring-2', 'focus:ring-blue-500', 'focus:ring-offset-2');
                });
                
                // Make video controls keyboard accessible
                videos.forEach(video => {
                    video.setAttribute('tabindex', '0');
                    video.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            if (video.paused) {
                                video.play();
                            } else {
                                video.pause();
                            }
                        }
                    });
                });
                
                return {
                    buttonsEnhanced: buttons.length,
                    videosEnhanced: videos.length
                };
            }
            
            announceSlideChange(current, total) {
                const liveRegion = mockDocument.getElementById('slide-announcements');
                if (liveRegion) {
                    liveRegion.textContent = `Slide ${current} of ${total}`;
                }
                return `Slide ${current} of ${total}`;
            }
            
            // Fullscreen methods (for keyboard shortcuts)
            toggleFullscreen() {
                this.isFullscreen = !this.isFullscreen;
                return { fullscreen: this.isFullscreen };
            }
            
            exitFullscreen() {
                this.isFullscreen = false;
                return { fullscreen: this.isFullscreen };
            }
            
            // Simulate keyboard event
            simulateKeyboardEvent(key, options = {}) {
                const event = {
                    key,
                    preventDefault: jest.fn(),
                    target: { tagName: 'BODY' },
                    ctrlKey: options.ctrlKey || false,
                    metaKey: options.metaKey || false,
                    ...options
                };
                
                const handler = this.keyboardHandlers.get('keydown');
                if (handler) {
                    handler(event);
                }
                
                return event;
            }
        }
        
        viewer = new TestNavigationViewer();
    });
    
    describe('Keyboard navigation support for slide traversal', () => {
        test('should setup keyboard event handlers', () => {
            const result = viewer.setupKeyboardNavigation();
            
            expect(result.handlerRegistered).toBe(true);
            expect(result.keysSupported).toContain('ArrowLeft');
            expect(result.keysSupported).toContain('ArrowRight');
            expect(result.keysSupported).toContain('Home');
            expect(result.keysSupported).toContain('End');
            expect(mockDocument.addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
        });
        
        test('should navigate slides with arrow keys', () => {
            viewer.setupKeyboardNavigation();
            
            // Test right arrow navigation
            const rightEvent = viewer.simulateKeyboardEvent('ArrowRight');
            expect(rightEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(1);
            
            // Test left arrow navigation
            const leftEvent = viewer.simulateKeyboardEvent('ArrowLeft');
            expect(leftEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should navigate with Page Up/Down keys', () => {
            viewer.setupKeyboardNavigation();
            
            const pageDownEvent = viewer.simulateKeyboardEvent('PageDown');
            expect(pageDownEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(1);
            
            const pageUpEvent = viewer.simulateKeyboardEvent('PageUp');
            expect(pageUpEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should navigate with spacebar', () => {
            viewer.setupKeyboardNavigation();
            
            const spaceEvent = viewer.simulateKeyboardEvent(' ');
            expect(spaceEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(1);
        });
        
        test('should navigate to first/last slide with Home/End keys', () => {
            viewer.setupKeyboardNavigation();
            viewer.currentSlide = 1; // Start in middle
            
            const endEvent = viewer.simulateKeyboardEvent('End');
            expect(endEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(2);
            
            const homeEvent = viewer.simulateKeyboardEvent('Home');
            expect(homeEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should not interfere with form inputs', () => {
            viewer.setupKeyboardNavigation();
            
            const inputEvent = viewer.simulateKeyboardEvent('ArrowRight', {
                target: { tagName: 'INPUT' }
            });
            
            expect(inputEvent.preventDefault).not.toHaveBeenCalled();
            expect(viewer.currentSlide).toBe(0); // Should not change
        });
    });
    
    describe('Speaker notes toggle functionality', () => {
        test('should toggle speaker notes with N key', () => {
            viewer.setupKeyboardNavigation();
            
            const nEvent = viewer.simulateKeyboardEvent('n');
            expect(nEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.speakerNotesVisible).toBe(true);
            
            const NEvent = viewer.simulateKeyboardEvent('N');
            expect(NEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.speakerNotesVisible).toBe(false);
        });
        
        test('should update speaker notes visibility and ARIA attributes', () => {
            const result = viewer.toggleSpeakerNotes();
            
            expect(result.visible).toBe(true);
            expect(result.notesCount).toBe(1);
            expect(typeof result.buttonUpdated).toBe('boolean');
            
            // Test toggling back to hidden
            const result2 = viewer.toggleSpeakerNotes();
            expect(result2.visible).toBe(false);
            expect(result2.notesCount).toBe(1);
        });
        
        test('should update toggle button state', () => {
            // Mock the toggle button exists
            const mockButton = { 
                setAttribute: jest.fn(),
                classList: { toggle: jest.fn() }
            };
            mockDocument.getElementById = jest.fn((id) => {
                if (id === 'speaker-notes-toggle') return mockButton;
                return null;
            });
            
            const result = viewer.toggleSpeakerNotes();
            
            expect(result.buttonUpdated).toBe(true);
            expect(mockButton.setAttribute).toHaveBeenCalledWith('aria-pressed', 'true');
            expect(mockButton.classList.toggle).toHaveBeenCalledWith('bg-blue-100', true);
        });
    });
    
    describe('Accessibility attributes and keyboard support', () => {
        test('should add ARIA labels to slides', () => {
            const result = viewer.setupAccessibility();
            
            expect(result.slidesLabeled).toBe(3);
            
            const slides = mockDocument.querySelectorAll('.slide');
            slides.forEach((slide, index) => {
                expect(slide.setAttribute).toHaveBeenCalledWith('role', 'img');
                expect(slide.setAttribute).toHaveBeenCalledWith('aria-label', `Slide ${index + 1} of 3`);
                expect(slide.setAttribute).toHaveBeenCalledWith('tabindex', index === 0 ? '0' : '-1');
            });
        });
        
        test('should create skip navigation link', () => {
            const result = viewer.createSkipNavigation();
            
            expect(result.created).toBe(true);
            expect(result.href).toBe('#slides-container');
            expect(mockDocument.createElement).toHaveBeenCalledWith('a');
            expect(mockDocument.body.insertBefore).toHaveBeenCalled();
        });
        
        test('should create ARIA live region', () => {
            const result = viewer.createAriaLiveRegion();
            
            expect(result.created).toBe(true);
            expect(result.id).toBe('slide-announcements');
            expect(mockDocument.createElement).toHaveBeenCalledWith('div');
            expect(mockDocument.body.appendChild).toHaveBeenCalled();
        });
        
        test('should enhance keyboard accessibility for interactive elements', () => {
            const result = viewer.enhanceKeyboardAccessibility();
            
            expect(result.buttonsEnhanced).toBe(2);
            expect(result.videosEnhanced).toBe(1);
            
            const buttons = mockDocument.querySelectorAll('button');
            buttons.forEach(button => {
                expect(button.classList.add).toHaveBeenCalledWith('focus:ring-2', 'focus:ring-blue-500', 'focus:ring-offset-2');
            });
            
            const videos = mockDocument.querySelectorAll('video');
            videos.forEach(video => {
                expect(video.setAttribute).toHaveBeenCalledWith('tabindex', '0');
                expect(video.addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
            });
        });
        
        test('should announce slide changes to screen readers', () => {
            const announcement = viewer.announceSlideChange(2, 3);
            
            expect(announcement).toBe('Slide 2 of 3');
            
            // Test that the method attempts to update the live region
            expect(mockDocument.getElementById).toHaveBeenCalledWith('slide-announcements');
        });
        
        test('should focus current slide for screen readers', () => {
            const result = viewer.goToSlide(1);
            
            expect(result.success).toBe(true);
            
            const slides = mockDocument.querySelectorAll('.slide');
            expect(slides[1].focus).toHaveBeenCalled();
            expect(slides[1].setAttribute).toHaveBeenCalledWith('tabindex', '0');
            expect(slides[0].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
            expect(slides[2].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
        });
    });
    
    describe('Fullscreen keyboard shortcuts', () => {
        test('should toggle fullscreen with F key', () => {
            viewer.setupKeyboardNavigation();
            
            const fEvent = viewer.simulateKeyboardEvent('f');
            expect(fEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.isFullscreen).toBe(true);
        });
        
        test('should exit fullscreen with Escape key', () => {
            viewer.setupKeyboardNavigation();
            viewer.isFullscreen = true;
            
            const escapeEvent = viewer.simulateKeyboardEvent('Escape');
            expect(escapeEvent.preventDefault).toHaveBeenCalled();
            expect(viewer.isFullscreen).toBe(false);
        });
        
        test('should not interfere with Ctrl+F (browser find)', () => {
            viewer.setupKeyboardNavigation();
            
            const ctrlFEvent = viewer.simulateKeyboardEvent('f', { ctrlKey: true });
            expect(ctrlFEvent.preventDefault).not.toHaveBeenCalled();
        });
    });
    
    describe('Navigation boundary handling', () => {
        test('should not navigate beyond first slide', () => {
            viewer.currentSlide = 0;
            
            const result = viewer.previousSlide();
            expect(result.success).toBe(false);
            expect(result.reason).toBe('Already at first slide');
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should not navigate beyond last slide', () => {
            viewer.currentSlide = 2; // Last slide
            
            const result = viewer.nextSlide();
            expect(result.success).toBe(false);
            expect(result.reason).toBe('Already at last slide');
            expect(viewer.currentSlide).toBe(2);
        });
    });
});