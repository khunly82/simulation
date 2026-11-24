import { PyRunner } from "./runner.js";
import { Session, pickQuestions, mulberry32, EXAM_SECONDS, TIER_PLAN } from "./session.js";

const $ = (id) => document.getElementById(id);
const TIER_LABEL = { easy: "Facile", medium: "Moyen", hard: "Difficile" };
const KEY_SESSION = "sim.session.v1";
const KEY_REPORT = "sim.report.v1";

const params = new URLSearchParams(location.search);
const DURATION = params.has("minutes") ? Math.round(Number(params.get("minutes")) * 60) : EXAM_SECONDS;
const rng = params.has("seed") ? mulberry32(Number(params.get("seed"))) : Math.random;

let bank = [];
let runner = null;
let session = null;
let timerId = null;
let busy = false;
let report = null;

// ----------------------------------------------------------------- utilitaires
const store = {
  get(key) { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* stockage indisponible */ } },
  del(key) { try { localStorage.removeItem(key); } catch { /* ignore */ } },
};

function show(id) {
  for (const el of document.querySelectorAll(".screen")) el.hidden = el.id !== id;
}

function fmtClock(seconds) {
  const s = Math.ceil(seconds);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  for (const c of children) node.append(c);
  return node;
}

function confirmDialog(message, okLabel = "Confirmer") {
  return new Promise((resolve) => {
    const dlg = $("dlg");
    const done = (value) => {
      dlg.close();
      resolve(value);
    };
    $("dlg-msg").textContent = message;
    $("dlg-ok").textContent = okLabel;
    $("dlg-ok").onclick = () => done(true);
    $("dlg-cancel").onclick = () => done(false);
    dlg.oncancel = () => resolve(false); // touche Échap (le navigateur ferme le dialogue)
    dlg.showModal();
  });
}

function persist() {
  if (session) store.set(KEY_SESSION, { ...session.toJSON(), draft: $("code").value });
}

// ----------------------------------------------------------------- éditeur
const code = $("code");

function updateGutter() {
  const n = code.value.split("\n").length;
  $("gutter").textContent = Array.from({ length: n }, (_, i) => i + 1).join("\n");
  $("gutter").scrollTop = code.scrollTop;
}

function insertText(text) {
  code.focus();
  if (!document.execCommand("insertText", false, text)) code.setRangeText(text, code.selectionStart, code.selectionEnd, "end");
}

code.addEventListener("input", () => { updateGutter(); schedulePersist(); });
code.addEventListener("scroll", () => { $("gutter").scrollTop = code.scrollTop; });
code.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); runSamples(); return; }
  if (e.key === "Tab" && !e.shiftKey) { e.preventDefault(); insertText("    "); return; }
  if (e.key === "Enter" && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    e.preventDefault();
    const before = code.value.slice(0, code.selectionStart);
    const line = before.slice(before.lastIndexOf("\n") + 1);
    let indent = line.match(/^ */)[0];
    if (line.trimEnd().endsWith(":")) indent += "    ";
    insertText("\n" + indent);
  }
});

let persistTimer = null;
function schedulePersist() {
  clearTimeout(persistTimer);
  persistTimer = setTimeout(persist, 800);
}

function setCode(text) {
  code.value = text;
  code.scrollTop = 0;
  updateGutter();
}

// ----------------------------------------------------------------- accueil
function renderRules() {
  const total = TIER_PLAN.reduce((s, [, n]) => s + n, 0);
  const rules = [
    `${total} questions tirées au sort (2 faciles, 2 moyennes, 1 difficile).`,
    `${Math.round(DURATION / 60)} minutes au total, un seul chronomètre pour l'ensemble du test.`,
    "Les tests d'exemple sont exécutables autant de fois que vous voulez : ils ne couvrent qu'une partie des cas.",
    "Votre solution sera corrigée à la fin sur tous les cas, y compris des cas cachés (cas limites).",
    "Une fois passé à la question suivante, il est impossible de revenir en arrière.",
    "Le test s'arrête automatiquement quand le temps est écoulé : le code en cours est alors conservé.",
    "Python uniquement, bibliothèque standard ; les valeurs retournées sont comparées sous forme de texte.",
    "Recharger la page ne remet pas le chrono à zéro.",
  ];
  const ul = $("rules");
  ul.replaceChildren(...rules.map((r) => el("li", { textContent: r })));
}

