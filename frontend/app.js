/* ================================================================
   Card Exchange — SPA
================================================================ */
const TOKEN_KEY = "ce_token";

// ── State ──────────────────────────────────────────────────────
const state = {
  user: null,
  token: null,
  ws: null,
  notifications: [],
  shop: { skip: 0, limit: 20, hasMore: true },
  tm:   { skip: 0, limit: 20, hasMore: true },
  selectedOfferedCardId: null,
  pendingBuyCard: null,
  pendingOfferCard: null,
};

// ── API ────────────────────────────────────────────────────────
async function api(method, path, body, asForm = false) {
  const headers = {};
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  let init = { method, headers };
  if (body && !asForm) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  } else if (body && asForm) {
    init.body = body;
  }
  const res = await fetch(path, init);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

// ── Token helpers ──────────────────────────────────────────────
function saveToken(t)  { localStorage.setItem(TOKEN_KEY, t); state.token = t; }
function loadToken()   { state.token = localStorage.getItem(TOKEN_KEY); }
function clearToken()  { localStorage.removeItem(TOKEN_KEY); state.token = null; }

// ── Misc DOM helpers ───────────────────────────────────────────
function showMsg(el, text, type = "") {
  el.textContent = text;
  el.className = `msg ${type}`.trim();
}
function clearMsg(el) { el.textContent = ""; el.className = "msg"; }

function avatarSrc(url) {
  if (!url) return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%2330363d'/%3E%3Ctext x='20' y='26' text-anchor='middle' fill='%238b949e' font-size='18'%3E♟%3C/text%3E%3C/svg%3E";
  return url;
}

function rarityClass(r) {
  return `rarity-${r}`;
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "short", year: "numeric" });
}

function fmtTime(iso) {
  return new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// ── Card render ────────────────────────────────────────────────
function renderCardItem(card, actions = []) {
  const div = document.createElement("div");
  div.className = "card-item";
  const imgEl = card.image_url
    ? `<img class="card-item-img" src="${card.image_url}" alt="${card.name}" loading="lazy">`
    : `<div class="card-item-img-placeholder">♟</div>`;

  const badges = card.is_for_sale
    ? `<span class="sale-badge">На продаже · ${formatCoin(card.sale_price)}</span>`
    : "";
  const locked = card.is_locked ? `<span class="card-item-locked">🔒 В обмене</span>` : "";

  div.innerHTML = `
    ${imgEl}
    <div class="card-item-body">
      <div class="card-item-name">${card.name}</div>
      <div class="card-item-rarity ${rarityClass(card.rarity)}">${card.rarity.toUpperCase()}</div>
      ${badges}${locked}
      <div class="card-item-stats">⚔ ${card.power} &nbsp; 🛡 ${card.defense}</div>
      <div class="card-item-price">${formatCoin(card.price)}</div>
      ${card.owner_username ? `<div class="card-item-owner">Владелец: ${card.owner_username}</div>` : ""}
    </div>
    <div class="card-item-actions"></div>
  `;

  const actDiv = div.querySelector(".card-item-actions");
  actions.forEach(({ label, cls, fn }) => {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.className = cls || "btn-secondary";
    btn.style.fontSize = "12px";
    btn.style.padding = "6px 10px";
    btn.addEventListener("click", () => fn(card, btn));
    actDiv.appendChild(btn);
  });
  return div;
}

function formatCoin(v) { return `${Number(v).toFixed(2)} ¢`; }

// ── Navigation ─────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const page = document.getElementById(`page-${name}`);
  if (page) page.classList.add("active");
  document.querySelectorAll(".nav-link").forEach(l => {
    l.classList.toggle("active", l.dataset.page === name);
  });
}

// ── Auth screen ────────────────────────────────────────────────
const authScreen = document.getElementById("auth-screen");
const appScreen  = document.getElementById("app-screen");

function showAuth() {
  authScreen.classList.remove("hidden");
  appScreen.classList.add("hidden");
}
function showApp() {
  authScreen.classList.add("hidden");
  appScreen.classList.remove("hidden");
}

// Auth tabs
document.querySelectorAll("[data-auth-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.authTab;
    document.querySelectorAll("[data-auth-tab]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    document.getElementById(`${tab}-form`).classList.add("active");
    clearMsg(document.getElementById("auth-msg"));
  });
});

