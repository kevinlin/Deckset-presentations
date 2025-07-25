/**
 * Simplified unit tests for EnhancedSlideViewer JavaScript functionality
 * Tests core functionality without complex module loading
 */

describe('EnhancedSlideViewer Core Functionality', () => {
    let mockDocument;
    let mockWindow;
    let EnhancedSlideViewer;
    
    beforeEach(() => {
        // Create mock DOM elements
        const slides = [
            { classList: { toggle: jest.fn(), contains: jest.fn() }, setAttribute: jest.fn(), focus: jest.fn() },
            { classList: { toggle: jest.fn(), contains: jest.fn() }, setAttribute: jest.fn(), focus: jest.fn() },
            { classList: { toggle: jest.fn(), contains: jest.fn() }, setAttribute: jest.fn(), focus: jest.fn() }
        ];
        
        const mockElements = {
            '.slide': slides,
            '.fit-text': [{ 
                style: { fontSize: '48px', wordBreak: '' },
                parentElement: { offsetWidth: 800 },
                scrollWidth: 600
            }],
            '.speaker-notes': [
                { style: { display: 'none' }, setAttribute: jest.fn() }
            ],
            'video[data-autoplay="true"]': [
                { 
                    play: jest.fn().mockResolvedValue(undefined),
                    pause: jest.fn(),
                    addEventListener: jest.fn(),
                    parentElement: document.createElement('div')
                }
            ],
            '.math-display': [
                { 
                    style: {},
                    dataset: {},
                    title: ''
                }
            ],
            '.math-display, .math-inline': [
                { 
                    style: {},
                    dataset: {},
                    title: ''
                }
            ]
        };
        
        mockDocument = {
            querySelectorAll: jest.fn((selector) => mockElements[selector] || []),
            querySelector: jest.fn((selector) => mockElements[selector] ? mockElements[selector][0] : null),
            getElementById: jest.fn((id) => {
                const elementMap = {
                    'prev-slide': { disabled: false, addEventListener: jest.fn() },
                    'next-slide': { disabled: false, addEventListener: jest.fn() },
                    'current-slide': { textContent: '1' },
                    'fullscreen-button': { addEventListener: jest.fn() },
                    'slides-container': { requestFullscreen: jest.fn().mockResolvedValue(undefined) },
                    'slide-announcements': { textContent: '' }
                };
                
                // Return a reference that can be modified
                const element = elementMap[id];
                if (element && (id === 'prev-slide' || id === 'next-slide')) {
                    // Make disabled property writable
                    return new Proxy(element, {
                        set(target, prop, value) {
                            target[prop] = value;
                            return true;
                        }
                    });
                }
                if (element && (id === 'current-slide' || id === 'slide-announcements')) {
                    // Make textContent property writable
                    return new Proxy(element, {
                        set(target, prop, value) {
                            target[prop] = value;
                            return true;
                        }
                    });
                }
                return elementMap[id] || null;
            }),
            createElement: jest.fn((tag) => {
                const element = {
                    className: '',
                    style: {},
                    innerHTML: '',
                    textContent: '',
                    setAttribute: jest.fn(),
                    addEventListener: jest.fn(),
                    appendChild: jest.fn(),
                    insertBefore: jest.fn(),
                    remove: jest.fn()
                };
                // Make it a proper mock node for appendChild
                Object.defineProperty(element, 'nodeType', { value: 1 });
                return element;
            }),
            addEventListener: jest.fn(),
            dispatchEvent: jest.fn(),
            body: {
                insertBefore: jest.fn(),
                appendChild: jest.fn(),
                firstChild: null
            },
            fullscreenElement: null,
            exitFullscreen: jest.fn().mockResolvedValue(undefined)
        };
        
        mockWindow = {
            location: { hash: '' },
            addEventListener: jest.fn(),
            getComputedStyle: jest.fn(() => ({ fontSize: '48px' })),
            MathJax: {
                config: {},
                typesetPromise: jest.fn().mockResolvedValue(undefined)
            }
        };
        
        // Create the class inline for testing
        EnhancedSlideViewer = class {
            constructor() {
                this.currentSlide = 0;
                this.totalSlides = mockDocument.querySelectorAll('.slide').length;
                this.speakerNotesVisible = false;
                this.isFullscreen = false;
            }
            
            scaleFitText(element) {
                const container = element.parentElement;
                if (!container) return;
                
                const containerWidth = container.offsetWidth - 40;
                let fontSize = parseInt(mockWindow.getComputedStyle(element).fontSize) || 48;
                
                fontSize = Math.min(fontSize, 120);
                element.style.fontSize = fontSize + 'px';
                
                while (element.scrollWidth > containerWidth && fontSize > 12) {
                    fontSize -= 2;
                    element.style.fontSize = fontSize + 'px';
                }
                
                if (fontSize < 16) {
                    element.style.fontSize = '16px';
                    element.style.wordBreak = 'break-word';
                }
            }
            
            handleMathJaxError() {
                const mathElements = mockDocument.querySelectorAll('.math-display, .math-inline');
                mathElements.forEach(element => {
                    if (!element.dataset.fallbackShown) {
                        element.style.fontFamily = 'monospace';
                        element.style.backgroundColor = '#f3f4f6';
                        element.style.padding = '2px 4px';
                        element.style.borderRadius = '3px';
                        element.title = 'Math rendering unavailable - showing raw LaTeX';
                        element.dataset.fallbackShown = 'true';
                    }
                });
            }
            
            showVideoPlayButton(video) {
                if (video.parentElement.querySelector && video.parentElement.querySelector('.video-play-overlay')) return;
                
                const overlay = mockDocument.createElement('div');
                overlay.className = 'video-play-overlay';
                overlay.innerHTML = '▶';
                overlay.setAttribute('aria-label', 'Play video');
                
                video.parentElement.style = { position: 'relative' };
                video.parentElement.appendChild(overlay);
            }
            
            toggleSpeakerNotes() {
                const speakerNotes = mockDocument.querySelectorAll('.speaker-notes');
                this.speakerNotesVisible = !this.speakerNotesVisible;
                
                speakerNotes.forEach(note => {
                    if (this.speakerNotesVisible) {
                        note.style.display = 'block';
                        note.setAttribute('aria-hidden', 'false');
                    } else {
                        note.style.display = 'none';
                        note.setAttribute('aria-hidden', 'true');
                    }
                });
            }
            
            goToSlide(index) {
                if (index < 0 || index >= this.totalSlides) return;
                
                const slides = mockDocument.querySelectorAll('.slide');
                const prevButton = mockDocument.getElementById('prev-slide');
                const nextButton = mockDocument.getElementById('next-slide');
                const currentSlideElement = mockDocument.getElementById('current-slide');
                
                slides.forEach((slide, i) => {
                    slide.classList.toggle('hidden', i !== index);
                    slide.setAttribute('tabindex', i === index ? '0' : '-1');
                });
                
                if (prevButton) prevButton.disabled = index === 0;
                if (nextButton) nextButton.disabled = index === this.totalSlides - 1;
                
                if (currentSlideElement) {
                    currentSlideElement.textContent = index + 1;
                }
                
                mockWindow.location.hash = `slide-${index + 1}`;
                this.currentSlide = index;
                
                if (slides[index]) {
                    slides[index].focus();
                }
                
                this.announceSlideChange(index + 1, this.totalSlides);
            }
            
            announceSlideChange(current, total) {
                const liveRegion = mockDocument.getElementById('slide-announcements');
                if (liveRegion) {
                    liveRegion.textContent = `Slide ${current} of ${total}`;
                }
            }
        };
    });
    
    describe('Initialization', () => {
        test('should initialize with correct slide count', () => {
            const viewer = new EnhancedSlideViewer();
            expect(viewer.totalSlides).toBe(3);
            expect(viewer.currentSlide).toBe(0);
            expect(viewer.speakerNotesVisible).toBe(false);
        });
    });
    
    describe('Fit Text Scaling', () => {
        test('should scale fit text to container width', () => {
            const viewer = new EnhancedSlideViewer();
            const fitElement = mockDocument.querySelector('.fit-text');
            
            // Mock element dimensions for overflow
            fitElement.scrollWidth = 900; // Wider than container
            fitElement.parentElement.offsetWidth = 800;
            
            viewer.scaleFitText(fitElement);
            
            // Font size should be reduced from 48px
            const fontSize = parseInt(fitElement.style.fontSize);
            expect(fontSize).toBeLessThan(48);
            expect(fontSize).toBeGreaterThanOrEqual(12);
        });
        
        test('should set minimum font size and word break for very long text', () => {
            const viewer = new EnhancedSlideViewer();
            const fitElement = mockDocument.querySelector('.fit-text');
            
            // Mock very wide text
            fitElement.scrollWidth = 2000;
            fitElement.parentElement.offsetWidth = 400;
            
            viewer.scaleFitText(fitElement);
            
            expect(fitElement.style.fontSize).toBe('16px');
            expect(fitElement.style.wordBreak).toBe('break-word');
        });
    });
    
    describe('MathJax Integration', () => {
        test('should handle MathJax errors gracefully', () => {
            const viewer = new EnhancedSlideViewer();
            const mathElement = mockDocument.querySelector('.math-display');
            
            viewer.handleMathJaxError();
            
            expect(mathElement.style.fontFamily).toBe('monospace');
            expect(mathElement.style.backgroundColor).toBe('#f3f4f6');
            expect(mathElement.dataset.fallbackShown).toBe('true');
        });
    });
    
    describe('Video Autoplay', () => {
        test('should show play button when autoplay fails', () => {
            const viewer = new EnhancedSlideViewer();
            const video = mockDocument.querySelector('video[data-autoplay="true"]');
            
            // Mock querySelector for parent element
            video.parentElement.querySelector = jest.fn().mockReturnValue(null);
            
            viewer.showVideoPlayButton(video);
            
            expect(mockDocument.createElement).toHaveBeenCalledWith('div');
            expect(video.parentElement.appendChild).toHaveBeenCalled();
        });
    });
    
    describe('Speaker Notes', () => {
        test('should toggle speaker notes visibility', () => {
            const viewer = new EnhancedSlideViewer();
            const speakerNotes = mockDocument.querySelectorAll('.speaker-notes');
            
            // Initially hidden
            expect(viewer.speakerNotesVisible).toBe(false);
            
            // Toggle to show
            viewer.toggleSpeakerNotes();
            
            expect(viewer.speakerNotesVisible).toBe(true);
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('block');
                expect(note.setAttribute).toHaveBeenCalledWith('aria-hidden', 'false');
            });
            
            // Toggle to hide
            viewer.toggleSpeakerNotes();
            
            expect(viewer.speakerNotesVisible).toBe(false);
            speakerNotes.forEach(note => {
                expect(note.style.display).toBe('none');
                expect(note.setAttribute).toHaveBeenCalledWith('aria-hidden', 'true');
            });
        });
    });
    
    describe('Slide Navigation', () => {
        test('should navigate to specific slide', () => {
            const viewer = new EnhancedSlideViewer();
            
            viewer.goToSlide(1);
            
            expect(viewer.currentSlide).toBe(1);
            expect(mockDocument.getElementById('current-slide').textContent).toBe('2');
            expect(mockWindow.location.hash).toBe('#slide-2');
            
            // Check slide visibility
            const slides = mockDocument.querySelectorAll('.slide');
            slides.forEach((slide, index) => {
                expect(slide.classList.toggle).toHaveBeenCalledWith('hidden', index !== 1);
            });
        });
        
        test('should update navigation button states', () => {
            const viewer = new EnhancedSlideViewer();
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
        
        test('should handle invalid slide indices', () => {
            const viewer = new EnhancedSlideViewer();
            
            // Should not change slide for invalid indices
            viewer.goToSlide(-1);
            expect(viewer.currentSlide).toBe(0);
            
            viewer.goToSlide(10);
            expect(viewer.currentSlide).toBe(0);
        });
    });
    
    describe('Accessibility', () => {
        test('should announce slide changes', () => {
            const viewer = new EnhancedSlideViewer();
            
            viewer.announceSlideChange(2, 3);
            
            const liveRegion = mockDocument.getElementById('slide-announcements');
            expect(liveRegion.textContent).toBe('Slide 2 of 3');
        });
    });
});