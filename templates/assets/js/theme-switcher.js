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
        if (val === '') {
            localStorage.removeItem('deckset-site-theme');
            link.href = link.dataset.defaultHref;
        } else {
            localStorage.setItem('deckset-site-theme', val);
            _swapHref(link, val);
        }
    });

    function _swapHref(linkEl, slug) {
        var base = linkEl.dataset.defaultHref;
        linkEl.href = base.replace(/[^/]+\.css$/, slug + '.css');
    }
});
