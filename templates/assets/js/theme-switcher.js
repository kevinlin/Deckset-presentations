/**
 * Theme switcher: populates a <select> from an inline JSON manifest,
 * swaps the theme <link> href, and persists the choice in localStorage.
 */
document.addEventListener('DOMContentLoaded', function () {
    var manifestEl = document.getElementById('theme-manifest');
    if (!manifestEl) return;

    var manifest;
    try {
        manifest = JSON.parse(manifestEl.textContent);
    } catch (e) {
        return;
    }
    if (!Array.isArray(manifest) || manifest.length === 0) return;

    var select = document.getElementById('theme-select');
    var link = document.getElementById('theme-css');
    if (!select || !link) return;

    var defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = 'Page default';
    select.appendChild(defaultOpt);

    for (var i = 0; i < manifest.length; i++) {
        var opt = document.createElement('option');
        opt.value = manifest[i].slug;
        opt.textContent = manifest[i].name;
        select.appendChild(opt);
    }

    var stored = localStorage.getItem('deckset-site-theme');
    if (stored) {
        var found = manifest.some(function (t) { return t.slug === stored; });
        if (found) {
            _swapHref(link, stored);
            select.value = stored;
        }
    }

    select.addEventListener('change', function () {
        var val = select.value;
        _withHouseLights(function () {
            if (val === '') {
                localStorage.removeItem('deckset-site-theme');
                link.href = link.dataset.defaultHref;
            } else {
                localStorage.setItem('deckset-site-theme', val);
                _swapHref(link, val);
            }
        });
    });

    function _swapHref(linkEl, slug) {
        var base = linkEl.dataset.defaultHref;
        linkEl.href = base.replace(/[^/]+\.css$/, slug + '.css');
    }

    // Cross-fade surfaces while the theme stylesheet swaps, like house
    // lights coming up between shows. The class arms a transition on every
    // color property; it is removed once the new sheet has settled.
    function _withHouseLights(applyFn) {
        var reduce = window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduce) {
            applyFn();
            return;
        }

        var root = document.documentElement;
        root.classList.add('theme-fading');
        applyFn();

        var clear = function () {
            setTimeout(function () { root.classList.remove('theme-fading'); }, 400);
        };
        link.addEventListener('load', clear, { once: true });
        setTimeout(clear, 1000);
    }
});
