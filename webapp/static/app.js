const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#0a0d13"); } catch (e) {}
  try { tg.setBackgroundColor("#0a0d13"); } catch (e) {}
}

const initData = tg?.initData || "";
const tgUser = tg?.initDataUnsafe?.user || null;

const STATUS_LABELS = {
  new: "Ожидает оплаты",
  awaiting_review: "Проверяется админом",
  approved: "Оплата подтверждена",
  rejected: "Отклонён",
  completed: "Выполнен",
  cancelled: "Отменён",
};

/* ---------- Icon set (stroke, 24x24, currentColor) ---------- */
const ICONS = {
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v9a1 1 0 0 0 1 1h4v-6h2v6h4a1 1 0 0 0 1-1v-9"/></svg>',
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>',
  package: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8.5 12 3 3 8.5l9 5.5 9-5.5Z"/><path d="M3 8.5V16l9 5.5 9-5.5V8.5"/><path d="M12 14v7.5"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.6"/><path d="M4.5 20c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5"/></svg>',
  star: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 3.3 14.6 9l6.2.6-4.7 4.1 1.4 6.1L12 16.9 6.5 19.8l1.4-6.1L3.2 9.6 9.4 9 12 3.3Z"/></svg>',
  gem: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12l3 5-9 13L3 8l3-5Z"/><path d="M3 8h18"/><path d="M9 3 12 21 15 3"/></svg>',
  gamepad: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="7.5" width="19" height="10" rx="4"/><path d="M7.5 10.5v4M5.5 12.5h4"/><circle cx="15.5" cy="11" r="0.9" fill="currentColor" stroke="none"/><circle cx="18" cy="13.5" r="0.9" fill="currentColor" stroke="none"/></svg>',
  gift: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="9" width="17" height="11" rx="1.5"/><path d="M3.5 13h17"/><path d="M12 9v11"/><path d="M12 9c-1.2-3-3-4-4.3-3.1C6.4 6.7 7 9 12 9Z"/><path d="M12 9c1.2-3 3-4 4.3-3.1C17.6 6.7 17 9 12 9Z"/></svg>',
  chevronLeft: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5 8 12l7 7"/></svg>',
  chevronRight: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>',
  paperclip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 7.5 8.5 16a3 3 0 1 0 4.2 4.2L21 12"/><path d="M13.3 3.8a4 4 0 0 1 5.7 5.7L10.4 18a1.7 1.7 0 1 1-2.4-2.4l8-8"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5 9.5 18 20 6"/></svg>',
  refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v5h5"/><path d="M20 20v-5h-5"/><path d="M5 10a7 7 0 0 1 12-4.2L20 8"/><path d="M19 14a7 7 0 0 1-12 4.2L4 16"/></svg>',
  support: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13v-1a8 8 0 0 1 16 0v1"/><rect x="2.5" y="13" width="5" height="6" rx="1.5"/><rect x="16.5" y="13" width="5" height="6" rx="1.5"/><path d="M20 19v1a3 3 0 0 1-3 3h-3"/></svg>',
  boxEmpty: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8.5 12 3 3 8.5l9 5.5 9-5.5Z"/><path d="M3 8.5V16l9 5.5 9-5.5V8.5"/></svg>',
};

const CATEGORY_ICON = { stars: "star", premium: "gem", game: "gamepad" };

function icon(name) {
  return ICONS[name] || "";
}

let catalog = [];
let activeCategoryId = null;
let selectedProduct = null;
let currency = "UZS";
let receiptFile = null;
let currentOrderId = null;

function formatMoney(value) {
  return Math.round(value).toLocaleString("ru-RU") + " " + currency;
}

function alertMsg(text) {
  if (tg?.showAlert) tg.showAlert(text);
  else alert(text);
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  headers["X-Telegram-Init-Data"] = initData;
  const resp = await fetch(path, { ...options, headers });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `Ошибка ${resp.status}`);
  }
  return resp.json();
}

