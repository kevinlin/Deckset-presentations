/**
 * Enhanced Slide Viewer JavaScript
 * Provides navigation, keyboard shortcuts, and enhanced features for Deckset presentations
 */

class EnhancedSlideViewer {
    constructor() {
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.totalSlides = this.slides.length;
        this.notesVisible = false;
        
        this.init();
    }
    
    init() {
        // Mark presentation container as JS-enabled
        const container = document.querySelector('.presentation-container');
        if (container) {
            container.classList.add('js-enabled');
        }
        
        this.setupNavigation();
        this.setupKeyboardShortcuts();
        this.setupSlideCounter();
        this.setupNotesToggle();
        this.setupAutoplay();
        this.setupResponsiveFeatures();
        this.initializeHighlighting();
        this.initializeMathJax();
        this.setupFitText();
        
        // Show first slide
        this.showSlide(0);
        
        console.log(`Enhanced Slide Viewer initialized with ${this.totalSlides} slides`);
    }
    
    setupNavigation() {
        const prevButton = document.getElementById('prev-slide');
        const nextButton = document.getElementById('next-slide');
        
        if (prevButton) {
            prevButton.addEventListener('click', () => this.previousSlide());
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => this.nextSlide());
        }
        
        // Touch/swipe support
        let startX = 0;
        let startY = 0;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Only handle horizontal swipes
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0) {
                    this.nextSlide();
                } else {
                    this.previousSlide();
                }
            }
            
            startX = 0;
            startY = 0;
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
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
                    
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                    
                case 'Escape':
                    if (document.fullscreenElement) {
                        document.exitFullscreen();
                    }
                    break;
                    
                default:
                    // Handle number keys for direct slide navigation
                    if (e.key >= '1' && e.key <= '9') {
                        const slideNumber = parseInt(e.key) - 1;
                        if (slideNumber < this.totalSlides) {
                            this.goToSlide(slideNumber);
                        }
                    }
                    break;
            }
        });
    }
    
    setupSlideCounter() {
        const counter = document.getElementById('slide-counter');
        if (counter) {
            this.updateSlideCounter();
        }
    }
    
    setupNotesToggle() {
        const notesButton = document.getElementById('toggle-notes');
        if (notesButton) {
            notesButton.addEventListener('click', () => this.toggleNotes());
            // Set initial aria-pressed state
            notesButton.setAttribute('aria-pressed', 'false');
        }
        
        // Ensure notes are hidden initially
        const notes = document.querySelectorAll('.speaker-notes');
        notes.forEach(note => {
            note.style.display = 'none';
        });
    }
    
    setupAutoplay() {
        // Check for autoplay parameter in URL
        const urlParams = new URLSearchParams(window.location.search);
        const autoplay = urlParams.get('autoplay');
        
        if (autoplay) {
            const interval = parseInt(autoplay) || 5000; // Default 5 seconds
            this.startAutoplay(interval);
        }
    }
    
    setupResponsiveFeatures() {
        // Handle window resize for responsive adjustments
        window.addEventListener('resize', () => {
            this.adjustForViewport();
        });
        
        // Initial adjustment
        this.adjustForViewport();
    }
    
    setupFitText() {
        // Scale all fit text elements initially
        this.scaleAllFitText();
        
        // Re-scale on window resize
        window.addEventListener('resize', () => {
            this.scaleAllFitText();
        });
        
        // Re-scale when slides change (in case of dynamic content)
        const observer = new MutationObserver(() => {
            this.scaleAllFitText();
        });
        
        // Observe changes to slide content
        this.slides.forEach(slide => {
            observer.observe(slide, { childList: true, subtree: true });
        });
    }
    
    scaleAllFitText() {
        const fitElements = document.querySelectorAll('.fit');
        fitElements.forEach(element => {
            this.scaleFitText(element);
        });
    }
    
    scaleFitText(element) {
        if (!element || !element.parentElement) {
            console.warn('scaleFitText: Invalid element or missing parent');
            return;
        }
        
        const container = element.parentElement;
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        
        if (containerWidth <= 0) {
            console.warn('scaleFitText: Container width is 0 or negative');
            return;
        }
        
        console.log(`Scaling fit text: "${element.textContent.substring(0, 20)}..." in container ${containerWidth}px wide`);
        
        // Start with a large font size and scale down until it fits
        let fontSize = Math.min(containerWidth / 8, 120); // Start with reasonable max
        element.style.fontSize = fontSize + 'px';
        
        // Binary search for optimal font size
        let minSize = 12;
        let maxSize = Math.min(containerWidth / 2, 200);
        let iterations = 0;
        const maxIterations = 20;
        
        while (minSize < maxSize && iterations < maxIterations) {
            fontSize = Math.floor((minSize + maxSize) / 2);
            element.style.fontSize = fontSize + 'px';
            
            // Check if text fits horizontally
            if (element.scrollWidth <= containerWidth * 0.95) { // 5% margin
                minSize = fontSize + 1;
            } else {
                maxSize = fontSize - 1;
            }
            
            iterations++;
        }
        
        // Use the largest size that fits
        fontSize = maxSize;
        element.style.fontSize = fontSize + 'px';
        
        // Ensure minimum readability
        if (fontSize < 16) {
            fontSize = 16;
            element.style.fontSize = fontSize + 'px';
        }
        
        console.log(`Final font size: ${fontSize}px after ${iterations} iterations`);
        return fontSize;
    }
    
    initializeHighlighting() {
        // Initialize syntax highlighting if highlight.js is available
        if (typeof hljs !== 'undefined') {
            hljs.highlightAll();
            console.log('Syntax highlighting initialized');
        }
    }
    
    initializeMathJax() {
        // Initialize MathJax if available
        if (typeof MathJax !== 'undefined') {
            MathJax.typesetPromise().then(() => {
                console.log('MathJax rendering completed');
            }).catch((err) => {
                console.error('MathJax rendering failed:', err);
            });
        }
    }
    
    showSlide(index) {
        if (index < 0 || index >= this.totalSlides) return;
        
        // Hide all slides using CSS classes
        this.slides.forEach((slide, i) => {
            if (i === index) {
                slide.classList.add('active');
                slide.style.display = 'block'; // Fallback for older browsers
            } else {
                slide.classList.remove('active');
                slide.style.display = 'none'; // Fallback for older browsers
            }
        });
        
        this.currentSlide = index;
        this.updateSlideCounter();
        this.updateNavigationButtons();
        
        // Trigger any slide-specific animations or media
        this.activateSlideMedia(index);
        
        // Update URL hash for bookmarking
        window.location.hash = `slide-${index + 1}`;
        
        // Announce slide change for screen readers
        this.announceSlideChange();
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
        const counter = document.getElementById('slide-counter');
        if (counter) {
            counter.textContent = `${this.currentSlide + 1} / ${this.totalSlides}`;
        }
    }
    
    updateNavigationButtons() {
        const prevButton = document.getElementById('prev-slide');
        const nextButton = document.getElementById('next-slide');
        
        if (prevButton) {
            prevButton.disabled = this.currentSlide === 0;
        }
        
        if (nextButton) {
            nextButton.disabled = this.currentSlide === this.totalSlides - 1;
        }
    }
    
    toggleNotes() {
        this.notesVisible = !this.notesVisible;
        const notes = document.querySelectorAll('.speaker-notes');
        
        notes.forEach(note => {
            note.style.display = this.notesVisible ? 'block' : 'none';
        });
        
        const notesButton = document.getElementById('toggle-notes');
        if (notesButton) {
            notesButton.textContent = this.notesVisible ? 'Hide Notes' : 'Notes';
            notesButton.setAttribute('aria-pressed', this.notesVisible);
        }
        
        console.log(`Notes toggled: ${this.notesVisible ? 'shown' : 'hidden'} (${notes.length} note elements found)`);
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
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
        
        console.log(`Autoplay started with ${interval}ms interval`);
    }
    
    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
            console.log('Autoplay stopped');
        }
    }
    
    adjustForViewport() {
        const slides = document.querySelectorAll('.slide');
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        slides.forEach(slide => {
            const content = slide.querySelector('.slide-content');
            if (!content) return;
            
            // Apply autoscale if content is too large
            const autoscaleElement = content.querySelector('.autoscale-content');
            if (autoscaleElement) {
                this.applyAutoscale(autoscaleElement, viewport);
            }
            
            // Adjust math formulas for mobile
            if (viewport.width < 768) {
                this.adjustMathForMobile(slide);
            }
        });
    }
    
    applyAutoscale(element, viewport) {
        const rect = element.getBoundingClientRect();
        const scaleX = (viewport.width * 0.9) / rect.width;
        const scaleY = (viewport.height * 0.8) / rect.height;
        const scale = Math.min(scaleX, scaleY, 1);
        
        if (scale < 1) {
            element.style.transform = `scale(${scale})`;
        } else {
            element.style.transform = 'none';
        }
    }
    
    adjustMathForMobile(slide) {
        const mathElements = slide.querySelectorAll('.MathJax');
        mathElements.forEach(math => {
            if (math.scrollWidth > slide.clientWidth * 0.9) {
                math.style.fontSize = '0.8em';
                math.style.overflowX = 'auto';
            }
        });
    }
    
    activateSlideMedia(index) {
        const slide = this.slides[index];
        if (!slide) return;
        
        // Handle video autoplay
        const videos = slide.querySelectorAll('video[data-autoplay="true"]');
        videos.forEach(video => {
            video.currentTime = 0;
            video.play().catch(err => {
                console.warn('Video autoplay failed:', err);
            });
        });
        
        // Handle audio autoplay
        const audios = slide.querySelectorAll('audio[data-autoplay="true"]');
        audios.forEach(audio => {
            audio.currentTime = 0;
            audio.play().catch(err => {
                console.warn('Audio autoplay failed:', err);
            });
        });
        
        // Pause media from other slides
        this.pauseOtherSlideMedia(index);
    }
    
    pauseOtherSlideMedia(currentIndex) {
        this.slides.forEach((slide, index) => {
            if (index !== currentIndex) {
                const videos = slide.querySelectorAll('video');
                const audios = slide.querySelectorAll('audio');
                
                videos.forEach(video => video.pause());
                audios.forEach(audio => audio.pause());
            }
        });
    }
    
    announceSlideChange() {
        // Create or update live region for screen readers
        let liveRegion = document.getElementById('slide-announcer');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'slide-announcer';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.position = 'absolute';
            liveRegion.style.left = '-10000px';
            liveRegion.style.width = '1px';
            liveRegion.style.height = '1px';
            liveRegion.style.overflow = 'hidden';
            document.body.appendChild(liveRegion);
        }
        
        const slideTitle = this.slides[this.currentSlide].querySelector('h1, h2, h3, h4, h5, h6');
        const title = slideTitle ? slideTitle.textContent : `Slide ${this.currentSlide + 1}`;
        
        liveRegion.textContent = `${title}, slide ${this.currentSlide + 1} of ${this.totalSlides}`;
    }
    
    // Initialize from URL hash
    initializeFromHash() {
        const hash = window.location.hash;
        if (hash.startsWith('#slide-')) {
            const slideNumber = parseInt(hash.replace('#slide-', '')) - 1;
            if (slideNumber >= 0 && slideNumber < this.totalSlides) {
                this.showSlide(slideNumber);
                return;
            }
        }
        
        // Default to first slide
        this.showSlide(0);
    }
}