// Check for reset token in URL
(function checkResetToken() {
  const hash = window.location.hash;
  if (hash.startsWith("#reset-password")) {
    const params = new URLSearchParams(hash.split("?")[1] || "");
    const token = params.get("token");
    if (token) {
      document.querySelectorAll("[data-auth-tab]").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
      document.querySelector("[data-auth-tab='forgot']").classList.add("active");
      const resetForm = document.getElementById("reset-form");
      resetForm.classList.add("active");
      resetForm.querySelector("[name='token']").value = token;
      history.replaceState(null, "", "/");
    }
  }
})();

// Login
document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("auth-msg");
  const data = Object.fromEntries(new FormData(e.target));
  try {
    const res = await api("POST", "/auth/login", data);
    saveToken(res.access_token);
    await loadCurrentUser();
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// Register
document.getElementById("register-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("auth-msg");
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("POST", "/auth/register", data);
    showMsg(msg, "Аккаунт создан! Теперь войди.", "success");
    document.querySelectorAll("[data-auth-tab]").forEach(b => b.classList.remove("active"));
    document.querySelector("[data-auth-tab='login']").classList.add("active");
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    document.getElementById("login-form").classList.add("active");
    document.getElementById("register-form").reset();
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// Forgot password
document.getElementById("forgot-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("auth-msg");
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("POST", "/auth/forgot-password", data);
    showMsg(msg, "Если email найден — ссылка отправлена.", "success");
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// Reset password
document.getElementById("reset-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("auth-msg");
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("POST", "/auth/reset-password", data);
    showMsg(msg, "Пароль изменён! Войди с новым паролем.", "success");
    e.target.reset();
    document.querySelectorAll("[data-auth-tab]").forEach(b => b.classList.remove("active"));
    document.querySelector("[data-auth-tab='login']").classList.add("active");
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    document.getElementById("login-form").classList.add("active");
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ── Load current user ──────────────────────────────────────────
async function loadCurrentUser() {
  if (!state.token) { showAuth(); return; }
  try {
    state.user = await api("GET", "/auth/me");
    renderNavUser();
    showApp();
    showPage("shop");
    loadShop();
    connectWS();
  } catch {
    clearToken();
    showAuth();
  }
}

function renderNavUser() {
  const u = state.user;
  document.getElementById("nav-avatar").src = avatarSrc(u.avatar_url);
  document.getElementById("nav-username").textContent = u.username;
  document.getElementById("nav-balance").textContent = formatCoin(u.balance);
  document.getElementById("nav-mod").classList.toggle("hidden", !["moderator", "admin"].includes(u.role));
  document.getElementById("nav-admin").classList.toggle("hidden", u.role !== "admin");
}

// ── Logout ─────────────────────────────────────────────────────
document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  state.user = null;
  if (state.ws) { state.ws.close(); state.ws = null; }
  showAuth();
});

// ── Navigation clicks ──────────────────────────────────────────
document.querySelectorAll("[data-page]").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const page = link.dataset.page;
    showPage(page);
    if (page === "shop")       loadShop(true);
    if (page === "trade-market") loadTradeMarket(true);
    if (page === "profile")    loadProfile();
    if (page === "find-users") { document.getElementById("user-search-results").innerHTML = ""; document.getElementById("viewed-profile").classList.add("hidden"); }
    if (page === "moderation") loadModeration();
  });
});

// ── Profile tabs ───────────────────────────────────────────────
document.querySelectorAll("[data-profile-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-profile-tab]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".profile-tab").forEach(t => t.classList.remove("active"));
    document.getElementById(`profile-tab-${btn.dataset.profileTab}`).classList.add("active");
    if (btn.dataset.profileTab === "pending-trades") loadPendingTrades();
    if (btn.dataset.profileTab === "history") loadMyHistory();
  });
});

// ── Viewed Profile tabs ────────────────────────────────────────
document.querySelectorAll("[data-vp-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-vp-tab]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll("[id^='vp-tab-']").forEach(t => t.classList.remove("active"));
    document.getElementById(`vp-tab-${btn.dataset.vpTab}`).classList.add("active");
  });
});

