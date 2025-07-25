/**
 * Jest setup file for enhanced slide viewer tests
 */

// Add polyfills for Node.js environment
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    warn: jest.fn(),
    error: jest.fn(),
    log: jest.fn()
};

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback) => {
    setTimeout(callback, 0);
};

// Mock cancelAnimationFrame
global.cancelAnimationFrame = (id) => {
    clearTimeout(id);
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
    constructor(callback) {
        this.callback = callback;
    }
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock scrollTo
global.scrollTo = jest.fn();

// Mock focus method
HTMLElement.prototype.focus = jest.fn();

// Mock getBoundingClientRect
HTMLElement.prototype.getBoundingClientRect = jest.fn(() => ({
    width: 800,
    height: 600,
    top: 0,
    left: 0,
    bottom: 600,
    right: 800,
    x: 0,
    y: 0,
}));

// Mock offsetWidth and offsetHeight
Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
    configurable: true,
    value: 800,
});

Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    value: 600,
});

Object.defineProperty(HTMLElement.prototype, 'scrollWidth', {
    configurable: true,
    value: 800,
});

Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
    configurable: true,
    value: 600,
});

// Mock video play/pause methods
HTMLVideoElement.prototype.play = jest.fn().mockResolvedValue(undefined);
HTMLVideoElement.prototype.pause = jest.fn();

// Mock audio play/pause methods
HTMLAudioElement.prototype.play = jest.fn().mockResolvedValue(undefined);
HTMLAudioElement.prototype.pause = jest.fn();

// Mock CustomEvent for JSDOM
global.CustomEvent = class CustomEvent extends Event {
    constructor(type, options = {}) {
        super(type, options);
        this.detail = options.detail;
    }
};