// Utility functions for enhanced features
class SlideUtils {
    static createProgressBar() {
        const progressBar = document.createElement('div');
        progressBar.id = 'slide-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: #3b82f6;
            transition: width 0.3s ease;
            z-index: 1000;
        `;
        document.body.appendChild(progressBar);
        return progressBar;
    }
    
    static updateProgress(current, total) {
        const progressBar = document.getElementById('slide-progress');
        if (progressBar) {
            const percentage = ((current + 1) / total) * 100;
            progressBar.style.width = `${percentage}%`;
        }
    }
    
    static addSlideNumbers() {
        const slides = document.querySelectorAll('.slide');
        slides.forEach((slide, index) => {
            if (!slide.querySelector('.slide-number')) {
                const slideNumber = document.createElement('div');
                slideNumber.className = 'slide-number';
                slideNumber.textContent = index + 1;
                slide.appendChild(slideNumber);
            }
        });
    }
    
    static enablePrintMode() {
        // Show all slides for printing
        const slides = document.querySelectorAll('.slide');
        slides.forEach(slide => {
            slide.style.display = 'block';
            slide.style.pageBreakAfter = 'always';
        });
        
        // Hide navigation
        const navigation = document.querySelector('.navigation');
        if (navigation) {
            navigation.style.display = 'none';
        }
        
        // Show all speaker notes
        const notes = document.querySelectorAll('.speaker-notes');
        notes.forEach(note => {
            note.style.display = 'block';
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're in a presentation view
    if (document.querySelector('.presentation-container')) {
        const viewer = new EnhancedSlideViewer();
        
        // Add progress bar
        SlideUtils.createProgressBar();
        
        // Update progress on slide change
        const originalShowSlide = viewer.showSlide.bind(viewer);
        viewer.showSlide = function(index) {
            originalShowSlide(index);
            SlideUtils.updateProgress(index, this.totalSlides);
        };
        
        // Initialize from URL hash
        viewer.initializeFromHash();
        
        // Handle print mode
        window.addEventListener('beforeprint', SlideUtils.enablePrintMode);
        
        // Expose viewer globally for debugging
        window.slideViewer = viewer;
    }
    
    // Initialize homepage search if present
    if (document.getElementById('search-input')) {
        initializeHomepageSearch();
    }
});

function initializeHomepageSearch() {
    const searchInput = document.getElementById('search-input');
    const presentationCards = document.querySelectorAll('.presentation-card');
    const presentationsGrid = document.getElementById('presentations-grid');
    const noResults = document.getElementById('no-results');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        let matchCount = 0;
        
        presentationCards.forEach(card => {
            const title = card.querySelector('.presentation-title');
            if (title && title.textContent.toLowerCase().includes(searchTerm)) {
                card.classList.remove('hidden');
                matchCount++;
            } else {
                card.classList.add('hidden');
            }
        });
        
        // Show/hide no results message
        if (matchCount === 0 && searchTerm !== '') {
            if (presentationsGrid) presentationsGrid.classList.add('hidden');
            if (noResults) noResults.classList.remove('hidden');
        } else {
            if (presentationsGrid) presentationsGrid.classList.remove('hidden');
            if (noResults) noResults.classList.add('hidden');
        }
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EnhancedSlideViewer, SlideUtils };
}