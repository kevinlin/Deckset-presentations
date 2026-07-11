document.addEventListener('DOMContentLoaded', function () {
    var searchInput = document.getElementById('search-input');
    var presentationCards = document.querySelectorAll('.presentation-card');
    var presentationsGrid = document.getElementById('presentations-grid');
    var noResults = document.getElementById('no-results');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        var searchTerm = this.value.toLowerCase().trim();
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
            if (presentationsGrid) presentationsGrid.classList.add('hidden');
            if (noResults) noResults.classList.remove('hidden');
        } else {
            if (presentationsGrid) presentationsGrid.classList.remove('hidden');
            if (noResults) noResults.classList.add('hidden');
        }
    });
});
