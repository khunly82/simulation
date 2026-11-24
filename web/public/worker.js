// Web Worker : charge Pyodide (Python 3.12 en WebAssembly) et exécute le code du candidat.
// Un worker bloqué (boucle infinie) est simplement terminé par le thread principal.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let harness = null;

(async () => {
  try {
    const py = await loadPyodide();
    const src = await (await fetch("harness.py", { cache: "no-cache" })).text();
    py.runPython(src);
    harness = { prepare: py.globals.get("prepare"), runOne: py.globals.get("run_one") };
    postMessage({ type: "ready" });
  } catch (err) {
    postMessage({ type: "initerror", error: String(err) });
  }
})();

onmessage = (e) => {
  const { code, func, tests } = e.data;
  if (!harness) return postMessage({ type: "fatal", error: "Python n'est pas encore chargé." });
  const prep = JSON.parse(harness.prepare(code, func));
  if (prep.fatal) return postMessage({ type: "fatal", error: prep.fatal });
  for (let i = 0; i < tests.length; i++) {
    postMessage({ type: "started", i });
    const r = JSON.parse(harness.runOne(JSON.stringify(tests[i].args), tests[i].expected));
    postMessage({ type: "result", i, ...r });
  }
  postMessage({ type: "done" });
};
