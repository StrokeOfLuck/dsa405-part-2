(() => {
  const state = document.getElementById('review-state');
  const search = document.getElementById('review-search');
  if (!state || !search) return;
  function filter() {
    const query = search.value.trim().toLowerCase();
    let count = 0;
    document.querySelectorAll('.review-item').forEach(item => {
      const status = item.dataset.reviewState;
      const matches = state.value === 'all' || (state.value === 'reviewed' ? status !== 'unreviewed' : status === 'unreviewed');
      item.hidden = !matches || !item.textContent.toLowerCase().includes(query);
      if (!item.hidden) count++;
    });
    document.getElementById('review-count').textContent = `${count} rows shown`;
  }
  state.addEventListener('change', filter);
  search.addEventListener('input', filter);
  filter();
})();