function enterStart() {
  show("screen-start");
  renderRules();
  $("name").focus();
}

$("start-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = $("name").value.trim();
  if (!name) return;
  session = new Session({ candidate: name, questions: pickQuestions(bank, rng), duration: DURATION });
  report = null;
  store.del(KEY_REPORT);
  enterExam();
  persist();
});

// ----------------------------------------------------------------- examen
function enterExam(draft = null) {
  show("screen-exam");
  loadQuestion(draft);
  clearInterval(timerId);
  timerId = setInterval(tick, 250);
  tick();
}

function loadQuestion(draft = null) {
  const q = session.current;
  $("q-label").textContent = `Question ${session.index + 1} / ${session.questions.length} · ${TIER_LABEL[q.tier]}`;
  const st = $("statement");
  const nSamples = session.sampleTests().length;
  const parts = [
    el("h2", { textContent: q.title }),
    el("p", {}, "Fonction à écrire : ", el("code", { textContent: `${q.func}(${q.params})` })),
    ...q.statement.split("\n").map((t) => el("p", { textContent: t })),
  ];
  if (q.note) parts.push(el("p", { className: "note", textContent: `Note : ${q.note}` }));
  parts.push(el("p", { className: "note", textContent:
    `${nSamples} tests d'exemple sont exécutables ; d'autres cas, cachés, seront évalués à la fin.` }));
  st.replaceChildren(...parts);
  st.scrollTop = 0;
  setCode(draft ?? q.starter);
  $("output").replaceChildren(el("span", { className: "dim", textContent: "Les résultats des tests d'exemple s'afficheront ici." }));
  $("btn-next").textContent = session.isLast ? "Terminer le test ✔" : "Valider et question suivante ▶";
  setBusy(false);
  code.focus();
}

function tick() {
  if (!session || session.finished) return;
  const rem = session.remaining();
  $("timer").textContent = fmtClock(rem);
  $("timer").classList.toggle("low", rem < 300);
  if (rem <= 0) endExam();
}

function setBusy(b) {
  busy = b;
  $("btn-run").disabled = b;
  $("btn-next").disabled = b;
}

function renderRun(rep, func) {
  const out = $("output");
  const nodes = [];
  const add = (cls, text) => nodes.push(el("span", { className: cls, textContent: text }));
  if (rep.fatal) {
    add("fail", "Erreur :\n" + rep.fatal + "\n");
  } else {
    const passed = rep.results.filter((r) => r.ok).length;
    nodes.push(el("b", { className: passed === rep.results.length ? "ok" : "fail",
      textContent: `${passed} / ${rep.results.length} tests d'exemple réussis\n\n` }));
    for (const r of rep.results) {
      let args = r.args.map((a) => JSON.stringify(a)).join(", ");
      if (args.length > 90) args = args.slice(0, 87) + "...";
      const head = `Test ${r.index + 1} : ${func}(${args})\n`;
      if (!r.ran) add("dim", "⏭  " + head + "    non exécuté\n");
      else if (r.ok) add("ok", "✔  " + head);
      else {
        add("fail", "✘  " + head);
        add("", `    attendu : ${JSON.stringify(r.expected)}\n`);
        if (r.error) add("fail", "    " + r.error.trim().replace(/\n/g, "\n    ") + "\n");
        else add("", `    obtenu  : ${r.got}\n`);
      }
      if (r.out) add("dim", "    sortie standard : " + r.out.trimEnd().replace(/\n/g, "\n      ") + "\n");
    }
    if (passed === rep.results.length)
      add("dim", "\nVos cas d'exemple passent. Pensez aux cas limites : d'autres tests seront évalués à la fin.\n");
  }
  out.replaceChildren(...nodes);
}

async function runSamples() {
  if (busy || !session || session.finished) return;
  setBusy(true);
  $("btn-run").textContent = "Exécution…";
  const idx = session.index;
  const q = session.current;
  try {
    const rep = await runner.run(code.value, q.func, session.sampleTests());
    if (session.index === idx && !session.finished) renderRun(rep, q.func);
  } catch (err) {
    $("output").replaceChildren(el("span", { className: "fail", textContent: `Erreur interne : ${err.message}` }));
  } finally {
    $("btn-run").textContent = "▶ Exécuter les tests d'exemple";
    if (!session.finished) setBusy(false);
  }
}

