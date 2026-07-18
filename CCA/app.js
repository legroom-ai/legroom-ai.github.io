/* AWS Certified AI Practitioner (AIF-C01) — practice tests (vanilla JS, no build step) */

const LS_KEY = "claude-arch-quiz-progress-v1";
const USER_KEY = "claude-arch-quiz-user-v1";
const MOCK = { count: 60, minutes: 78, pass: 70 }; // full-length timed Claude Architect mock exam

// ── Google Sign-In ──────────────────────────────────────────────────────────
// Paste your OAuth 2.0 Client ID below (see README.md). Until it is set, the app
// runs in guest mode and shows a small "Sign-in not configured" hint.
const GOOGLE_CLIENT_ID = "REPLACE_WITH_YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";
const AUTH_CONFIGURED =
  /\.apps\.googleusercontent\.com$/.test(GOOGLE_CLIENT_ID) &&
  !GOOGLE_CLIENT_ID.startsWith("REPLACE_WITH_");

const state = {
  all: [],          // every question
  view: [],         // questions currently in play
  idx: 0,
  mode: "practice",
  user: null,             // { sub, name, email, picture } when signed in
  // practice/exam progress, persisted; keyed by question id: { selected:[], checked, correct }
  records: {},
  // in-memory record set for the active mock attempt (not persisted)
  mockRecords: {},
  mock: { active: false, submitted: false, endTime: 0, durationS: 0 },
  timer: null,
};

const $ = (id) => document.getElementById(id);
const LETTERS = ["A", "B", "C", "D", "E", "F"];

async function load() {
  try {
    const res = await fetch("data/questions.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.all = data.map((q, i) => ({ ...q, id: q.id ?? i + 1 }));
  } catch (e) {
    $("q-text").textContent = "Could not load questions.json — " + e.message;
    $("foot-status").textContent = "Load error";
    return;
  }
  migrateLegacyProgress();
  restoreUser();
  restore();
  buildTestFilter();
  buildCategoryFilter();
  state.mode = $("mode-select").value;
  applyFilter();
  wire();
  initAuth();
  renderAuthUI();
  $("foot-status").textContent = `${state.all.length} questions loaded`;
}

/* ---- per-user progress storage ---- */
function userKey() { return LS_KEY + "::" + (state.user ? state.user.sub : "guest"); }

function migrateLegacyProgress() {
  // Early builds stored guest progress under the bare LS_KEY — preserve it.
  const guestKey = LS_KEY + "::guest";
  const legacy = localStorage.getItem(LS_KEY);
  if (legacy && !localStorage.getItem(guestKey)) localStorage.setItem(guestKey, legacy);
}

function restore() {
  try {
    const saved = JSON.parse(localStorage.getItem(userKey()) || "{}");
    state.records = (saved && saved.records) ? saved.records : {};
  } catch { state.records = {}; }
}
function persist() {
  if (state.mock.active) return; // mock attempts are ephemeral
  localStorage.setItem(userKey(), JSON.stringify({ records: state.records }));
}

function restoreUser() {
  try {
    const u = JSON.parse(localStorage.getItem(USER_KEY) || "null");
    if (u && u.sub) state.user = u;
  } catch { /* ignore */ }
}

/* ---- Google Identity Services ---- */
function decodeJwt(token) {
  const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  const json = decodeURIComponent(
    atob(b64).split("").map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0")).join("")
  );
  return JSON.parse(json);
}

function onCredential(resp) {
  try {
    const p = decodeJwt(resp.credential);
    state.user = { sub: p.sub, name: p.name || p.email || "User", email: p.email || "", picture: p.picture || "" };
    localStorage.setItem(USER_KEY, JSON.stringify(state.user));
    afterIdentityChange();
  } catch (e) { console.error("Google sign-in failed:", e); }
}

function signOut() {
  if (AUTH_CONFIGURED && window.google?.accounts?.id) {
    try { google.accounts.id.disableAutoSelect(); } catch { /* ignore */ }
  }
  state.user = null;
  localStorage.removeItem(USER_KEY);
  afterIdentityChange();
}

// Switch the active progress namespace and reset transient UI when the user changes.
function afterIdentityChange() {
  leaveMock();
  restore();
  renderAuthUI();
  if (state.mode === "mock") showMockStart();
  else applyFilter();
}

let gisTries = 0;
function initAuth() {
  if (!AUTH_CONFIGURED) return; // guest-only; hint shown by renderAuthUI()
  if (!(window.google && google.accounts && google.accounts.id)) {
    if (gisTries++ < 40) setTimeout(initAuth, 150); // wait for async GIS script
    return;
  }
  google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: onCredential, auto_select: false });
  if (!state.user) renderGisButton();
}
function renderGisButton() {
  const el = $("g-signin");
  if (!el || !(window.google && google.accounts && google.accounts.id)) return;
  el.innerHTML = "";
  google.accounts.id.renderButton(el, { theme: "filled_black", size: "medium", type: "standard", shape: "pill", text: "signin_with" });
}

