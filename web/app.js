const fmt = new Intl.NumberFormat('ar-EG', { style: 'currency', currency: 'EGP' });
const els = {
  grid: document.getElementById('grid'),
  count: document.getElementById('count'),
  search: document.getElementById('search'),
  brand: document.getElementById('brand'),
  minPrice: document.getElementById('minPrice'),
  maxPrice: document.getElementById('maxPrice'),
  clear: document.getElementById('clear'),
};

let all = [];
let filtered = [];

async function load() {
  const res = await fetch('data/products.json?_=' + Date.now());
  all = await res.json();
  const brands = [...new Set(all.map(p => p.brand).filter(Boolean))].sort();
  els.brand.innerHTML = '<option value="">All brands</option>' + brands.map(b => `<option>${b}</option>`).join('');
  applyFilters();
}

function applyFilters() {
  const q = (els.search.value || '').toLowerCase();
  const b = els.brand.value || '';
  const min = parseFloat(els.minPrice.value);
  const max = parseFloat(els.maxPrice.value);

  filtered = all.filter(p => {
    const matchesQ = !q || p.name.toLowerCase().includes(q);
    const matchesB = !b || p.brand === b;
    const price = p.price_egp || 0;
    const matchesMin = isNaN(min) || price >= min;
    const matchesMax = isNaN(max) || price <= max;
    return matchesQ && matchesB && matchesMin && matchesMax;
  });

  render();
}

function render() {
  els.count.textContent = `${filtered.length} products`;
  els.grid.innerHTML = filtered.map(p => `
    <article class="card">
      <img src="${p.image_url || ''}" alt="${p.name}" loading="lazy"/>
      <div class="body">
        <h3>${p.name}</h3>
        <div class="price">${fmt.format(p.price_egp || 0)}</div>
        <div class="meta">${p.brand || ''} • ${p.category || ''} • <span>${p.source || ''}</span></div>
        <a class="btn" href="${p.url}" target="_blank" rel="noopener">View</a>
      </div>
    </article>
  `).join('');
}

['input','change'].forEach(ev => {
  els.search.addEventListener(ev, applyFilters);
  els.brand.addEventListener(ev, applyFilters);
  els.minPrice.addEventListener(ev, applyFilters);
  els.maxPrice.addEventListener(ev, applyFilters);
});
els.clear.addEventListener('click', () => {
  els.search.value = '';
  els.brand.value = '';
  els.minPrice.value = '';
  els.maxPrice.value = '';
  applyFilters();
});

load();
