const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const initData = tg?.initData || "";

const STATUS_LABELS = {
  new: "🕓 Ожидает оплаты",
  awaiting_review: "🔎 Проверяется админом",
  approved: "✅ Оплата подтверждена",
  rejected: "❌ Отклонён",
  completed: "🎉 Выполнен",
  cancelled: "🚫 Отменён",
};

let catalog = [];
let activeCategoryId = null;
let selectedProduct = null;
let currency = "UZS";
let receiptFile = null;
let currentOrderId = null;

function formatMoney(value) {
  return Math.round(value).toLocaleString("ru-RU") + " " + currency;
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

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  document.getElementById("nav-catalog").classList.toggle("active", id === "screen-catalog");
  document.getElementById("nav-orders").classList.toggle("active", id === "screen-orders");
}

function renderTabs() {
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  catalog.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "tab" + (cat.id === activeCategoryId ? " active" : "");
    btn.textContent = cat.title;
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

  category.products.forEach((product) => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `
      <div>
        <div class="product-title">${product.title}</div>
        ${product.description ? `<div class="product-desc">${product.description}</div>` : ""}
      </div>
      <div class="product-price">${formatMoney(product.price)}</div>
    `;
    card.onclick = () => openOrderScreen(product);
    container.appendChild(card);
  });
}

function openOrderScreen(product) {
  selectedProduct = product;
  document.getElementById("order-title").textContent = product.title;
  document.getElementById("order-price").textContent = formatMoney(product.price);

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

  showScreen("screen-order");
}

document.getElementById("btn-create-order").onclick = async () => {
  if (!selectedProduct) return;
  const recipientInput = document.getElementById("order-recipient-input");
  if (selectedProduct.requires_recipient && !recipientInput.value.trim()) {
    tg?.showAlert ? tg.showAlert("Укажите получателя") : alert("Укажите получателя");
    return;
  }

  const formData = new FormData();
  formData.append("product_id", selectedProduct.id);
  formData.append("recipient_info", recipientInput.value.trim());

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
    document.getElementById("upload-box").textContent = "📎 Нажмите, чтобы выбрать фото чека";
    showScreen("screen-payment");
  } catch (e) {
    tg?.showAlert ? tg.showAlert(e.message) : alert(e.message);
  }
};

document.getElementById("upload-box").onclick = () => {
  document.getElementById("receipt-input").click();
};

document.getElementById("receipt-input").onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  receiptFile = file;
  document.getElementById("upload-box").textContent = "✅ Файл выбран: " + file.name;
  document.getElementById("btn-send-receipt").disabled = false;
};

document.getElementById("btn-send-receipt").onclick = async () => {
  if (!receiptFile || !currentOrderId) return;
  const formData = new FormData();
  formData.append("file", receiptFile);

  try {
    await api(`/api/orders/${currentOrderId}/receipt`, { method: "POST", body: formData });
    showScreen("screen-done");
  } catch (e) {
    tg?.showAlert ? tg.showAlert(e.message) : alert(e.message);
  }
};

async function loadOrders() {
  const list = document.getElementById("orders-list");
  list.innerHTML = '<p class="muted">Загрузка...</p>';
  try {
    const orders = await api("/api/me/orders");
    if (!orders.length) {
      list.innerHTML = '<p class="muted">У вас пока нет заказов.</p>';
      return;
    }
    list.innerHTML = "";
    orders.forEach((o) => {
      const row = document.createElement("div");
      row.className = "order-row";
      row.innerHTML = `
        <div><strong>№${o.id}</strong> · ${o.product_title}</div>
        <div>${formatMoney(o.total_price)}</div>
        <div class="status">${STATUS_LABELS[o.status] || o.status}</div>
      `;
      list.appendChild(row);
    });
  } catch (e) {
    list.innerHTML = `<p class="muted">Ошибка загрузки: ${e.message}</p>`;
  }
}

document.querySelectorAll("[data-back]").forEach((btn) => {
  btn.onclick = () => showScreen("screen-" + btn.dataset.back);
});

document.getElementById("nav-catalog").onclick = () => showScreen("screen-catalog");
document.getElementById("nav-orders").onclick = () => {
  showScreen("screen-orders");
  loadOrders();
};

async function init() {
  try {
    const me = await api("/api/me");
    currency = me.currency;
  } catch (e) {
    document.getElementById("products").innerHTML =
      `<p class="muted">Не удалось авторизоваться: ${e.message}. Откройте магазин через кнопку в боте.</p>`;
    return;
  }

  try {
    catalog = await api("/api/catalog");
  } catch (e) {
    document.getElementById("products").innerHTML = `<p class="muted">Ошибка загрузки каталога.</p>`;
    return;
  }

  if (catalog.length) {
    activeCategoryId = catalog[0].id;
    renderTabs();
    renderProducts();
  } else {
    document.getElementById("products").innerHTML = '<p class="muted">Товаров пока нет.</p>';
  }
}

init();