async function next() {
  if (busy) return;
  const msg = session.isLast
    ? "Terminer le test ? Vous ne pourrez plus modifier vos réponses."
    : "Passer à la question suivante ? Vous ne pourrez plus revenir à celle-ci.";
  if (!(await confirmDialog(msg))) return;
  if (session.finished) return; // le chrono a expiré pendant la confirmation
  if (session.expired()) return endExam();
  if (session.submit(code.value)) {
    persist();
    loadQuestion();
  } else {
    endExam();
  }
}

async function endExam() {
  if (!session.finished) session.finish(code.value);
  clearInterval(timerId);
  persist();
  show("screen-grading");
  await gradeAndShow();
}

async function gradeAndShow() {
  try {
    await runner.ready;
    report = await session.grade(runner);
  } catch (err) {
    alert(`Erreur de correction : ${err.message}`);
    return;
  }
  report.savedPath = await saveOnServer(report);
  store.set(KEY_REPORT, report);
  showResult();
}

async function saveOnServer(rep) {
  try {
    const res = await fetch("/api/results", { method: "POST", body: JSON.stringify(rep) });
    if (res.ok) return (await res.json()).path;
  } catch { /* serveur statique sans API */ }
  return null;
}

function showResult() {
  show("screen-result");
  $("res-sub").textContent = `${report.candidate} — ${fmtClock(report.secondsUsed)} utilisées sur ${fmtClock(session.duration)}`;
  $("res-score").textContent = `Score global : ${Math.round(report.score)} %`;
  $("res-rows").replaceChildren(...report.grades.map((g, i) => {
    let state = "✔ réussie", cls = "ok";
    if (i >= report.answered && report.codes[i] === null) { state = "non atteinte"; cls = "fail"; }
    else if (g.fatal) { state = "erreur de code"; cls = "fail"; }
    else if (g.passed !== g.total) { state = g.passed ? "✘ partielle" : "✘ échec"; cls = "fail"; }
    return el("tr", {}, el("td", { textContent: `${i + 1}. ${g.title}` }), el("td", { textContent: TIER_LABEL[g.tier] }),
      el("td", { textContent: `${g.passed} / ${g.total}` }), el("td", { className: cls, textContent: state }));
  }));
  $("res-saved").textContent = report.savedPath
    ? `Rapport enregistré dans : ${report.savedPath}`
    : "Rapport non enregistré sur disque (serveur statique) : utilisez le bouton de téléchargement.";
}

$("btn-run").addEventListener("click", runSamples);
$("btn-next").addEventListener("click", next);
$("btn-new").addEventListener("click", () => {
  store.del(KEY_SESSION);
  store.del(KEY_REPORT);
  session = null;
  report = null;
  $("name").value = "";
  enterStart();
});
$("btn-download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(report, null, 1)], { type: "application/json" });
  const a = el("a", { href: URL.createObjectURL(blob), download: `resultat_${report.candidate.replace(/\W+/g, "_")}.json` });
  a.click();
  URL.revokeObjectURL(a.href);
});
window.addEventListener("beforeunload", (e) => {
  if (session && !session.finished) { e.preventDefault(); e.returnValue = ""; }
});

// ----------------------------------------------------------------- démarrage
async function init() {
  try {
    bank = (await (await fetch("bank.json", { cache: "no-cache" })).json()).questions;
  } catch (err) {
    document.body.textContent = `Impossible de charger la banque de questions : ${err.message}`;
    return;
  }
  runner = new PyRunner("worker.js");
  window.__sim = { runner, get session() { return session; } }; // utile au débogage / aux tests

  const saved = store.get(KEY_SESSION);
  if (saved) {
    try {
      session = Session.restore(saved, bank);
    } catch {
      store.del(KEY_SESSION);
    }
  }
  if (session) {
    if (session.finished) {
      report = store.get(KEY_REPORT);
      if (report) return showResult();
      show("screen-grading");
      return gradeAndShow();
    }
    if (session.expired()) { setCode(saved.draft ?? ""); return endExam(); }
    return enterExam(saved.draft ?? null);
  }

  enterStart();
  try {
    await runner.ready;
    $("py-status").textContent = "Python est prêt.";
    $("btn-start").disabled = false;
  } catch (err) {
    $("py-status").textContent = `Impossible de charger Python (connexion internet requise la première fois) : ${err.message}`;
  }
}

init();