// ════════════════════════════════════════════════════════════════
//  SHOP PAGE
// ════════════════════════════════════════════════════════════════
async function loadShop(reset = false) {
  if (reset) { state.shop.skip = 0; state.shop.hasMore = true; }
  const search   = document.getElementById("shop-search").value.trim();
  const rarity   = document.getElementById("shop-rarity").value;
  const minPrice = document.getElementById("shop-min-price").value;
  const maxPrice = document.getElementById("shop-max-price").value;
  const { skip, limit } = state.shop;

  const params = new URLSearchParams({ for_sale: "true", skip, limit });
  if (search)   params.set("search",    search);
  if (rarity)   params.set("rarity",    rarity);
  if (minPrice) params.set("min_price", minPrice);
  if (maxPrice) params.set("max_price", maxPrice);

  try {
    const cards = await api("GET", `/cards?${params}`);
    const grid = document.getElementById("shop-grid");
    if (reset) grid.innerHTML = "";
    if (!cards.length) {
      if (reset) grid.innerHTML = `<p class="muted">Карточек на продаже нет.</p>`;
      state.shop.hasMore = false;
    } else {
      cards.forEach(c => {
        const actions = [];
        if (state.user && c.owner_id !== state.user.id) {
          actions.push({ label: `Купить ${formatCoin(c.sale_price)}`, cls: "btn-primary", fn: card => openBuyModal(card) });
        }
        grid.appendChild(renderCardItem(c, actions));
      });
      state.shop.hasMore = cards.length === limit;
    }
    updatePagination("shop");
  } catch (err) { console.error(err); }
}

document.getElementById("shop-filter-btn").addEventListener("click", () => loadShop(true));
document.getElementById("shop-search").addEventListener("keydown", e => { if (e.key === "Enter") loadShop(true); });
document.getElementById("shop-prev").addEventListener("click", () => {
  state.shop.skip = Math.max(0, state.shop.skip - state.shop.limit);
  loadShop();
});
document.getElementById("shop-next").addEventListener("click", () => {
  state.shop.skip += state.shop.limit;
  loadShop();
});

function updatePagination(ns) {
  const page = Math.floor(state[ns].skip / state[ns].limit) + 1;
  document.getElementById(`${ns}-page-info`).textContent = `Страница ${page}`;
  document.getElementById(`${ns}-prev`).disabled = state[ns].skip === 0;
  document.getElementById(`${ns}-next`).disabled = !state[ns].hasMore;
}

// ════════════════════════════════════════════════════════════════
//  TRADE MARKET PAGE
// ════════════════════════════════════════════════════════════════
async function loadTradeMarket(reset = false) {
  if (reset) { state.tm.skip = 0; state.tm.hasMore = true; }
  const search = document.getElementById("tm-search").value.trim();
  const rarity = document.getElementById("tm-rarity").value;
  const { skip, limit } = state.tm;

  const params = new URLSearchParams({ skip, limit });
  if (search) params.set("search", search);
  if (rarity) params.set("rarity", rarity);

  try {
    const cards = await api("GET", `/cards?${params}`);
    const grid = document.getElementById("tm-grid");
    if (reset) grid.innerHTML = "";
    if (!cards.length) {
      if (reset) grid.innerHTML = `<p class="muted">Карточек нет.</p>`;
      state.tm.hasMore = false;
    } else {
      const myCards = state.user ? await api("GET", `/cards/user/${state.user.id}`) : [];
      cards.forEach(c => {
        const isOwn = state.user && c.owner_id === state.user.id;
        const actions = [];
        if (!isOwn && state.user) {
          actions.push({ label: "Предложить обмен", cls: "btn-secondary", fn: card => openTradeModal(card, myCards) });
        }
        grid.appendChild(renderCardItem(c, actions));
      });
      state.tm.hasMore = cards.length === limit;
    }
    updatePagination("tm");
  } catch (err) { console.error(err); }
}

document.getElementById("tm-filter-btn").addEventListener("click", () => loadTradeMarket(true));
document.getElementById("tm-search").addEventListener("keydown", e => { if (e.key === "Enter") loadTradeMarket(true); });
document.getElementById("tm-prev").addEventListener("click", () => {
  state.tm.skip = Math.max(0, state.tm.skip - state.tm.limit);
  loadTradeMarket();
});
document.getElementById("tm-next").addEventListener("click", () => {
  state.tm.skip += state.tm.limit;
  loadTradeMarket();
});

// ════════════════════════════════════════════════════════════════
//  PROFILE PAGE
// ════════════════════════════════════════════════════════════════
async function loadProfile() {
  const u = state.user;
  document.getElementById("profile-username").textContent = u.username;
  document.getElementById("profile-avatar-img").src = avatarSrc(u.avatar_url);
  document.getElementById("profile-balance").textContent = formatCoin(u.balance);
  const badge = document.getElementById("profile-role-badge");
  badge.textContent = u.role;
  badge.className = `role-badge role-${u.role}`;

  // Reload fresh user data for balance
  try {
    state.user = await api("GET", "/auth/me");
    renderNavUser();
    document.getElementById("profile-balance").textContent = formatCoin(state.user.balance);
    document.getElementById("nav-avatar").src = avatarSrc(state.user.avatar_url);
    document.getElementById("profile-avatar-img").src = avatarSrc(state.user.avatar_url);
  } catch {}

  await loadInventory();
}

