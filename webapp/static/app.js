const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#0a0e1a"); } catch (e) {}
  try { tg.setBackgroundColor("#0a0e1a"); } catch (e) {}
}

const initData = tg?.initData || "";
const tgUser = tg?.initDataUnsafe?.user || null;

const STATUS_LABELS = {
  new: "🕓 Ожидает оплаты",
  awaiting_review: "🔎 Проверяется админом",
  approved: "✅ Оплата подтверждена",
  rejected: "❌ Отклонён",
  completed: "🎉 Выполнен",
  cancelled: "🚫 Отменён",
};

const CATEGORY_EMOJI = { stars: "⭐", premium: "💎", game: "🎮" };

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

function renderHome() {
  const catGrid = document.getElementById("home-categories");
  catGrid.innerHTML = "";
  catalog.forEach((cat) => {
    const tile = document.createElement("div");
    tile.className = "cat-tile";
    tile.innerHTML = `<div class="emoji">${CATEGORY_EMOJI[cat.type] || "🛍"}</div><div class="label">${cat.title}</div>`;
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
  const popularProducts = catalog.flatMap((c) => c.products).slice(0, 4);
  popularProducts.forEach((product) => popular.appendChild(productTile(product)));
}

function productTile(product) {
  const tile = document.createElement("div");
  tile.className = "product-tile";
  const priceLabel = product.is_variable
    ? `от ${formatMoney(product.unit_price * product.min_quantity)}`
    : formatMoney(product.price);
  tile.innerHTML = `
    <div class="icon">🎁</div>
    <div class="title">${product.title}</div>
    <div class="price">${priceLabel}</div>
  `;
  tile.onclick = () => openOrderScreen(product);
  return tile;
}

function renderTabs() {
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  catalog.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "tab" + (cat.id === activeCategoryId ? " active" : "");
    btn.textContent = (CATEGORY_EMOJI[cat.type] || "") + " " + cat.title;
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
  category.products.forEach((product) => container.appendChild(productTile(product)));
}

const QTY_PRESETS = [100, 300, 500, 750, 1000];

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

function openOrderScreen(product) {
  selectedProduct = product;
  document.getElementById("order-title").textContent = product.title;

  const qtyField = document.getElementById("order-quantity-field");
  const qtyLabel = document.getElementById("order-quantity-label");
  const qtyInput = document.getElementById("order-quantity-input");

  if (product.is_variable) {
    qtyField.classList.remove("hidden");
    qtyLabel.textContent = `Количество (минимум ${product.min_quantity})`;
    qtyInput.placeholder = String(product.min_quantity);
    qtyInput.value = product.min_quantity;
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
    box.textContent = "📎 Нажмите, чтобы выбрать фото чека";
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

document.getElementById("upload-box").onclick = () => {
  document.getElementById("receipt-input").click();
};

document.getElementById("receipt-input").onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  receiptFile = file;
  const box = document.getElementById("upload-box");
  box.textContent = "✅ Файл выбран: " + file.name;
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

async function loadOrders() {
  const list = document.getElementById("orders-list");
  list.innerHTML = '<p class="muted">Загрузка...</p>';
  try {
    const orders = await api("/api/me/orders");
    if (!orders.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="emoji">📦</div>
          <div>Нет заказов</div>
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

document.querySelectorAll("[data-back]").forEach((btn) => {
  btn.onclick = () => showScreen(btn.dataset.back);
});

document.querySelectorAll("[data-nav]").forEach((btn) => {
  btn.onclick = () => showScreen(btn.dataset.nav);
});

document.getElementById("btn-refresh").onclick = () => location.reload();

document.getElementById("btn-support").onclick = () => {
  if (tg?.openTelegramLink) {
    alertMsg("Напишите вопрос в чат бота — раздел «Поддержка».");
  } else {
    alertMsg("Напишите вопрос в чат бота — раздел «Поддержка».");
  }
};

async function init() {
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
  } catch (e) {
    catalog = [];
  }

  renderHome();

  document.getElementById("splash").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}

init();