/* ---------- Static chrome (nav, icons, labels) ---------- */
function setupChrome() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    const name = btn.dataset.icon;
    const label = btn.textContent.trim();
    btn.innerHTML = `${icon(name)}<span>${label}</span>`;
  });

  document.querySelectorAll(".back-link").forEach((btn) => {
    btn.innerHTML = `${icon("chevronLeft")}<span>${btn.dataset.label || "Назад"}</span>`;
  });

  document.getElementById("btn-refresh").innerHTML = icon("refresh");
  document.getElementById("done-icon").innerHTML = icon("check");
  document.getElementById("upload-box-icon").innerHTML = icon("paperclip");
  document.getElementById("profile-orders-icon").innerHTML = icon("package");
  document.getElementById("profile-support-icon").innerHTML = icon("support");
  document.getElementById("profile-chevron-1").innerHTML = icon("chevronRight");
  document.getElementById("profile-chevron-2").innerHTML = icon("chevronRight");
}

function setupUserUI() {
  const initials = (tgUser?.first_name || "?").charAt(0).toUpperCase();
  const name = [tgUser?.first_name, tgUser?.last_name].filter(Boolean).join(" ") || "Гость";
  const username = tgUser?.username ? "@" + tgUser.username : "";

  document.getElementById("topbar-name").textContent = name;
  document.getElementById("profile-name").textContent = name;
  document.getElementById("profile-username").textContent = username;

  [document.getElementById("topbar-avatar"), document.getElementById("profile-avatar")].forEach((el) => {
    if (tgUser?.photo_url) {
      el.innerHTML = `<img src="${tgUser.photo_url}" alt="">`;
    } else {
      el.textContent = initials;
    }
  });
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));
  document.getElementById("screen-" + id).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.nav === id);
  });
  if (id === "orders") loadOrders();
}

/* ---------- Catalog rendering ---------- */
function renderHome() {
  const catGrid = document.getElementById("home-categories");
  catGrid.innerHTML = "";
  catalog.forEach((cat) => {
    const tile = document.createElement("div");
    tile.className = "cat-tile";
    tile.innerHTML = `<div class="cat-icon">${icon(CATEGORY_ICON[cat.type] || "grid")}</div><div class="label">${cat.title}</div>`;
    tile.onclick = () => {
      activeCategoryId = cat.id;
      showScreen("catalog");
      renderTabs();
      renderProducts();
    };
    catGrid.appendChild(tile);
  });

  const popular = document.getElementById("home-popular");
  popular.innerHTML = "";
  const popularTiles = catalog.flatMap((c) => productTiles(c.products[0] ? [c.products[0]] : [])).slice(0, 4);
  popularTiles.forEach((tile) => popular.appendChild(tile));
}

const QTY_PRESETS = [100, 300, 500, 750, 1000];

function mediaHtml(product) {
  if (product.image_url) {
    return `<img src="${product.image_url}" alt="">`;
  }
  return icon(CATEGORY_ICON[product._categoryType] || "gift");
}

function productTile(product, presetQty) {
  const tile = document.createElement("div");
  tile.className = "product-tile";

  let title = product.title;
  let priceLabel;
  if (product.is_variable && presetQty) {
    title = `${presetQty} ${product.title}`;
    priceLabel = formatMoney(product.unit_price * presetQty);
  } else if (product.is_variable) {
    priceLabel = `от ${formatMoney(product.unit_price * product.min_quantity)}`;
  } else {
    priceLabel = formatMoney(product.price);
  }

  tile.innerHTML = `
    <div class="media">${mediaHtml(product)}</div>
    <div class="title">${title}</div>
    <div class="price">${priceLabel}</div>
  `;
  tile.onclick = () => openOrderScreen(product, presetQty);
  return tile;
}

function productTiles(products) {
  const tiles = [];
  products.forEach((product) => {
    if (product.is_variable) {
      const values = [...new Set([product.min_quantity, ...QTY_PRESETS.filter((v) => v >= product.min_quantity)])];
      values.forEach((qty) => tiles.push(productTile(product, qty)));
    } else {
      tiles.push(productTile(product));
    }
  });
  return tiles;
}

