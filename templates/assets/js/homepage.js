document.addEventListener('DOMContentLoaded', function () {
    var searchInput = document.getElementById('search-input');
    var presentationCards = document.querySelectorAll('.presentation-card');
    var presentationsGrid = document.getElementById('presentations-grid');
    var noResults = document.getElementById('no-results');
    var noResultsTitle = noResults ? noResults.querySelector('.hp-state-title') : null;

    // Booth signature for whoever opens the projection window
    try {
        var deckCount = presentationCards.length;
        var accent = getComputedStyle(document.documentElement)
            .getPropertyValue('--color-accent').trim() || '#3b82f6';
        console.log(
            '%cThe Projection Booth%c\n' +
            deckCount + ' deck' + (deckCount === 1 ? '' : 's') +
            ', written in Deckset Markdown, staged by the site’s own generator.\n' +
            'View the machinery: https://github.com/kevinlin/Deckset-presentations',
            'color:' + accent + ';font-weight:600;font-size:13px;font-family:Menlo,Monaco,monospace;',
            'font-size:12px;font-family:Menlo,Monaco,monospace;'
        );
    } catch (e) {
        // Console styling is best-effort
    }

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        var rawTerm = this.value.trim();
        var searchTerm = rawTerm.toLowerCase();
        var matchCount = 0;

        presentationCards.forEach(function (card) {
            var title = card.querySelector('.presentation-title');
            if (title && title.textContent.toLowerCase().includes(searchTerm)) {
                card.classList.remove('hidden');
                matchCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        if (matchCount === 0 && searchTerm !== '') {
            if (noResultsTitle) {
                noResultsTitle.textContent = 'Nothing matches “' + rawTerm + '”';
            }
            if (presentationsGrid) presentationsGrid.classList.add('hidden');
            if (noResults) noResults.classList.remove('hidden');
        } else {
            if (presentationsGrid) presentationsGrid.classList.remove('hidden');
            if (noResults) noResults.classList.add('hidden');
        }
    });
});