function renderAuthUI() {
  const chip = $("user-chip"), gbtn = $("g-signin"), hint = $("auth-hint");
  if (state.user) {
    chip.hidden = false; gbtn.hidden = true; hint.hidden = true;
    $("user-name").textContent = state.user.name;
    const av = $("user-avatar");
    if (state.user.picture) { av.src = state.user.picture; av.hidden = false; } else { av.hidden = true; }
  } else {
    chip.hidden = true;
    if (AUTH_CONFIGURED) { gbtn.hidden = false; hint.hidden = true; renderGisButton(); }
    else { gbtn.hidden = true; hint.hidden = false; hint.textContent = "Sign-in not configured"; }
  }
}

/* ---- record access (practice/exam vs mock) ---- */
function records() { return state.mock.active ? state.mockRecords : state.records; }
function recOf(q) {
  const m = records();
  if (!m[q.id]) m[q.id] = { selected: [], checked: false, correct: false };
  return m[q.id];
}
function revealed(q) {
  if (state.mode === "practice") return recOf(q).checked;
  if (state.mode === "mock") return state.mock.submitted;
  return false; // exam: only the summary box, no per-question reveal until submit handled elsewhere
}

function buildCategoryFilter() {
  const cats = Array.from(new Set(state.all.map((q) => q.category))).sort();
  const sel = $("category-filter");
  sel.innerHTML = `<option value="__all">All categories (${state.all.length})</option>`;
  for (const c of cats) {
    const n = state.all.filter((q) => q.category === c).length;
    const o = document.createElement("option");
    o.value = c; o.textContent = `${c} (${n})`;
    sel.appendChild(o);
  }
}

function buildTestFilter() {
  const sel = $("test-filter");
  const tests = Array.from(new Set(state.all.map((q) => q.test))).sort((a, b) => a - b);
  sel.innerHTML = `<option value="__all">All tests (${state.all.length})</option>`;
  for (const t of tests) {
    const n = state.all.filter((q) => q.test === t).length;
    const o = document.createElement("option");
    o.value = String(t); o.textContent = `Practice Test ${t} (${n})`;
    sel.appendChild(o);
  }
}

function applyFilter() {
  const cat = $("category-filter").value || "__all";
  const test = $("test-filter").value || "__all";
  state.view = state.all.filter((q) =>
    (cat === "__all" || q.category === cat) &&
    (test === "__all" || String(q.test) === test));
  state.idx = 0;
  $("exam-result").hidden = true;
  render();
}