function renderTabs() {
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  catalog.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "tab" + (cat.id === activeCategoryId ? " active" : "");
    btn.innerHTML = `${icon(CATEGORY_ICON[cat.type] || "grid")}<span>${cat.title}</span>`;
    btn.onclick = () => {
      activeCategoryId = cat.id;
      renderTabs();
      renderProducts();
    };
    tabs.appendChild(btn);
  });
}

function renderProducts() {
  const container = document.getElementById("products");
  container.innerHTML = "";
  const category = catalog.find((c) => c.id === activeCategoryId);
  if (!category) return;
  const products = category.products.map((p) => ({ ...p, _categoryType: category.type }));
  productTiles(products).forEach((tile) => container.appendChild(tile));
}

/* ---------- Order flow ---------- */
function updateOrderPrice() {
  if (!selectedProduct) return;
  if (selectedProduct.is_variable) {
    const qtyInput = document.getElementById("order-quantity-input");
    const qty = parseInt(qtyInput.value, 10) || 0;
    document.getElementById("order-price").textContent = formatMoney(selectedProduct.unit_price * qty);
    document.querySelectorAll(".qty-chip").forEach((chip) => {
      chip.classList.toggle("active", parseInt(chip.dataset.qty, 10) === qty);
    });
  } else {
    document.getElementById("order-price").textContent = formatMoney(selectedProduct.price);
  }
}

function renderQtyPresets(product) {
  const box = document.getElementById("qty-presets");
  box.innerHTML = "";
  const values = [product.min_quantity, ...QTY_PRESETS.filter((v) => v >= product.min_quantity)];
  [...new Set(values)].forEach((value) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "qty-chip";
    chip.dataset.qty = value;
    chip.textContent = value;
    chip.onclick = () => {
      document.getElementById("order-quantity-input").value = value;
      updateOrderPrice();
    };
    box.appendChild(chip);
  });
}

function openOrderScreen(product, presetQty) {
  selectedProduct = product;
  document.getElementById("order-title").textContent = product.title;

  const qtyField = document.getElementById("order-quantity-field");
  const qtyLabel = document.getElementById("order-quantity-label");
  const qtyInput = document.getElementById("order-quantity-input");

  if (product.is_variable) {
    qtyField.classList.remove("hidden");
    qtyLabel.textContent = `Количество (минимум ${product.min_quantity})`;
    qtyInput.placeholder = String(product.min_quantity);
    qtyInput.value = presetQty || product.min_quantity;
    renderQtyPresets(product);
  } else {
    qtyField.classList.add("hidden");
    qtyInput.value = "";
  }

  const field = document.getElementById("order-recipient-field");
  const label = document.getElementById("order-recipient-label");
  const input = document.getElementById("order-recipient-input");
  input.value = "";

  if (product.requires_recipient) {
    field.classList.remove("hidden");
    label.textContent = product.recipient_label;
  } else {
    field.classList.add("hidden");
  }

  updateOrderPrice();
  showScreen("order");
}

document.getElementById("order-quantity-input").oninput = updateOrderPrice;

document.getElementById("btn-create-order").onclick = async () => {
  if (!selectedProduct) return;
  const recipientInput = document.getElementById("order-recipient-input");
  if (selectedProduct.requires_recipient && !recipientInput.value.trim()) {
    alertMsg("Укажите получателя");
    return;
  }

  let quantity = 1;
  if (selectedProduct.is_variable) {
    quantity = parseInt(document.getElementById("order-quantity-input").value, 10) || 0;
    if (quantity < selectedProduct.min_quantity) {
      alertMsg(`Минимальное количество — ${selectedProduct.min_quantity}`);
      return;
    }
  }

  const formData = new FormData();
  formData.append("product_id", selectedProduct.id);
  formData.append("recipient_info", recipientInput.value.trim());
  formData.append("quantity", quantity);

  try {
    const order = await api("/api/orders", { method: "POST", body: formData });
    currentOrderId = order.order_id;
    currency = order.currency;
    document.getElementById("pay-order-id").textContent = order.order_id;
    document.getElementById("pay-amount").textContent = formatMoney(order.total_price);
    document.getElementById("pay-bank").textContent = order.card.bank_name;
    document.getElementById("pay-card-number").textContent = order.card.card_number;
    document.getElementById("pay-holder").textContent = order.card.holder_name;
    receiptFile = null;
    document.getElementById("btn-send-receipt").disabled = true;
    const box = document.getElementById("upload-box");
    document.getElementById("upload-box-text").textContent = "Выбрать фото чека";
    box.classList.remove("filled");
    showScreen("payment");
  } catch (e) {
    alertMsg(e.message);
  }
};

