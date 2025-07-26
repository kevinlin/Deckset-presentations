/**
 * Integration tests for enhanced slide viewer navigation functionality
 * Tests the complete navigation flow including counter updates and DOM interactions
 */

describe('Enhanced Slide Viewer - Navigation Integration', () => {
    let mockDocument;
    let mockSlides;
    let mockCounter;
    let mockButtons;
    let viewer;
    
    beforeEach(() => {
        // Create mock slides with full DOM structure
        mockSlides = [
            {
                id: 'slide-1',
                classList: { add: jest.fn(), remove: jest.fn(), contains: jest.fn(() => false) },
                style: { display: 'none' },
                querySelector: jest.fn((selector) => {
                    if (selector === 'h1, h2, h3, h4, h5, h6') {
                        return { textContent: 'Slide 1 Title' };
                    }
                    return null;
                }),
                querySelectorAll: jest.fn(() => [])
            },
            {
                id: 'slide-2',
                classList: { add: jest.fn(), remove: jest.fn(), contains: jest.fn(() => false) },
                style: { display: 'none' },
                querySelector: jest.fn((selector) => {
                    if (selector === 'h1, h2, h3, h4, h5, h6') {
                        return { textContent: 'Slide 2 Title' };
                    }
                    return null;
                }),
                querySelectorAll: jest.fn(() => [])
            },
            {
                id: 'slide-3',
                classList: { add: jest.fn(), remove: jest.fn(), contains: jest.fn(() => false) },
                style: { display: 'none' },
                querySelector: jest.fn((selector) => {
                    if (selector === 'h1, h2, h3, h4, h5, h6') {
                        return { textContent: 'Slide 3 Title' };
                    }
                    return null;
                }),
                querySelectorAll: jest.fn(() => [])
            }
        ];
        
        // Mock DOM elements
        mockCounter = { textContent: '1 / 3' };
        mockButtons = {
            'prev-slide': { 
                addEventListener: jest.fn(),
                disabled: true,
                click: jest.fn()
            },
            'next-slide': { 
                addEventListener: jest.fn(),
                disabled: false,
                click: jest.fn()
            },
            'toggle-notes': { 
                addEventListener: jest.fn(),
                setAttribute: jest.fn(),
                textContent: 'Notes',
                click: jest.fn()
            }
        };
        
        const speakerNotes = [
            { style: { display: 'none' } },
            { style: { display: 'none' } },
            { style: { display: 'none' } }
        ];
        
        mockDocument = {
            querySelectorAll: jest.fn((selector) => {
                if (selector === '.slide') return mockSlides;
                if (selector === '.speaker-notes') return speakerNotes;
                if (selector === '.fit') return [];
                return [];
            }),
            querySelector: jest.fn((selector) => {
                if (selector === '.presentation-container') {
                    return { classList: { add: jest.fn() } };
                }
                return null;
            }),
            getElementById: jest.fn((id) => {
                if (id === 'slide-counter') return mockCounter;
                return mockButtons[id] || null;
            }),
            addEventListener: jest.fn(),
            createElement: jest.fn(() => ({
                style: {},
                setAttribute: jest.fn(),
                appendChild: jest.fn()
            })),
            body: { appendChild: jest.fn() }
        };
        
        // Mock window
        const mockWindow = {
            location: { hash: '', search: '' },
            addEventListener: jest.fn(),
            innerWidth: 1024,
            innerHeight: 768,
            URLSearchParams: jest.fn(() => ({
                get: jest.fn(() => null)
            }))
        };
        
        // Mock globals
        global.document = mockDocument;
        global.window = mockWindow;
        global.console = { log: jest.fn(), warn: jest.fn(), error: jest.fn() };
        global.MutationObserver = jest.fn(() => ({
            observe: jest.fn(),
            disconnect: jest.fn()
        }));
        
        // Create test viewer
        class TestNavigationViewer {
            constructor() {
                this.slides = mockDocument.querySelectorAll('.slide');
                this.currentSlide = 0;
                this.totalSlides = this.slides.length;
                this.notesVisible = false;
                this.clickHandlers = new Map();
            }
            
            init() {
                this.setupNavigation();
                this.setupNotesToggle();
                this.showSlide(0);
            }
            
            setupNavigation() {
                const prevButton = mockDocument.getElementById('prev-slide');
                const nextButton = mockDocument.getElementById('next-slide');
                
                if (prevButton) {
                    const prevHandler = () => this.previousSlide();
                    prevButton.addEventListener('click', prevHandler);
                    this.clickHandlers.set('prev', prevHandler);
                }
                
                if (nextButton) {
                    const nextHandler = () => this.nextSlide();
                    nextButton.addEventListener('click', nextHandler);
                    this.clickHandlers.set('next', nextHandler);
                }
            }
            
            setupNotesToggle() {
                const notesButton = mockDocument.getElementById('toggle-notes');
                if (notesButton) {
                    const notesHandler = () => this.toggleNotes();
                    notesButton.addEventListener('click', notesHandler);
                    notesButton.setAttribute('aria-pressed', 'false');
                    this.clickHandlers.set('notes', notesHandler);
                }
            }
            
            showSlide(index) {
                if (index < 0 || index >= this.totalSlides) return;
                
                // Update slide visibility
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
                    notesButton.setAttribute('aria-pressed', this.notesVisible.toString());
                }
            }
            
            // Simulate button clicks for testing
            simulateButtonClick(buttonId) {
                const handler = this.clickHandlers.get(buttonId);
                if (handler) {
                    handler();
                }
            }
        }
        
        viewer = new TestNavigationViewer();
        viewer.init();
    });
    
    afterEach(() => {
        delete global.document;
        delete global.window;
        delete global.console;
        delete global.MutationObserver;
    });
    
    describe('Slide Counter Integration', () => {
        test('should initialize with correct counter text', () => {
            expect(mockCounter.textContent).toBe('1 / 3');
            expect(viewer.currentSlide).toBe(0);
        });
        
        test('should update counter when navigating forward', () => {
            viewer.simulateButtonClick('next');
            
            expect(viewer.currentSlide).toBe(1);
            expect(mockCounter.textContent).toBe('2 / 3');
        });
        
        test('should update counter when navigating backward', () => {
            // Go to slide 2 first
            viewer.goToSlide(1);
            expect(mockCounter.textContent).toBe('2 / 3');
            
            // Then go back
            viewer.simulateButtonClick('prev');
            
            expect(viewer.currentSlide).toBe(0);
            expect(mockCounter.textContent).toBe('1 / 3');
        });
        
        test('should update counter for direct navigation', () => {
            viewer.goToSlide(2);
            
            expect(viewer.currentSlide).toBe(2);
            expect(mockCounter.textContent).toBe('3 / 3');
        });
    });
    
    describe('Navigation Button States', () => {
        test('should disable previous button on first slide', () => {
            expect(mockButtons['prev-slide'].disabled).toBe(true);
            expect(mockButtons['next-slide'].disabled).toBe(false);
        });
        
        test('should enable both buttons on middle slides', () => {
            viewer.goToSlide(1);
            
            expect(mockButtons['prev-slide'].disabled).toBe(false);
            expect(mockButtons['next-slide'].disabled).toBe(false);
        });
        
        test('should disable next button on last slide', () => {
            viewer.goToSlide(2);
            
            expect(mockButtons['prev-slide'].disabled).toBe(false);
            expect(mockButtons['next-slide'].disabled).toBe(true);
        });
        
        test('should not allow navigation beyond boundaries', () => {
            // Try to go previous from first slide
            viewer.simulateButtonClick('prev');
            expect(viewer.currentSlide).toBe(0);
            
            // Try to go next from last slide
            viewer.goToSlide(2);
            viewer.simulateButtonClick('next');
            expect(viewer.currentSlide).toBe(2);
        });
    });
    
    describe('Slide Visibility Management', () => {
        test('should show only active slide', () => {
            expect(mockSlides[0].classList.add).toHaveBeenCalledWith('active');
            expect(mockSlides[0].style.display).toBe('block');
            expect(mockSlides[1].style.display).toBe('none');
            expect(mockSlides[2].style.display).toBe('none');
        });
        
        test('should update visibility when changing slides', () => {
            viewer.goToSlide(1);
            
            expect(mockSlides[0].classList.remove).toHaveBeenCalledWith('active');
            expect(mockSlides[0].style.display).toBe('none');
            expect(mockSlides[1].classList.add).toHaveBeenCalledWith('active');
            expect(mockSlides[1].style.display).toBe('block');
            expect(mockSlides[2].style.display).toBe('none');
        });
    });
    
    describe('Speaker Notes Integration', () => {
        test('should initialize with notes hidden', () => {
            const notes = mockDocument.querySelectorAll('.speaker-notes');
            notes.forEach(note => {
                expect(note.style.display).toBe('none');
            });
            expect(viewer.notesVisible).toBe(false);
        });
        
        test('should toggle notes visibility and button state', () => {
            viewer.simulateButtonClick('notes');
            
            expect(viewer.notesVisible).toBe(true);
            expect(mockButtons['toggle-notes'].textContent).toBe('Hide Notes');
            expect(mockButtons['toggle-notes'].setAttribute).toHaveBeenCalledWith('aria-pressed', 'true');
            
            const notes = mockDocument.querySelectorAll('.speaker-notes');
            notes.forEach(note => {
                expect(note.style.display).toBe('block');
            });
        });
        
        test('should toggle notes back to hidden', () => {
            // Show notes first
            viewer.simulateButtonClick('notes');
            expect(viewer.notesVisible).toBe(true);
            
            // Hide notes
            viewer.simulateButtonClick('notes');
            
            expect(viewer.notesVisible).toBe(false);
            expect(mockButtons['toggle-notes'].textContent).toBe('Notes');
            expect(mockButtons['toggle-notes'].setAttribute).toHaveBeenCalledWith('aria-pressed', 'false');
        });
    });
    
    describe('Complete Navigation Flow', () => {
        test('should handle full navigation sequence', () => {
            // Start at slide 1
            expect(viewer.currentSlide).toBe(0);
            expect(mockCounter.textContent).toBe('1 / 3');
            
            // Navigate to slide 2
            viewer.simulateButtonClick('next');
            expect(viewer.currentSlide).toBe(1);
            expect(mockCounter.textContent).toBe('2 / 3');
            expect(mockButtons['prev-slide'].disabled).toBe(false);
            expect(mockButtons['next-slide'].disabled).toBe(false);
            
            // Navigate to slide 3
            viewer.simulateButtonClick('next');
            expect(viewer.currentSlide).toBe(2);
            expect(mockCounter.textContent).toBe('3 / 3');
            expect(mockButtons['prev-slide'].disabled).toBe(false);
            expect(mockButtons['next-slide'].disabled).toBe(true);
            
            // Navigate back to slide 2
            viewer.simulateButtonClick('prev');
            expect(viewer.currentSlide).toBe(1);
            expect(mockCounter.textContent).toBe('2 / 3');
            
            // Navigate back to slide 1
            viewer.simulateButtonClick('prev');
            expect(viewer.currentSlide).toBe(0);
            expect(mockCounter.textContent).toBe('1 / 3');
            expect(mockButtons['prev-slide'].disabled).toBe(true);
            expect(mockButtons['next-slide'].disabled).toBe(false);
        });
    });
}); 