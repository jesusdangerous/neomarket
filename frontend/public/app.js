const state = {
  userId: localStorage.getItem('nm_user_id') || '11111111-1111-1111-1111-111111111111',
  moderatorToken: localStorage.getItem('nm_moderator_token') || '',
  products: [],
  categories: [],
  banners: [],
  collections: [],
  homeProducts: [],
  skuMap: JSON.parse(localStorage.getItem('nm_sku_map') || '{}'),
  currentModerationCard: null,
  blockingReasons: [],
};

const $ = (id) => document.getElementById(id);

function apiHeaders(extra = {}) {
  return {
    'Content-Type': 'application/json',
    'X-User-Id': state.userId,
    ...extra,
  };
}

function moderationHeaders(extra = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...extra,
  };
  if (state.moderatorToken) {
    headers.Authorization = `Bearer ${state.moderatorToken}`;
  } else {
    headers['X-Moderator-Id'] = 'ui.moderator';
    headers['X-Roles'] = 'MODERATOR';
  }
  return headers;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : null;
  if (!response.ok) {
    const message = data?.message || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return data;
}

function formatRub(amount) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(amount || 0);
}

function parseDeliveryAddress() {
  return {
    city: 'Екатеринбург',
    street: 'Ленина, 1',
    apartment: '42',
    comment: 'demo checkout from UI',
  };
}

function saveSkuMap() {
  localStorage.setItem('nm_sku_map', JSON.stringify(state.skuMap));
}

function setMessage(nodeId, text, isError = false) {
  const node = $(nodeId);
  if (!node) {
    return;
  }
  node.textContent = text;
  node.style.color = isError ? '#be123c' : '#5f6774';
}

function wireTabs() {
  document.querySelectorAll('.tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((item) => item.classList.remove('active'));
      document.querySelectorAll('.panel').forEach((panel) => panel.classList.remove('active'));
      tab.classList.add('active');
      $(tab.dataset.tab).classList.add('active');
    });
  });
}

async function loadCategories() {
  const data = await api('/api/catalog/api/v1/categories');
  const roots = data?.items || [];
  const flattened = [];

  function walk(items, prefix = '') {
    for (const item of items) {
      flattened.push({ id: item.id, name: prefix ? `${prefix} / ${item.name}` : item.name });
      if (item.children?.length) {
        walk(item.children, item.name);
      }
    }
  }

  walk(roots);
  state.categories = flattened;

  const select = $('categorySelect');
  select.innerHTML = '<option value="">Все категории</option>';
  for (const c of flattened) {
    const option = document.createElement('option');
    option.value = c.id;
    option.textContent = c.name;
    select.appendChild(option);
  }
}

async function loadProductSkus(productId) {
  const skus = await api(`/api/catalog/api/v1/products/${productId}/skus`);
  for (const sku of skus) {
    state.skuMap[sku.id] = {
      product_id: productId,
      sku_id: sku.id,
      title: sku.name,
      unit_price: sku.price,
    };
  }
  saveSkuMap();
  return skus;
}