async function loadInventory() {
  const search = document.getElementById("inv-search").value.toLowerCase();
  const grid = document.getElementById("inventory-grid");
  grid.innerHTML = "";
  try {
    let cards = await api("GET", `/cards/user/${state.user.id}`);
    if (search) cards = cards.filter(c => c.name.toLowerCase().includes(search));
    if (!cards.length) { grid.innerHTML = `<p class="muted">Коллекция пуста.</p>`; return; }
    cards.forEach(c => {
      const actions = [];
      if (!c.is_locked) {
        if (!c.is_for_sale) {
          actions.push({ label: "Выставить на продажу", cls: "btn-secondary", fn: card => promptListForSale(card) });
        } else {
          actions.push({ label: "Снять с продажи", cls: "btn-ghost", fn: card => delistCard(card) });
        }
      }
      grid.appendChild(renderCardItem(c, actions));
    });
  } catch (err) { console.error(err); }
}

document.getElementById("inv-search").addEventListener("input", () => loadInventory());

async function promptListForSale(card) {
  const price = prompt(`Цена продажи для "${card.name}" (текущая: ${card.price}):`);
  if (!price || isNaN(price) || Number(price) <= 0) return;
  try {
    await api("POST", `/cards/${card.id}/list`, { sale_price: Number(price) });
    await loadInventory();
  } catch (err) { alert(err.message); }
}

async function delistCard(card) {
  try {
    await api("DELETE", `/cards/${card.id}/list`);
    await loadInventory();
  } catch (err) { alert(err.message); }
}

// Avatar upload
document.getElementById("avatar-input").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await api("PUT", "/auth/me/avatar", fd, true);
    state.user.avatar_url = res.avatar_url;
    document.getElementById("profile-avatar-img").src = avatarSrc(res.avatar_url);
    document.getElementById("nav-avatar").src = avatarSrc(res.avatar_url);
  } catch (err) { alert(err.message); }
});

