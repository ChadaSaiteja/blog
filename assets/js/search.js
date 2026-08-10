document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('search-clear-btn');
  const postsGrid = document.getElementById('blog-posts-grid');
  const noResults = document.getElementById('no-search-results');
  const filterContainer = document.getElementById('active-filters-container');
  const filterBadgeVal = document.getElementById('filter-badge-val');
  const clearFilterLink = document.getElementById('clear-filter-link');
  
  let searchIndex = [];
  let isIndexLoaded = false;

  async function loadSearchIndex() {
    if (isIndexLoaded) return;
    try {
      const response = await fetch('/search.json');
      if (!response.ok) throw new Error('Search index load failed');
      searchIndex = await response.json();
      isIndexLoaded = true;
    } catch (err) {
      console.error('Error loading search index:', err);
    }
  }

  function filterPosts() {
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const urlParams = new URLSearchParams(window.location.search);
    const categoryFilter = urlParams.get('category') ? urlParams.get('category').toLowerCase() : '';
    const tagFilter = urlParams.get('tag') ? urlParams.get('tag').toLowerCase() : '';

    if (filterContainer && filterBadgeVal) {
      if (categoryFilter || tagFilter) {
        filterContainer.style.display = 'flex';
        filterBadgeVal.textContent = categoryFilter ? `Category: ${categoryFilter}` : `Tag: #${tagFilter}`;
      } else {
        filterContainer.style.display = 'none';
      }
    }

    if (clearBtn) {
      clearBtn.style.display = query ? 'block' : 'none';
    }

    if (!postsGrid) return;
    const posts = postsGrid.querySelectorAll('.filterable-post');
    let visibleCount = 0;

    posts.forEach(post => {
      const title = post.getAttribute('data-title') || '';
      const desc = post.getAttribute('data-description') || '';
      const cats = post.getAttribute('data-categories') || '';
      const tags = post.getAttribute('data-tags') || '';

      let matchesFilter = true;
      if (categoryFilter && !cats.includes(categoryFilter)) matchesFilter = false;
      if (tagFilter && !tags.includes(tagFilter)) matchesFilter = false;

      let matchesQuery = true;
      if (query) {
        matchesQuery = title.includes(query) || 
                       desc.includes(query) || 
                       cats.includes(query) || 
                       tags.includes(query);
      }

      if (matchesFilter && matchesQuery) {
        post.style.display = 'block';
        visibleCount++;
      } else {
        post.style.display = 'none';
      }
    });

    if (noResults) {
      if (visibleCount === 0) {
        noResults.style.display = 'block';
        postsGrid.style.display = 'none';
      } else {
        noResults.style.display = 'none';
        postsGrid.style.display = 'flex';
      }
    }
  }

  if (searchInput) {
    searchInput.addEventListener('focus', loadSearchIndex);
    searchInput.addEventListener('input', () => {
      loadSearchIndex().then(filterPosts);
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.style.display = 'none';
        filterPosts();
        searchInput.focus();
      });
    }
  }

  if (clearFilterLink) {
    clearFilterLink.addEventListener('click', (e) => {
      e.preventDefault();
      const url = new URL(window.location);
      url.searchParams.delete('category');
      url.searchParams.delete('tag');
      window.history.pushState({}, '', url);
      filterPosts();
    });
  }

  filterPosts();
});