function productCardNode(product, context = 'store') {
  const node = $('productTemplate').content.firstElementChild.cloneNode(true);
  node.querySelector('.product-title').textContent = product.title;
  node.querySelector('.product-price').textContent = formatRub(product.price);
  node.querySelector('.product-meta').textContent = product.in_stock ? 'В наличии' : 'Нет в наличии';

  const skuSelect = node.querySelector('.sku-select');
  skuSelect.innerHTML = '<option>Загрузка SKU...</option>';

  loadProductSkus(product.id)
    .then((skus) => {
      skuSelect.innerHTML = '';
      if (!skus.length) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'SKU отсутствуют';
        skuSelect.appendChild(opt);
        return;
      }
      for (const sku of skus) {
        const option = document.createElement('option');
        option.value = sku.id;
        option.textContent = `${sku.name} - ${formatRub(sku.price)}`;
        skuSelect.appendChild(option);
      }
    })
    .catch(() => {
      skuSelect.innerHTML = '<option>Не удалось загрузить SKU</option>';
    });

  node.querySelector('.add-cart-btn').addEventListener('click', async () => {
    const skuId = skuSelect.value;
    if (!skuId) {
      alert('SKU не выбран');
      return;
    }
    const skuData = state.skuMap[skuId];
    if (skuData) {
      skuData.product_title = product.title;
    }
    saveSkuMap();

    try {
      await api('/api/cart/api/v1/cart/items', {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({ sku_id: skuId, quantity: 1 }),
      });
      await Promise.all([loadCart(), loadFavorites()]);
    } catch (error) {
      alert(error.message);
    }
  });

  node.querySelector('.favorite-btn').addEventListener('click', async () => {
    try {
      await api(`/api/cart/api/v1/favorites/${product.id}`, {
        method: 'POST',
        headers: apiHeaders(),
      });
      await loadFavorites();
    } catch (error) {
      alert(error.message);
    }
  });

  const detailsBtn = node.querySelector('.details-btn');
  detailsBtn.textContent = context === 'home' ? 'В каталог' : 'Похожие';
  detailsBtn.addEventListener('click', async () => {
    if (context === 'home') {
      document.querySelector('[data-tab="store"]').click();
      return;
    }
    try {
      const similar = await api(`/api/catalog/api/v1/products/${product.id}/similar?limit=6&offset=0`);
      alert(`Похожих товаров: ${similar.total_count}`);
    } catch (error) {
      alert(error.message);
    }
  });

  return node;
}

async function loadProducts() {
  const params = new URLSearchParams();
  const search = $('searchInput').value.trim();
  const category = $('categorySelect').value;
  const sort = $('sortSelect').value;

  if (search) params.set('search', search);
  if (category) params.set('category_id', category);
  if (sort) params.set('sort', sort);

  const data = await api(`/api/catalog/api/v1/products?${params.toString()}`);
  state.products = data.items || [];
  $('productsMeta').textContent = `Всего товаров: ${data.total_count}`;

  const grid = $('productsGrid');
  grid.innerHTML = '';

  for (const product of state.products) {
    grid.appendChild(productCardNode(product, 'store'));
  }
}

async function loadBanners() {
  const data = await api('/api/cart/api/v1/home/banners');
  state.banners = data.items || [];
  const root = $('heroBanners');
  root.innerHTML = '';
  for (const banner of state.banners) {
    const item = document.createElement('article');
    item.className = 'banner-item';
    item.style.backgroundImage = `url('${banner.image}')`;
    item.innerHTML = `<div class="banner-copy"><strong>${banner.title}</strong><p>${banner.subtitle || ''}</p></div>`;
    root.appendChild(item);
  }
}

async function loadCollections() {
  const data = await api('/api/cart/api/v1/main/collections');
  state.collections = data.items || [];
  const grid = $('collectionsGrid');
  grid.innerHTML = '';

  for (const collection of state.collections) {
    const node = document.createElement('article');
    node.className = 'collection-card';
    node.innerHTML = `
      <h3>${collection.title}</h3>
      <p class="muted">${collection.description || ''}</p>
      <p class="muted">Товаров: ${collection.products_count || 0}</p>
      <button class="btn btn-ghost">Открыть подборку</button>
    `;
    node.querySelector('button').addEventListener('click', async () => {
      try {
        const payload = await api(`/api/cart/api/v1/collections/${collection.id}/products`);
        state.homeProducts = payload.items || [];
        renderHomeProducts();
      } catch (error) {
        alert(error.message);
      }
    });
    grid.appendChild(node);
  }
}

function renderHomeProducts() {
  const grid = $('homeProductsGrid');
  grid.innerHTML = '';
  for (const product of state.homeProducts) {
    grid.appendChild(productCardNode(product, 'home'));
  }
}

async function loadHomeProducts() {
  const data = await api('/api/cart/api/v1/cart/also_bought');
  state.homeProducts = data.items || [];
  renderHomeProducts();
}