document.getElementById("pay-card-number").onclick = () => {
  const text = document.getElementById("pay-card-number").textContent;
  navigator.clipboard?.writeText(text.replace(/\s/g, "")).then(() => {
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
  }).catch(() => {});
};

document.getElementById("receipt-input").onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  receiptFile = file;
  const box = document.getElementById("upload-box");
  document.getElementById("upload-box-text").textContent = file.name;
  box.classList.add("filled");
  document.getElementById("btn-send-receipt").disabled = false;
};

document.getElementById("btn-send-receipt").onclick = async () => {
  if (!receiptFile || !currentOrderId) return;
  const formData = new FormData();
  formData.append("file", receiptFile);

  try {
    await api(`/api/orders/${currentOrderId}/receipt`, { method: "POST", body: formData });
    showScreen("done");
  } catch (e) {
    alertMsg(e.message);
  }
};

/* ---------- Orders list ---------- */
async function loadOrders() {
  const list = document.getElementById("orders-list");
  list.innerHTML = '<p class="muted">Загрузка...</p>';
  try {
    const orders = await api("/api/me/orders");
    if (!orders.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">${icon("boxEmpty")}</div>
          <div class="title">Нет заказов</div>
          <div class="muted">Ваш первый заказ появится здесь</div>
        </div>`;
      return;
    }
    list.innerHTML = "";
    orders.forEach((o) => {
      const pillClass = o.status === "completed" ? "done" : o.status === "rejected" || o.status === "cancelled" ? "rejected" : "";
      const row = document.createElement("div");
      row.className = "order-row";
      row.innerHTML = `
        <div class="top"><span>№${o.id} · ${o.product_title}</span><span>${formatMoney(o.total_price)}</span></div>
        <span class="status-pill ${pillClass}">${STATUS_LABELS[o.status] || o.status}</span>
      `;
      list.appendChild(row);
    });
  } catch (e) {
    list.innerHTML = `<p class="muted">Ошибка загрузки: ${e.message}</p>`;
  }
}

/* ---------- Navigation wiring ---------- */
document.querySelectorAll("[data-back]").forEach((btn) => {
  btn.addEventListener("click", () => showScreen(btn.dataset.back));
});

document.querySelectorAll("[data-nav]").forEach((btn) => {
  btn.addEventListener("click", () => showScreen(btn.dataset.nav));
});

document.getElementById("btn-refresh").addEventListener("click", () => location.reload());

document.getElementById("btn-support").addEventListener("click", () => {
  alertMsg("Напишите вопрос в чат бота — раздел «Поддержка».");
});

/* ---------- Init ---------- */
async function init() {
  setupChrome();
  setupUserUI();

  try {
    const me = await api("/api/me");
    currency = me.currency;
  } catch (e) {
    document.getElementById("splash").classList.add("hidden");
    document.getElementById("app").classList.remove("hidden");
    document.getElementById("home-popular").innerHTML =
      `<p class="muted">Не удалось авторизоваться: ${e.message}. Откройте магазин через кнопку в боте.</p>`;
    return;
  }

  try {
    catalog = await api("/api/catalog");
    catalog.forEach((cat) => {
      cat.products = cat.products.map((p) => ({ ...p, _categoryType: cat.type }));
    });
  } catch (e) {
    catalog = [];
  }

  renderHome();

  document.getElementById("splash").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}

init();