// Change password
document.getElementById("change-pass-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("settings-msg");
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("POST", "/auth/change-password", data);
    showMsg(msg, "Пароль изменён.", "success");
    e.target.reset();
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ── Pending Trades ─────────────────────────────────────────────
async function loadPendingTrades() {
  const list = document.getElementById("pending-trades-list");
  list.innerHTML = "";
  try {
    const offers = await api("GET", "/trades/offers/mine");
    if (!offers.length) { list.innerHTML = `<p class="muted">Нет активных предложений.</p>`; return; }
    for (const offer of offers) {
      list.appendChild(renderOffer(offer));
    }
  } catch (err) { console.error(err); }
}

function renderOffer(offer) {
  const div = document.createElement("div");
  div.className = "offer-item";
  const isRequester = offer.requester_id === state.user.id;
  const offeredSnap = JSON.parse(offer.offered_card_snapshot);
  const requestedSnap = JSON.parse(offer.requested_card_snapshot);

  const statusLabel = { pending: "Ожидание", accepted: "Принят", rejected: "Отклонён", cancelled: "Отменён" }[offer.status] || offer.status;

  div.innerHTML = `
    <div class="offer-cards">
      <img class="offer-thumb" src="${offeredSnap.image_url || ""}" alt="${offeredSnap.name}" onerror="this.style.display='none'">
      <div class="offer-arrow">⇄</div>
      <img class="offer-thumb" src="${requestedSnap.image_url || ""}" alt="${requestedSnap.name}" onerror="this.style.display='none'">
    </div>
    <div class="offer-meta">
      <div><strong>${offeredSnap.name}</strong> ⇄ <strong>${requestedSnap.name}</strong></div>
      <div class="muted">${isRequester ? "Ты предложил → " + offer.responder_username : offer.requester_username + " → тебе"}</div>
      <div class="muted">${fmtTime(offer.created_at)}</div>
    </div>
    <span class="offer-status status-${offer.status}">${statusLabel}</span>
    <div class="offer-actions"></div>
  `;

  const actions = div.querySelector(".offer-actions");

  if (offer.status === "pending") {
    if (!isRequester) {
      const acceptBtn = document.createElement("button");
      acceptBtn.textContent = "Принять";
      acceptBtn.className = "btn-primary";
      acceptBtn.style.fontSize = "13px";
      acceptBtn.style.padding = "7px 12px";
      acceptBtn.addEventListener("click", () => respondOffer(offer.id, "accept", div));
      actions.appendChild(acceptBtn);

      const rejectBtn = document.createElement("button");
      rejectBtn.textContent = "Отклонить";
      rejectBtn.className = "btn-danger";
      rejectBtn.style.fontSize = "13px";
      rejectBtn.addEventListener("click", () => respondOffer(offer.id, "reject", div));
      actions.appendChild(rejectBtn);
    } else {
      const cancelBtn = document.createElement("button");
      cancelBtn.textContent = "Отменить";
      cancelBtn.className = "btn-ghost";
      cancelBtn.style.fontSize = "13px";
      cancelBtn.addEventListener("click", () => respondOffer(offer.id, "cancel", div));
      actions.appendChild(cancelBtn);
    }

    const detailBtn = document.createElement("button");
    detailBtn.textContent = "Подробнее";
    detailBtn.className = "btn-ghost";
    detailBtn.style.fontSize = "13px";
    detailBtn.addEventListener("click", () => openOfferModal(offer));
    actions.appendChild(detailBtn);
  }

  return div;
}

async function respondOffer(offerId, action, rowEl) {
  try {
    await api("POST", `/trades/offers/${offerId}/${action}`);
    rowEl.remove();
    await refreshBalance();
    if (action === "accept") addNotification("Предложение обмена принято!");
  } catch (err) { alert(err.message); }
}

// ── Transaction History ────────────────────────────────────────
async function loadMyHistory() {
  const list = document.getElementById("history-list");
  list.innerHTML = "";
  try {
    const txs = await api("GET", "/trades/history/me");
    renderHistory(list, txs);
  } catch (err) { console.error(err); }
}

function renderHistory(container, txs) {
  if (!txs.length) { container.innerHTML = `<p class="muted">История пуста.</p>`; return; }
  txs.forEach(tx => container.appendChild(renderTx(tx)));
}

function renderTx(tx) {
  const div = document.createElement("div");
  div.className = "history-item";
  const isBuyer  = tx.initiator_id === state.user?.id && tx.type === "buy";
  const isSeller = tx.counterparty_id === state.user?.id && tx.type === "buy";
  const isTrade  = tx.type === "trade";

  const typeLabel = { buy: isBuyer ? "Покупка" : "Продажа", sell: "Продажа", trade: "Обмен" }[tx.type] || tx.type;
  const typeClass = { buy: isBuyer ? "tx-buy" : "tx-sell", sell: "tx-sell", trade: "tx-trade" }[tx.type] || "tx-buy";
  const priceEl   = isSeller ? `<div class="history-price">+${formatCoin(tx.price)}</div>` :
                    isBuyer  ? `<div class="history-price negative">-${formatCoin(tx.price)}</div>` :
                    `<div class="history-price">${formatCoin(tx.price)}</div>`;

  div.innerHTML = `
    <img class="history-thumb" src="${tx.card_image_url || ""}" alt="${tx.card_name}" onerror="this.style.display='none'">
    <div class="history-meta">
      <div><strong>${tx.card_name}</strong></div>
      <div class="muted">${isTrade ? `${tx.initiator_username} ⇄ ${tx.counterparty_username}` : (isBuyer ? `У ${tx.counterparty_username}` : `Купил ${tx.initiator_username}`)}</div>
      <div class="muted">${fmtTime(tx.created_at)}</div>
    </div>
    ${priceEl}
    <span class="tx-type ${typeClass}">${typeLabel}</span>
  `;
  return div;
}

// ════════════════════════════════════════════════════════════════
//  FIND USERS PAGE
// ════════════════════════════════════════════════════════════════
document.getElementById("user-search-btn").addEventListener("click", searchUsers);
document.getElementById("user-search-input").addEventListener("keydown", e => { if (e.key === "Enter") searchUsers(); });

async function searchUsers() {
  const q = document.getElementById("user-search-input").value.trim();
  if (q.length < 2) return;
  const results = document.getElementById("user-search-results");
  results.innerHTML = "";
  document.getElementById("viewed-profile").classList.add("hidden");
  try {
    const users = await api("GET", `/users/search?q=${encodeURIComponent(q)}`);
    if (!users.length) { results.innerHTML = `<p class="muted">Игроки не найдены.</p>`; return; }
    users.forEach(u => {
      const div = document.createElement("div");
      div.className = "user-result-item";
      div.innerHTML = `
        <img class="user-result-avatar" src="${avatarSrc(u.avatar_url)}" alt="">
        <div>
          <div class="user-result-name">${u.username}</div>
          <span class="role-badge role-${u.role}">${u.role}</span>
        </div>
      `;
      div.addEventListener("click", () => viewProfile(u));
      results.appendChild(div);
    });
  } catch (err) { console.error(err); }
}

async function viewProfile(user) {
  const vp = document.getElementById("viewed-profile");
  vp.classList.remove("hidden");
  document.getElementById("vp-avatar").src = avatarSrc(user.avatar_url);
  document.getElementById("vp-username").textContent = user.username;
  const badge = document.getElementById("vp-role-badge");
  badge.textContent = user.role;
  badge.className = `role-badge role-${user.role}`;
  document.getElementById("vp-joined").textContent = `Регистрация: ${fmtDate(user.created_at)}`;

  const cardGrid = document.getElementById("vp-card-grid");
  const historyList = document.getElementById("vp-history-list");
  cardGrid.innerHTML = "";
  historyList.innerHTML = "";

  try {
    const [cards, history] = await Promise.all([
      api("GET", `/cards/user/${user.id}`),
      api("GET", `/trades/history/user/${user.id}`),
    ]);
    if (!cards.length) { cardGrid.innerHTML = `<p class="muted">Коллекция пуста.</p>`; }
    else cards.forEach(c => cardGrid.appendChild(renderCardItem(c)));

    renderHistory(historyList, history);
  } catch (err) { console.error(err); }
}

// ════════════════════════════════════════════════════════════════
//  MODERATION PAGE
// ════════════════════════════════════════════════════════════════
async function loadModeration() {
  const isFake = document.getElementById("mod-fake-filter").value;
  const params = new URLSearchParams({ limit: 100 });
  if (isFake !== "") params.set("is_fake", isFake);
  const grid = document.getElementById("mod-grid");
  grid.innerHTML = "";
  try {
    const cards = await api("GET", `/api/admin/cards?${params}`);
    if (!cards.length) { grid.innerHTML = `<p class="muted">Карточек нет.</p>`; return; }
    cards.forEach(c => {
      const actions = [
        { label: c.is_fake ? "✓ Оригинал" : "⚠ Фейк", cls: "btn-secondary", fn: card => toggleFake(card) },
      ];
      if (c.is_fake) {
        actions.push({ label: "Удалить", cls: "btn-danger", fn: card => deleteFake(card) });
      }
      grid.appendChild(renderCardItem(c, actions));
    });
  } catch (err) { console.error(err); }
}

document.getElementById("mod-filter-btn").addEventListener("click", loadModeration);

async function toggleFake(card) {
  try {
    await api("PATCH", `/api/admin/cards/${card.id}/fake`);
    await loadModeration();
  } catch (err) { alert(err.message); }
}

async function deleteFake(card) {
  if (!confirm(`Удалить карточку "${card.name}"?`)) return;
  try {
    await api("DELETE", `/api/admin/cards/${card.id}`);
    await loadModeration();
  } catch (err) { alert(err.message); }
}

document.getElementById("add-card-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("add-card-msg");
  const data = Object.fromEntries(new FormData(e.target));
  data.price = Number(data.price);
  data.power = Number(data.power) || 0;
  data.defense = Number(data.defense) || 0;
  try {
    await api("POST", "/cards", data);
    showMsg(msg, "Карточка создана!", "success");
    e.target.reset();
    await loadModeration();
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ════════════════════════════════════════════════════════════════
//  ADMIN PAGE
// ════════════════════════════════════════════════════════════════
document.getElementById("assign-role-form").addEventListener("submit", async e => {
  e.preventDefault();
  const msg = document.getElementById("admin-msg");
  const data = Object.fromEntries(new FormData(e.target));
  data.role = "moderator";
  try {
    const res = await api("POST", "/api/admin/assign-role", data);
    showMsg(msg, `${res.username} теперь модератор.`, "success");
    e.target.reset();
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ════════════════════════════════════════════════════════════════
//  MODALS
// ════════════════════════════════════════════════════════════════
const overlay = document.getElementById("modal-overlay");

function openModal(id) {
  overlay.classList.remove("hidden");
  document.getElementById(id).classList.remove("hidden");
}
function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
  const anyOpen = Array.from(overlay.querySelectorAll(".modal")).some(m => !m.classList.contains("hidden"));
  if (!anyOpen) overlay.classList.add("hidden");
}

overlay.addEventListener("click", e => { if (e.target === overlay) { overlay.querySelectorAll(".modal").forEach(m => m.classList.add("hidden")); overlay.classList.add("hidden"); } });
document.querySelectorAll(".modal-close").forEach(btn => {
  btn.addEventListener("click", () => closeModal(btn.dataset.close));
});

// ── Buy Modal ──────────────────────────────────────────────────
function openBuyModal(card) {
  state.pendingBuyCard = card;
  const cont = document.getElementById("modal-buy-card");
  cont.innerHTML = renderMiniCard(card);
  document.getElementById("modal-buy-text").textContent =
    `Купить "${card.name}" за ${formatCoin(card.sale_price)}? Твой баланс: ${formatCoin(state.user.balance)}`;
  clearMsg(document.getElementById("modal-buy-msg"));
  openModal("modal-buy");
}

document.getElementById("modal-buy-confirm").addEventListener("click", async () => {
  const card = state.pendingBuyCard;
  if (!card) return;
  const msg = document.getElementById("modal-buy-msg");
  try {
    await api("POST", `/trades/buy/${card.id}`);
    closeModal("modal-buy");
    state.user = await api("GET", "/auth/me");
    renderNavUser();
    await loadShop(true);
    addNotification(`Ты купил "${card.name}" за ${formatCoin(card.sale_price)}`);
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ── Trade Propose Modal ────────────────────────────────────────
async function openTradeModal(requestedCard, myCards) {
  state.pendingOfferCard = requestedCard;
  state.selectedOfferedCardId = null;

  const reqDiv = document.getElementById("modal-requested-card");
  reqDiv.innerHTML = renderMiniCard(requestedCard);

  const listDiv = document.getElementById("modal-my-cards-list");
  listDiv.innerHTML = "";

  const eligible = myCards.filter(c => !c.is_locked && !c.is_fake && c.id !== requestedCard.id);
  if (!eligible.length) {
    listDiv.innerHTML = `<p class="muted">У тебя нет подходящих карточек.</p>`;
  } else {
    eligible.forEach(c => {
      const row = document.createElement("div");
      row.className = "mini-card-select";
      row.dataset.id = c.id;
      const imgSrc = c.image_url || "";
      row.innerHTML = `<img src="${imgSrc}" alt="${c.name}" onerror="this.style.display='none'"> <span><strong>${c.name}</strong> · ${c.rarity}</span>`;
      row.addEventListener("click", () => {
        listDiv.querySelectorAll(".mini-card-select").forEach(r => r.classList.remove("selected"));
        row.classList.add("selected");
        state.selectedOfferedCardId = c.id;
        document.getElementById("modal-trade-submit").disabled = false;
      });
      listDiv.appendChild(row);
    });
  }

  document.getElementById("modal-trade-submit").disabled = true;
  clearMsg(document.getElementById("modal-trade-msg"));
  openModal("modal-trade");
}

document.getElementById("modal-trade-submit").addEventListener("click", async () => {
  const msg = document.getElementById("modal-trade-msg");
  try {
    await api("POST", "/trades/offers", {
      offered_card_id: state.selectedOfferedCardId,
      requested_card_id: state.pendingOfferCard.id,
    });
    closeModal("modal-trade");
    addNotification(`Предложение обмена отправлено!`);
  } catch (err) { showMsg(msg, err.message, "error"); }
});

// ── Offer Detail Modal ─────────────────────────────────────────
function openOfferModal(offer) {
  const isRequester = offer.requester_id === state.user.id;
  const offeredSnap = JSON.parse(offer.offered_card_snapshot);
  const requestedSnap = JSON.parse(offer.requested_card_snapshot);

  document.getElementById("modal-offer-title").textContent =
    isRequester ? "Ты предложил обмен" : "Входящее предложение обмена";
  document.getElementById("modal-offer-label-a").textContent = `${offer.requester_username} предлагает:`;
  document.getElementById("modal-offer-label-b").textContent = `Хочет получить:`;
  document.getElementById("modal-offer-card-a").innerHTML = renderMiniCard(offeredSnap);
  document.getElementById("modal-offer-card-b").innerHTML = renderMiniCard(requestedSnap);

  const actions = document.getElementById("modal-offer-actions");
  actions.innerHTML = "";
  clearMsg(document.getElementById("modal-offer-msg"));

  if (offer.status === "pending" && !isRequester) {
    const acceptBtn = document.createElement("button");
    acceptBtn.textContent = "Принять";
    acceptBtn.className = "btn-primary";
    acceptBtn.addEventListener("click", async () => {
      try {
        await api("POST", `/trades/offers/${offer.id}/accept`);
        closeModal("modal-offer");
        await loadPendingTrades();
        await refreshBalance();
      } catch (err) { showMsg(document.getElementById("modal-offer-msg"), err.message, "error"); }
    });

    const rejectBtn = document.createElement("button");
    rejectBtn.textContent = "Отклонить";
    rejectBtn.className = "btn-danger";
    rejectBtn.addEventListener("click", async () => {
      try {
        await api("POST", `/trades/offers/${offer.id}/reject`);
        closeModal("modal-offer");
        await loadPendingTrades();
      } catch (err) { showMsg(document.getElementById("modal-offer-msg"), err.message, "error"); }
    });

    actions.appendChild(acceptBtn);
    actions.appendChild(rejectBtn);
  }

  openModal("modal-offer");
}

function renderMiniCard(card) {
  const img = card.image_url ? `<img src="${card.image_url}" alt="${card.name}" onerror="this.style.display='none'">` : "";
  return `
    ${img}
    <div class="mini-card-body">
      <div class="name">${card.name}</div>
      <div class="${rarityClass(card.rarity)} muted" style="font-size:12px">${(card.rarity||"").toUpperCase()}</div>
      <div style="font-size:12px;color:var(--muted)">⚔ ${card.power||0} &nbsp; 🛡 ${card.defense||0}</div>
    </div>
  `;
}

// ════════════════════════════════════════════════════════════════
//  NOTIFICATIONS
// ════════════════════════════════════════════════════════════════
const notifBtn   = document.getElementById("notification-btn");
const notifPanel = document.getElementById("notif-panel");
const notifBadge = document.getElementById("notif-badge");

notifBtn.addEventListener("click", e => {
  e.stopPropagation();
  notifPanel.classList.toggle("hidden");
  notifBadge.classList.add("hidden");
  notifBadge.textContent = "0";
  state.notifications.forEach(n => n.read = true);
});

document.getElementById("notif-clear").addEventListener("click", () => {
  state.notifications = [];
  document.getElementById("notif-list").innerHTML = "";
});

document.addEventListener("click", e => {
  if (!notifPanel.classList.contains("hidden") && !notifPanel.contains(e.target) && e.target !== notifBtn) {
    notifPanel.classList.add("hidden");
  }
});

const NOTIF_MESSAGES = {
  trade_offer_received: d => `📩 ${d.from} предлагает обмен на твою карту "${d.card_name}"`,
  trade_accepted:       d => `✅ ${d.by} принял твоё предложение обмена`,
  trade_rejected:       d => `❌ ${d.by} отклонил твоё предложение обмена`,
  card_sold:            d => `💰 "${d.card_name}" продана ${d.buyer} за ${formatCoin(d.price)}`,
  card_purchased:       d => `🛒 Ты купил "${d.card_name}" за ${formatCoin(d.price)}`,
};

function addNotification(text) {
  const item = { text, time: new Date(), read: false };
  state.notifications.unshift(item);

  const list = document.getElementById("notif-list");
  const div = document.createElement("div");
  div.className = "notif-item";
  div.innerHTML = `<div>${text}</div><div class="notif-time">${fmtTime(item.time.toISOString())}</div>`;
  list.prepend(div);

  if (notifPanel.classList.contains("hidden")) {
    const count = state.notifications.filter(n => !n.read).length;
    notifBadge.textContent = count;
    notifBadge.classList.remove("hidden");
  }
}

function onWSMessage(data) {
  const tpl = NOTIF_MESSAGES[data.type];
  if (tpl) addNotification(tpl(data));

  if (data.type === "trade_offer_received") {
    document.querySelectorAll("[data-profile-tab='pending-trades']").forEach(b => {
      if (b.classList.contains("active")) loadPendingTrades();
    });
  }
  if (data.type === "card_sold" || data.type === "card_purchased") {
    refreshBalance();
  }
}

// ── WebSocket ──────────────────────────────────────────────────
function connectWS() {
  if (!state.token) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws?token=${state.token}`);
  ws.onmessage = e => { try { onWSMessage(JSON.parse(e.data)); } catch {} };
  ws.onclose   = () => { setTimeout(() => { if (state.token) connectWS(); }, 3000); };
  state.ws = ws;
}

async function refreshBalance() {
  try {
    state.user = await api("GET", "/auth/me");
    renderNavUser();
  } catch {}
}

// ════════════════════════════════════════════════════════════════
//  BOOT
// ════════════════════════════════════════════════════════════════
loadToken();
loadCurrentUser();