async function loadCart() {
  const data = await api('/api/cart/api/v1/cart', {
    headers: apiHeaders(),
  });

  const cartItems = $('cartItems');
  cartItems.innerHTML = '';

  for (const item of data.items || []) {
    const skuData = state.skuMap[item.sku_id] || {};
    const row = document.createElement('div');
    row.className = 'cart-item';
    row.innerHTML = `
      <strong>${skuData.product_title || skuData.title || item.sku_id}</strong>
      <div class="muted">SKU: ${item.sku_id}</div>
      <div>Количество: ${item.quantity}</div>
      <button class="btn btn-ghost" data-id="${item.item_id}">Удалить</button>
    `;
    row.querySelector('button').addEventListener('click', async () => {
      await api(`/api/cart/api/v1/cart/items/${item.item_id}`, {
        method: 'DELETE',
        headers: apiHeaders(),
      });
      await loadCart();
    });
    cartItems.appendChild(row);
  }

  $('cartSummary').textContent = `Позиций: ${data.summary.total_items}, количество товаров: ${data.summary.total_quantity}`;
}

async function checkout() {
  try {
    const cart = await api('/api/cart/api/v1/cart', { headers: apiHeaders() });
    if (!cart.items?.length) {
      setMessage('checkoutMsg', 'Корзина пустая', true);
      return;
    }

    const orderItems = [];
    let total = 0;

    for (const item of cart.items) {
      const skuData = state.skuMap[item.sku_id];
      if (!skuData?.product_id) {
        setMessage('checkoutMsg', `Не хватает данных по SKU ${item.sku_id} для оформления`, true);
        return;
      }
      const lineTotal = (skuData.unit_price || 0) * item.quantity;
      total += lineTotal;
      orderItems.push({
        product_id: skuData.product_id,
        sku_id: item.sku_id,
        quantity: item.quantity,
        unit_price: { amount: skuData.unit_price || 0, currency: 'RUB' },
        line_total: { amount: lineTotal, currency: 'RUB' },
      });
    }

    const created = await api('/api/orders/api/v1/orders', {
      method: 'POST',
      headers: apiHeaders({ 'Idempotency-Key': crypto.randomUUID() }),
      body: JSON.stringify({
        items: orderItems,
        total: { amount: total, currency: 'RUB' },
        delivery_address: parseDeliveryAddress(),
        payment_method: 'CARD_ONLINE',
        comment: 'Order from NeoMarket Control Surface',
      }),
    });

    setMessage('checkoutMsg', `Заказ ${created.id} создан`);
    await loadCart();
  } catch (error) {
    setMessage('checkoutMsg', error.message, true);
  }
}

async function loadFavorites() {
  try {
    const data = await api('/api/cart/api/v1/favorites?limit=10&offset=0', { headers: apiHeaders() });
    const list = $('favoritesList');
    list.innerHTML = '';
    const items = data.items || [];
    if (!items.length) {
      list.innerHTML = '<p class="muted">Пока ничего не добавлено</p>';
      return;
    }

    for (const favorite of items) {
      const node = document.createElement('div');
      node.className = 'favorite-item';
      node.innerHTML = `
        <strong>${favorite.product_id}</strong>
        <div class="muted">Добавлено: ${new Date(favorite.added_at).toLocaleString('ru-RU')}</div>
        <button class="btn btn-ghost">Убрать</button>
      `;
      node.querySelector('button').addEventListener('click', async () => {
        await api(`/api/cart/api/v1/favorites/${favorite.product_id}`, {
          method: 'DELETE',
          headers: apiHeaders(),
        });
        await loadFavorites();
      });
      list.appendChild(node);
    }
  } catch (error) {
    $('favoritesList').innerHTML = `<p class="muted" style="color:#be123c">${error.message}</p>`;
  }
}

async function loadBlockingReasons() {
  const reasons = await api('/api/moderation/api/v1/product-blocking-reasons', {
    headers: moderationHeaders(),
  });
  state.blockingReasons = reasons || [];
  const select = $('declineReason');
  select.innerHTML = '';
  for (const reason of state.blockingReasons) {
    const option = document.createElement('option');
    option.value = reason.code;
    option.textContent = `${reason.title} (${reason.code})`;
    select.appendChild(option);
  }
}

