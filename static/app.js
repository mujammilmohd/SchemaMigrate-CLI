const $ = (id) => document.getElementById(id);
let databaseCache = null;
let pendingConfirmation = null;
let toastTimer = null;

const role = () => $("roleSelect").value;

function toast(message, isError = false) {
  const element = $("toast");
  element.textContent = message;
  element.className = `toast show${isError ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.className = "toast", 3800);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {})
    }
  });
  const raw = await response.text();
  let data;
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    console.error("Non-JSON response from", url, response.status, raw);
    throw new Error(`The server returned an unexpected response (${response.status}). Check the Flask terminal.`);
  }
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
}

function showPage(page) {
  document.querySelectorAll(".page").forEach(section => section.classList.toggle("active", section.id === page));
  document.querySelectorAll(".nav-item").forEach(button => button.classList.toggle("active", button.dataset.page === page));
  const names = { overview: "Overview", migrations: "Migrations", history: "History", database: "Database" };
  $("pageTitle").textContent = names[page] || "Overview";
  $("crumb").textContent = (names[page] || "Overview").toUpperCase();
  if (page === "migrations") loadPatches();
  if (page === "history") loadHistory();
  if (page === "database") loadDatabase();
}

document.querySelectorAll(".nav-item").forEach(button => button.addEventListener("click", () => showPage(button.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(button => button.addEventListener("click", () => showPage(button.dataset.goto)));

function renderPipeline(data) {
  const items = [...data.applied, ...data.pending].slice(0, 6);
  $("pipeline").innerHTML = items.length ? items.map(item => {
    const pending = data.pending.some(p => p.version === item.version);
    return `<div class="pipe-row">
      <div class="pipe-dot ${pending ? "pending" : ""}">${pending ? "○" : "✓"}</div>
      <div class="pipe-main"><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.version)} · ${escapeHtml(item.filename)}</small></div>
      <span class="status-pill ${pending ? "pending" : ""}">${pending ? "PENDING" : "APPLIED"}</span>
    </div>`;
  }).join("") : '<div class="empty">No migration patches found.</div>';
}

function renderRecent(history) {
  $("recentActivity").innerHTML = history.length ? history.slice(0, 4).map(item => `
    <div class="activity-item"><div class="activity-icon">✓</div><div>
      <b>${escapeHtml(item.filename || `Migration ${item.version}`)}</b>
      <small>${escapeHtml(item.applied_at || "Applied")}</small>
    </div></div>`).join("") : '<div class="empty">No migrations have been applied yet.</div>';
}

async function refreshDashboard() {
  try {
    const data = await api("/api/dashboard");
    $("currentVersion").textContent = data.current_version;
    $("appliedCount").textContent = data.applied_count;
    $("pendingCount").textContent = data.pending_count;
    $("totalCount").textContent = data.total_patches;
    $("collectionCount").textContent = data.collections.length;
    $("navPending").textContent = data.pending_count;
    $("healthTitle").textContent = data.pending_count ? "Changes are waiting" : "Database is up to date";
    $("healthText").textContent = data.pending_count
      ? `${data.pending_count} pending migration(s). Run a dry-run before applying.`
      : "All available migrations have been applied successfully.";
    $("healthIcon").textContent = data.pending_count ? "◷" : "✓";
    $("healthIcon").classList.toggle("warning", data.pending_count > 0);
    renderPipeline(data);
    renderRecent(data.history);
    if ($("migrations").classList.contains("active")) loadPatches();
    if ($("history").classList.contains("active")) loadHistory();
    if ($("database").classList.contains("active")) loadDatabase();
  } catch (error) {
    toast(error.message, true);
    console.error(error);
  }
}

async function loadPatches() {
  try {
    const patches = await api("/api/patches");
    $("patchTable").innerHTML = patches.length ? patches.map(patch => `
      <tr data-search="${escapeHtml(`${patch.name} ${patch.filename} ${patch.version}`.toLowerCase())}">
        <td>${escapeHtml(patch.version)}</td>
        <td><b>${escapeHtml(patch.name)}</b><br><span class="mono">${escapeHtml(patch.filename)}</span></td>
        <td>${patch.operations.length} operation(s)</td>
        <td><span class="status-pill ${patch.status === "PENDING" ? "pending" : ""}">${patch.status}</span></td>
      </tr>`).join("") : '<tr><td colspan="4" class="empty-cell">No patches found.</td></tr>';
  } catch (error) {
    $("patchTable").innerHTML = `<tr><td colspan="4" class="empty-cell">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function loadHistory() {
  try {
    const history = await api("/api/history");
    $("historyTable").innerHTML = history.length ? history.map(item => `
      <tr><td>${escapeHtml(item.version)}</td><td>${escapeHtml(item.filename)}</td>
      <td>${escapeHtml(item.applied_at || "—")}</td><td><span class="status-pill">APPLIED</span></td></tr>`
    ).join("") : '<tr><td colspan="4" class="empty-cell">No migrations have been applied yet.</td></tr>';
  } catch (error) {
    $("historyTable").innerHTML = `<tr><td colspan="4" class="empty-cell">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function loadDatabase() {
  try {
    databaseCache = await api("/api/database");
    $("databaseJson").textContent = JSON.stringify(databaseCache, null, 4);
    const collections = Object.entries(databaseCache).filter(([, value]) => Array.isArray(value));
    $("collectionCards").innerHTML = collections.length ? collections.map(([name, rows]) => {
      const fields = [...new Set(rows.filter(row => row && typeof row === "object").flatMap(row => Object.keys(row)))];
      return `<article class="collection-card"><b>${escapeHtml(name)}</b><span>${rows.length} record(s)</span>
        <div class="field-chips">${fields.length ? fields.map(field => `<i>${escapeHtml(field)}</i>`).join("") : "<i>No fields yet</i>"}</div></article>`;
    }).join("") : '<div class="empty">No collections found.</div>';
  } catch (error) {
    $("databaseJson").textContent = error.message;
    $("collectionCards").innerHTML = "";
  }
}

$("refreshBtn").addEventListener("click", async () => {
  await refreshDashboard();
  toast("Dashboard refreshed.");
});

$("patchSearch").addEventListener("input", event => {
  const query = event.target.value.toLowerCase();
  document.querySelectorAll("#patchTable tr[data-search]").forEach(row => {
    row.style.display = row.dataset.search.includes(query) ? "" : "none";
  });
});

function askConfirmation(title, body, actionLabel, callback) {
  $("confirmTitle").textContent = title;
  $("confirmBody").textContent = body;
  $("confirmAction").textContent = actionLabel;
  pendingConfirmation = callback;
  $("confirmModal").classList.add("show");
}
function closeConfirmation() {
  $("confirmModal").classList.remove("show");
  pendingConfirmation = null;
}
$("closeConfirm").addEventListener("click", closeConfirmation);
$("cancelConfirm").addEventListener("click", closeConfirmation);
$("confirmAction").addEventListener("click", async () => {
  if (!pendingConfirmation) return;
  const action = pendingConfirmation;
  closeConfirmation();
  try { await action(); } catch (error) { toast(error.message, true); }
});

async function runDryRun() {
  if (role() !== "administrator") {
    toast("Choose Administrator role to run migration previews.", true);
    return;
  }
  const result = await api("/api/apply", {
    method: "POST",
    body: JSON.stringify({ role: role(), dry_run: true })
  });
  const count = (result.items || []).length;
  toast(result.message);
  if (count) {
    askConfirmation("Dry-run preview", `${count} migration(s) passed validation. No database files were changed. Close this preview?`, "Got it", async () => {});
  }
}

async function applyMigrations() {
  if (role() !== "administrator") {
    toast("Administrator access is required to apply migrations.", true);
    return;
  }
  askConfirmation("Apply pending migrations?", "This will update database/db.json. Run a dry-run first if you have not checked these changes.", "Apply migrations", async () => {
    const result = await api("/api/apply", {
      method: "POST",
      body: JSON.stringify({ role: role(), dry_run: false })
    });
    toast(result.message);
    await refreshDashboard();
  });
}

async function rollbackLatest() {
  if (role() !== "administrator") {
    toast("Administrator access is required to roll back migrations.", true);
    return;
  }
  askConfirmation("Roll back latest migration?", "The latest migration will be reversed using its rollback instructions. This changes database/db.json.", "Roll back", async () => {
    const result = await api("/api/rollback", {
      method: "POST",
      body: JSON.stringify({ role: role() })
    });
    toast(result.message);
    await refreshDashboard();
  });
}

$("applyTop").addEventListener("click", applyMigrations);
$("applyBtn").addEventListener("click", applyMigrations);
$("dryRunBtn").addEventListener("click", () => runDryRun().catch(error => toast(error.message, true)));
$("dryRunPage").addEventListener("click", () => runDryRun().catch(error => toast(error.message, true)));
$("rollbackBtn").addEventListener("click", rollbackLatest);

function openPatchModal() {
  if (role() !== "administrator") {
    toast("Administrator access is required to create migrations.", true);
    return;
  }
  $("patchModal").classList.add("show");
}
function closePatchModal() { $("patchModal").classList.remove("show"); }
$("newPatchBtn").addEventListener("click", openPatchModal);
$("closePatch").addEventListener("click", closePatchModal);
$("cancelPatch").addEventListener("click", closePatchModal);

$("savePatch").addEventListener("click", async () => {
  try {
    const payload = {
      role: role(),
      version: $("patchVersion").value.trim(),
      name: $("patchName").value.trim(),
      operations: JSON.parse($("forwardOps").value),
      rollback: JSON.parse($("rollbackOps").value)
    };
    const result = await api("/api/patches", { method: "POST", body: JSON.stringify(payload) });
    closePatchModal();
    toast(result.message);
    $("patchVersion").value = "";
    $("patchName").value = "";
    await refreshDashboard();
    await loadPatches();
  } catch (error) {
    toast(error instanceof SyntaxError ? "Check the JSON syntax in both operation boxes." : error.message, true);
  }
});

$("copyDb").addEventListener("click", async () => {
  try {
    if (!databaseCache) await loadDatabase();
    await navigator.clipboard.writeText(JSON.stringify(databaseCache, null, 4));
    toast("Database JSON copied to clipboard.");
  } catch (error) {
    toast("Could not copy JSON. Check browser clipboard permissions.", true);
  }
});

$("roleSelect").addEventListener("change", () => toast(`Role changed to ${role()}.`));

// First-visit guided tour. Completion is saved in this browser.
const tutorialSteps = [
  {
    symbol: "✦", label: "GETTING STARTED · 01", title: "Welcome to your migration workspace.",
    body: "SchemaMigrate helps you change your JSON database in a controlled, trackable way. This short tour shows you the essentials.",
    tip: "A migration is a versioned set of instructions that changes your database structure."
  },
  {
    symbol: "⇄", label: "MIGRATION LIBRARY · 02", title: "Every change starts with a patch.",
    body: "Open Migrations to see the numbered patch files. Each patch contains forward operations and rollback instructions.",
    tip: "Use Create migration to add a patch. Versions must be unique and contain at least three digits."
  },
  {
    symbol: "◷", label: "SAFE DEPLOYMENT · 03", title: "Preview before you apply.",
    body: "Run a dry-run to validate pending migrations without saving changes. When the preview succeeds, apply migrations to update the JSON database.",
    tip: "Apply and rollback actions require the Administrator role. Operator is intended for read-only review."
  },
  {
    symbol: "▤", label: "INSPECT & TRACK · 04", title: "Your database stays inspectable.",
    body: "History shows completed migrations. Database lets you inspect the current JSON data and collection fields.",
    tip: "This demo stores data locally in database/db.json and patch files in the patches folder. Back up these files regularly."
  }
];
let tutorialIndex = 0;
function renderTutorialStep() {
  const step = tutorialSteps[tutorialIndex];
  $("tutorialSymbol").textContent = step.symbol;
  $("tutorialStep").textContent = step.label;
  $("tutorialTitle").textContent = step.title;
  $("tutorialBody").textContent = step.body;
  $("tutorialTip").textContent = step.tip;
  $("tutorialCounter").textContent = `${tutorialIndex + 1} of ${tutorialSteps.length}`;
  $("tutorialProgress").style.width = `${((tutorialIndex + 1) / tutorialSteps.length) * 100}%`;
  $("nextTutorial").textContent = tutorialIndex === tutorialSteps.length - 1 ? "Start using SchemaMigrate ✓" : "Next step →";
}
function openTutorial() {
  tutorialIndex = 0;
  renderTutorialStep();
  $("tutorialModal").classList.add("show");
}
function finishTutorial() {
  $("tutorialModal").classList.remove("show");
  localStorage.setItem("schemamigrate_tutorial_done", "yes");
}
$("nextTutorial").addEventListener("click", () => {
  if (tutorialIndex < tutorialSteps.length - 1) {
    tutorialIndex += 1;
    renderTutorialStep();
  } else finishTutorial();
});
$("skipTutorial").addEventListener("click", finishTutorial);
$("closeTutorial").addEventListener("click", finishTutorial);
$("reopenTutorial").addEventListener("click", openTutorial);

refreshDashboard();
if (!localStorage.getItem("schemamigrate_tutorial_done")) openTutorial();
