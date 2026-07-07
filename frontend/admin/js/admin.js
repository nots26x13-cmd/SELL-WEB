let editingProductId = null;
let packageRowCount = 0;

// ---------- Tabs ----------
document.querySelectorAll(".admin-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".admin-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".admin-panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add("active");
  });
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await apiFetch("/api/admin/logout", { method: "POST" });
  window.location.href = "login.html";
});

// ---------- Auth guard ----------
async function guardAuth() {
  try {
    await apiFetch("/api/admin/settings");
  } catch (err) {
    window.location.href = "login.html";
  }
}

// ---------- Package row builder ----------
function addPackageRow(pkg = {}) {
  packageRowCount += 1;
  const id = `pkg_${packageRowCount}`;
  const wrap = document.createElement("div");
  wrap.className = "admin-grid";
  wrap.id = id;
  wrap.style.marginBottom = "8px";
  wrap.innerHTML = `
    <div class="form-row"><label>Label</label><input class="pkg-label" value="${pkg.label || ''}" placeholder="220 likes / 7day" /></div>
    <div class="form-row"><label>Price (BDT)</label><input class="pkg-price" type="number" value="${pkg.price_bdt || ''}" /></div>
    <div class="form-row"><label>Duration (days)</label><input class="pkg-duration" type="number" value="${pkg.duration_days || ''}" /></div>
    <div class="form-row"><label>Qty / day</label><input class="pkg-qty" type="number" value="${pkg.quantity_per_day || ''}" /></div>
    <div class="form-row"><label>In stock?</label>
      <select class="pkg-stock"><option value="true" ${pkg.in_stock !== false ? "selected" : ""}>Yes</option><option value="false" ${pkg.in_stock === false ? "selected" : ""}>No</option></select>
    </div>
    <button class="btn-sm reject" style="align-self:end;" onclick="document.getElementById('${id}').remove()">Remove</button>
  `;
  wrap.dataset.pkgId = pkg.id || `p${packageRowCount}-${Date.now()}`;
  document.getElementById("packageRows").appendChild(wrap);
}

function resetProductForm() {
  editingProductId = null;
  document.getElementById("p_name").value = "";
  document.getElementById("p_subtitle").value = "";
  document.getElementById("p_category").value = "";
  document.getElementById("p_requires_uid").value = "true";
  document.getElementById("packageRows").innerHTML = "";
}

function collectPackagesFromForm() {
  return [...document.querySelectorAll("#packageRows > div")].map(row => ({
    id: row.dataset.pkgId,
    label: row.querySelector(".pkg-label").value,
    price_bdt: parseFloat(row.querySelector(".pkg-price").value || "0"),
    duration_days: row.querySelector(".pkg-duration").value ? parseInt(row.querySelector(".pkg-duration").value) : null,
    quantity_per_day: row.querySelector(".pkg-qty").value ? parseInt(row.querySelector(".pkg-qty").value) : null,
    in_stock: row.querySelector(".pkg-stock").value === "true",
  }));
}

async function saveProduct() {
  const payload = {
    id: editingProductId,
    name: document.getElementById("p_name").value.trim(),
    subtitle: document.getElementById("p_subtitle").value.trim(),
    category: document.getElementById("p_category").value.trim() || "general",
    requires_uid: document.getElementById("p_requires_uid").value === "true",
    packages: collectPackagesFromForm(),
    active: true,
  };
  if (!payload.name || payload.packages.length === 0) {
    alert("Add a name and at least one package.");
    return;
  }
  const path = editingProductId ? `/api/admin/products/${editingProductId}` : "/api/admin/products";
  await apiFetch(path, { method: editingProductId ? "PUT" : "POST", body: JSON.stringify(payload) });
  resetProductForm();
  loadProducts();
}