function renderModerationCard(card) {
  const node = $('moderationCard');
  if (!card) {
    node.textContent = 'Очередь пуста';
    $('approveBtn').disabled = true;
    $('declineBtn').disabled = true;
    return;
  }

  node.innerHTML = `<pre>${JSON.stringify(card, null, 2)}</pre>`;
  $('approveBtn').disabled = false;
  $('declineBtn').disabled = false;
}

async function getNextCard() {
  try {
    const card = await api('/api/moderation/api/v1/product-moderation/get-next', {
      method: 'POST',
      headers: moderationHeaders(),
      body: JSON.stringify({}),
    });
    state.currentModerationCard = card;
    renderModerationCard(card);
    setMessage('moderationMsg', card ? 'Карточка получена' : 'Очередь пуста');
  } catch (error) {
    state.currentModerationCard = null;
    renderModerationCard(null);
    setMessage('moderationMsg', error.message, true);
  }
}

async function approveCurrent() {
  if (!state.currentModerationCard) {
    return;
  }
  try {
    const productId = state.currentModerationCard.product_id;
    const result = await api(`/api/moderation/api/v1/products/${productId}/approve`, {
      method: 'POST',
      headers: moderationHeaders(),
      body: JSON.stringify({}),
    });
    setMessage('moderationMsg', `Товар ${result.product_id} переведен в ${result.status}`);
    state.currentModerationCard = null;
    renderModerationCard(null);
  } catch (error) {
    setMessage('moderationMsg', error.message, true);
  }
}

async function declineCurrent() {
  if (!state.currentModerationCard) {
    return;
  }
  try {
    const productId = state.currentModerationCard.product_id;
    const payload = {
      reason_code: $('declineReason').value,
      comment: $('declineComment').value.trim(),
      fields: [],
    };
    const result = await api(`/api/moderation/api/v1/products/${productId}/decline`, {
      method: 'POST',
      headers: moderationHeaders(),
      body: JSON.stringify(payload),
    });
    setMessage('moderationMsg', `Товар ${result.product_id} переведен в ${result.status}`);
    state.currentModerationCard = null;
    renderModerationCard(null);
  } catch (error) {
    setMessage('moderationMsg', error.message, true);
  }
}

function bindEvents() {
  $('userIdInput').value = state.userId;
  $('moderatorTokenInput').value = state.moderatorToken;

  $('userIdInput').addEventListener('change', () => {
    state.userId = $('userIdInput').value.trim();
    localStorage.setItem('nm_user_id', state.userId);
    Promise.all([loadCart(), loadFavorites()]);
  });
  $('moderatorTokenInput').addEventListener('change', () => {
    state.moderatorToken = $('moderatorTokenInput').value.trim();
    localStorage.setItem('nm_moderator_token', state.moderatorToken);
  });
  $('refreshAll').addEventListener('click', () => {
    boot();
  });

  $('refreshProducts').addEventListener('click', loadProducts);
  $('reloadHomeProducts').addEventListener('click', loadHomeProducts);
  $('searchInput').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      loadProducts();
    }
  });
  $('clearCart').addEventListener('click', async () => {
    await api('/api/cart/api/v1/cart', { method: 'DELETE', headers: apiHeaders() });
    await loadCart();
  });
  $('checkoutBtn').addEventListener('click', checkout);

  $('getNextCard').addEventListener('click', getNextCard);
  $('approveBtn').addEventListener('click', approveCurrent);
  $('declineBtn').addEventListener('click', declineCurrent);
}

async function boot() {
  wireTabs();
  bindEvents();

  try {
    await Promise.all([
      loadCategories(),
      loadProducts(),
      loadCart(),
      loadFavorites(),
      loadBanners(),
      loadCollections(),
      loadHomeProducts(),
      loadBlockingReasons(),
    ]);
  } catch (error) {
    console.error(error);
    setMessage('checkoutMsg', `Ошибка загрузки: ${error.message}`, true);
  }
}

boot();