function shuffle() {
  shuffleInPlace(state.view);
  state.idx = 0;
  render();
}
function shuffleInPlace(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function current() { return state.view[state.idx]; }

function arraysEqual(a, b) {
  if (a.length !== b.length) return false;
  const s = [...a].sort(), t = [...b].sort();
  return s.every((v, i) => v === t[i]);
}

/* ============================ RENDER ============================ */
function render() {
  const q = current();
  if (!q) return;
  const rec = recOf(q);
  const multi = q.type === "multiple" || (q.correct && q.correct.length > 1);
  const isRev = revealed(q);

  $("q-category").textContent = q.category;
  $("q-index").textContent = `Question ${state.idx + 1} of ${state.view.length}`;
  $("q-text").textContent = q.question;
  $("q-hint").textContent = multi ? `Select ${q.correct.length}.` : "";

  const form = $("options-form");
  form.innerHTML = "";
  q.options.forEach((opt, i) => {
    const label = document.createElement("label");
    label.className = "option";
    const input = document.createElement("input");
    input.type = multi ? "checkbox" : "radio";
    input.name = "opt";
    input.value = String(i);
    input.checked = rec.selected.includes(i);
    if (isRev) { input.disabled = true; label.classList.add("disabled"); }
    input.addEventListener("change", () => onSelect(i, multi));

    const letter = document.createElement("span");
    letter.className = "opt-letter";
    letter.textContent = LETTERS[i];
    const text = document.createElement("span");
    text.textContent = opt;
    label.append(input, letter, text);

    if (isRev) {
      if (q.correct.includes(i)) label.classList.add("correct");
      else if (rec.selected.includes(i)) label.classList.add("wrong");
    }
    form.appendChild(label);
  });

  const fb = $("feedback");
  if (isRev) {
    fb.hidden = false;
    fb.className = "feedback " + (rec.correct ? "right" : "wrong");
    fb.innerHTML = `<span class="verdict">${rec.correct ? "✓ Correct" : "✗ Incorrect"}</span>
      <span class="explain">${escapeHtml(q.explanation || "")}</span>`;
  } else {
    fb.hidden = true;
  }

  // primary button label/behavior depends on mode
  const checkBtn = $("check-btn");
  if (state.mode === "mock") {
    if (state.mock.submitted) { checkBtn.textContent = "Exam submitted"; checkBtn.disabled = true; }
    else { checkBtn.textContent = "Submit exam"; checkBtn.disabled = false; }
  } else if (state.mode === "exam") {
    checkBtn.textContent = "Submit exam"; checkBtn.disabled = false;
  } else {
    checkBtn.textContent = isRev ? "Checked" : "Check answer";
    checkBtn.disabled = isRev || rec.selected.length === 0;
  }

  $("prev-btn").disabled = state.idx === 0;
  $("next-btn").disabled = state.idx === state.view.length - 1;

  updateStats();
  updateProgress();
  buildNav();
}

function onSelect(i, multi) {
  const q = current();
  const rec = recOf(q);
  if (revealed(q)) return;
  if (multi) {
    rec.selected = rec.selected.includes(i)
      ? rec.selected.filter((x) => x !== i)
      : [...rec.selected, i];
  } else {
    rec.selected = [i];
  }
  persist();
  if (state.mode === "practice") $("check-btn").disabled = rec.selected.length === 0;
  updateStats(); updateProgress(); buildNav();
}

function check() {
  const q = current();
  const rec = recOf(q);
  if (rec.selected.length === 0) return;
  rec.checked = true;
  rec.correct = arraysEqual(rec.selected, q.correct);
  persist();
  render();
}

function go(delta) {
  const ni = state.idx + delta;
  if (ni < 0 || ni >= state.view.length) return;
  state.idx = ni;
  render();
}

function updateStats() {
  const recs = Object.values(records());
  const checked = recs.filter((r) => r.checked);
  const correct = checked.filter((r) => r.correct).length;
  let answered = checked.length;
  if (state.mock.active && !state.mock.submitted) {
    answered = recs.filter((r) => r.selected.length > 0).length;
  }
  $("stat-answered").textContent = answered;
  $("stat-correct").textContent = correct;
  $("stat-accuracy").textContent = checked.length ? Math.round((correct / checked.length) * 100) + "%" : "—";
}

function updateProgress() {
  let done;
  if (state.mock.active && !state.mock.submitted) {
    done = state.view.filter((q) => recOf(q).selected.length > 0).length;
  } else {
    done = state.view.filter((q) => records()[q.id]?.checked).length;
  }
  const pct = state.view.length ? (done / state.view.length) * 100 : 0;
  $("progress-fill").style.width = pct + "%";
  $("progress-text").textContent = `${done} / ${state.view.length}`;
}

function buildNav() {
  const grid = $("nav-grid");
  grid.innerHTML = "";
  state.view.forEach((q, i) => {
    const b = document.createElement("button");
    b.textContent = i + 1;
    const rec = records()[q.id];
    if (i === state.idx) b.classList.add("current");
    else if (revealed(q) && rec?.checked) b.classList.add(rec.correct ? "correct" : "wrong");
    else if (rec?.selected?.length) b.classList.add("answered");
    b.addEventListener("click", () => { state.idx = i; render(); });
    grid.appendChild(b);
  });
}

/* ============================ EXAM (untimed, current view) ============================ */
function gradeExam() {
  const total = state.view.length;
  let answered = 0, correct = 0;
  state.view.forEach((q) => {
    const rec = recOf(q);
    rec.checked = true;
    rec.correct = arraysEqual(rec.selected, q.correct);
    if (rec.selected.length) answered++;
    if (rec.correct) correct++;
  });
  persist();
  const pct = total ? Math.round((correct / total) * 100) : 0;
  const pass = pct >= 70;
  const box = $("exam-result");
  box.hidden = false;
  box.innerHTML = `<h2>Exam results</h2>
    <p class="score-big">${pct}%</p>
    <p>${correct} / ${total} correct · ${answered} answered ·
       <strong style="color:${pass ? "var(--green)" : "var(--red)"}">${pass ? "PASS" : "BELOW PASS"}</strong>
       (passing ≈ 70%)</p>
    <p style="color:var(--muted)">Switch back to Practice mode to review explanations per question.</p>`;
  box.scrollIntoView({ behavior: "smooth" });
  render();
}

/* ============================ MOCK (timed, full-length) ============================ */
function sampleMock(count) {
  const cats = Array.from(new Set(state.all.map((q) => q.category)));
  const per = Math.floor(count / cats.length);
  const remainder = count - per * cats.length;
  const extraCats = new Set(shuffleInPlace([...cats]).slice(0, remainder));
  let picked = [];
  for (const c of cats) {
    const pool = shuffleInPlace(state.all.filter((q) => q.category === c));
    const take = per + (extraCats.has(c) ? 1 : 0);
    picked = picked.concat(pool.slice(0, take));
  }
  return shuffleInPlace(picked).slice(0, count);
}

function showMockStart() {
  stopTimer();
  state.mock.active = false;
  state.mock.submitted = false;
  $("timer").hidden = true;
  $("exam-result").hidden = true;
  $("main").hidden = true;
  $("mock-start").hidden = false;
  setControlsDisabled(false);
}

function startMock() {
  state.mockRecords = {};
  state.view = sampleMock(MOCK.count);
  state.idx = 0;
  state.mock.active = true;
  state.mock.submitted = false;
  state.mock.durationS = MOCK.minutes * 60;
  state.mock.endTime = Date.now() + state.mock.durationS * 1000;

  $("mock-start").hidden = true;
  $("main").hidden = false;
  $("exam-result").hidden = true;
  $("timer").hidden = false;
  setControlsDisabled(true);
  startTimer();
  render();
}

function startTimer() {
  stopTimer();
  tick();
  state.timer = setInterval(tick, 250);
}
function stopTimer() {
  if (state.timer) { clearInterval(state.timer); state.timer = null; }
}
function tick() {
  const ms = state.mock.endTime - Date.now();
  if (ms <= 0) { updateTimer(0); finishMock(true); return; }
  updateTimer(ms);
}
function updateTimer(ms) {
  const total = Math.max(0, Math.round(ms / 1000));
  const m = Math.floor(total / 60), s = total % 60;
  $("timer-num").textContent = `${m}:${String(s).padStart(2, "0")}`;
  $("timer").classList.toggle("warn", total <= 300); // last 5 minutes
}

function finishMock(auto) {
  stopTimer();
  state.mock.submitted = true;
  const total = state.view.length;
  let answered = 0, correct = 0;
  const byCat = {};
  state.view.forEach((q) => {
    const rec = recOf(q);
    rec.checked = true;
    rec.correct = arraysEqual(rec.selected, q.correct);
    if (rec.selected.length) answered++;
    if (rec.correct) correct++;
    const c = (byCat[q.category] ||= { total: 0, correct: 0 });
    c.total++; if (rec.correct) c.correct++;
  });
  const pct = total ? Math.round((correct / total) * 100) : 0;
  const pass = pct >= MOCK.pass;
  const usedS = state.mock.durationS - Math.max(0, Math.round((state.mock.endTime - Date.now()) / 1000));
  const usedM = Math.floor(usedS / 60), usedSec = usedS % 60;

  const rows = Object.entries(byCat).sort((a, b) => a[0].localeCompare(b[0])).map(([cat, c]) => {
    const p = Math.round((c.correct / c.total) * 100);
    return `<tr>
      <td>${escapeHtml(cat)}</td>
      <td class="num">${c.correct}/${c.total}</td>
      <td><div class="bar-mini"><i style="width:${p}%"></i></div></td>
      <td class="num">${p}%</td>
    </tr>`;
  }).join("");

  const box = $("exam-result");
  box.hidden = false;
  box.innerHTML = `<h2>Mock exam results${auto ? " — time expired" : ""}</h2>
    <p class="score-big" style="color:${pass ? "var(--green)" : "var(--red)"}">${pct}%</p>
    <p>${correct} / ${total} correct · ${answered} answered · time used ${usedM}:${String(usedSec).padStart(2, "0")} ·
       <strong style="color:${pass ? "var(--green)" : "var(--red)"}">${pass ? "PASS" : "FAIL"}</strong>
       (passing ≈ ${MOCK.pass}%)</p>
    <table class="breakdown">
      <thead><tr><th>Domain</th><th class="num">Score</th><th></th><th class="num">%</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="result-actions">
      <button class="btn" id="review-btn">Review answers</button>
      <button class="btn primary" id="retake-btn">New mock exam</button>
    </div>
    <p style="color:var(--muted)">Reviewing shows the correct answer and explanation for every question via the navigator.</p>`;
  $("review-btn").addEventListener("click", () => { state.idx = 0; render(); $("main").scrollIntoView({ behavior: "smooth" }); });
  $("retake-btn").addEventListener("click", () => showMockStart());
  $("timer").classList.remove("warn");
  setControlsDisabled(false, /*keepFilterLocked*/ true);
  box.scrollIntoView({ behavior: "smooth" });
  render();
}

function setControlsDisabled(disabled, keepModeFree) {
  $("test-filter").disabled = disabled;
  $("category-filter").disabled = disabled;
  $("shuffle-btn").disabled = disabled;
  $("reset-btn").disabled = disabled;
  $("mode-select").disabled = keepModeFree ? false : disabled;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ============================ WIRING ============================ */
function wire() {
  $("check-btn").addEventListener("click", () => {
    if (state.mode === "mock") { if (state.mock.active && !state.mock.submitted) finishMock(false); }
    else if (state.mode === "exam") gradeExam();
    else check();
  });
  $("prev-btn").addEventListener("click", () => go(-1));
  $("next-btn").addEventListener("click", () => go(1));
  $("shuffle-btn").addEventListener("click", shuffle);
  $("category-filter").addEventListener("change", applyFilter);
  $("test-filter").addEventListener("change", applyFilter);
  $("start-mock-btn").addEventListener("click", startMock);
  $("signout-btn").addEventListener("click", signOut);

  $("mode-select").addEventListener("change", (e) => {
    leaveMock();
    state.mode = e.target.value;
    $("exam-result").hidden = true;
    if (state.mode === "mock") {
      showMockStart();
    } else {
      $("mock-start").hidden = true;
      $("main").hidden = false;
      applyFilter();
    }
  });

  $("reset-btn").addEventListener("click", () => {
    const who = state.user ? state.user.name : "guest";
    if (!confirm(`Reset saved practice progress for ${who}?`)) return;
    state.records = {};
    persist();
    state.idx = 0;
    render();
  });

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "SELECT") return;
    if ($("main").hidden) return; // mock start screen
    if (e.key === "ArrowLeft") go(-1);
    if (e.key === "ArrowRight") go(1);
    if (e.key === "Enter" && state.mode !== "mock") $("check-btn").click();
    if (["1", "2", "3", "4", "5", "6"].includes(e.key)) {
      const i = +e.key - 1;
      const q = current();
      if (q && i < q.options.length && !revealed(q)) {
        onSelect(i, q.type === "multiple" || q.correct.length > 1);
        render();
      }
    }
  });
}

function leaveMock() {
  stopTimer();
  state.mock.active = false;
  state.mock.submitted = false;
  state.mockRecords = {};
  $("timer").hidden = true;
  $("timer").classList.remove("warn");
  setControlsDisabled(false);
}

load();