function editProduct(product) {
  editingProductId = product.id;
  document.getElementById("p_name").value = product.name;
  document.getElementById("p_subtitle").value = product.subtitle || "";
  document.getElementById("p_category").value = product.category;
  document.getElementById("p_requires_uid").value = String(product.requires_uid);
  document.getElementById("packageRows").innerHTML = "";
  product.packages.forEach(pkg => addPackageRow(pkg));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteProduct(id) {
  if (!confirm("Delete this product?")) return;
  await apiFetch(`/api/admin/products/${id}`, { method: "DELETE" });
  loadProducts();
}

async function loadProducts() {
  const products = await Api.listProducts();
  const tbody = document.querySelector("#productsTable tbody");
  tbody.innerHTML = products.map(p => `
    <tr>
      <td>${p.name}</td>
      <td>${p.category}</td>
      <td>${p.packages.length}</td>
      <td>${p.active ? "Yes" : "No"}</td>
      <td style="display:flex; gap:6px;">
        <button class="btn-sm approve" onclick='editProduct(${JSON.stringify(p).replace(/'/g, "&apos;")})'>Edit</button>
        <button class="btn-sm reject" onclick="deleteProduct('${p.id}')">Delete</button>
      </td>
    </tr>
  `).join("");
}

// ---------- Settings ----------
async function loadSettings() {
  const cfg = await apiFetch("/api/admin/settings");
  document.getElementById("pm_binance").checked = !!cfg.payment_methods.binance;
  document.getElementById("pm_bkash").checked = !!cfg.payment_methods.bkash;
  document.getElementById("pm_nagad").checked = !!cfg.payment_methods.nagad;
  document.getElementById("s_binance_pay_id").value = cfg.binance_pay_id;
  document.getElementById("s_min_deposit").value = cfg.min_deposit_usdt;
  document.getElementById("s_nickname_url").value = cfg.nickname_api_base_url;
  document.getElementById("s_nickname_enabled").checked = !!cfg.nickname_api_enabled;
}

async function saveSettings() {
  const payload = {
    binance_pay_id: document.getElementById("s_binance_pay_id").value.trim(),
    min_deposit_usdt: parseFloat(document.getElementById("s_min_deposit").value || "0"),
    payment_methods: {
      binance: document.getElementById("pm_binance").checked,
      bkash: document.getElementById("pm_bkash").checked,
      nagad: document.getElementById("pm_nagad").checked,
    },
    nickname_api_base_url: document.getElementById("s_nickname_url").value.trim(),
    nickname_api_enabled: document.getElementById("s_nickname_enabled").checked,
  };
  await apiFetch("/api/admin/settings", { method: "PUT", body: JSON.stringify(payload) });
  const resultEl = document.getElementById("settingsResult");
  resultEl.textContent = "Saved ✓";
  resultEl.style.color = "var(--success)";
  setTimeout(() => (resultEl.textContent = ""), 2000);
}

// ---------- Orders ----------
async function loadOrders() {
  const orders = await apiFetch("/api/admin/orders");
  const tbody = document.querySelector("#ordersTable tbody");
  tbody.innerHTML = orders
    .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""))
    .map(o => `
      <tr>
        <td>${o.product_name}<br /><small style="color:var(--text-muted);">${o.package_label}</small></td>
        <td>${o.player_uid}</td>
        <td>${bdt(o.price_bdt)}</td>
        <td>${o.status.replace(/_/g, " ")}</td>
        <td style="display:flex; gap:6px;">
          <button class="btn-sm approve" onclick="setOrderStatus('${o.id}', 'fulfilled')">Mark fulfilled</button>
          <button class="btn-sm reject" onclick="setOrderStatus('${o.id}', 'rejected')">Reject & refund</button>
        </td>
      </tr>
    `).join("");
}

async function setOrderStatus(orderId, status) {
  await apiFetch(`/api/admin/orders/${orderId}/status`, { method: "PUT", body: JSON.stringify({ status }) });
  loadOrders();
}

// ---------- Init ----------
(async function init() {
  await guardAuth();
  await Promise.all([loadProducts(), loadSettings(), loadOrders()]);
})();
