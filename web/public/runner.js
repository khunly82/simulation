// Exécute du code Python dans un Web Worker avec délai maximal par test.
export class PyRunner {
  constructor(workerUrl = "worker.js", { testTimeout = 5000 } = {}) {
    this.workerUrl = workerUrl;
    this.timeout = testTimeout;
    this._spawn();
  }

  _spawn() {
    const worker = new Worker(this.workerUrl);
    this.worker = worker;
    this.ready = new Promise((resolve, reject) => {
      const onMsg = (e) => {
        if (e.data.type === "ready") {
          worker.removeEventListener("message", onMsg);
          resolve();
        } else if (e.data.type === "initerror") {
          reject(new Error(e.data.error));
        }
      };
      worker.addEventListener("message", onMsg);
      worker.addEventListener("error", (e) => reject(new Error(e.message || "Erreur du worker")), { once: true });
    });
    this.ready.catch(() => {}); // évite un "unhandled rejection" : l'appelant gère l'erreur
  }

  /** @returns {Promise<{results: object[], fatal: string|null}>} */
  async run(code, func, tests) {
    await this.ready;
    const worker = this.worker;
    const results = tests.map((t, i) => ({
      index: i, ok: false, args: t.args, expected: t.expected, got: null, error: null, out: "", ran: false,
    }));
    return new Promise((resolve) => {
      let timer;
      let current = -1;
      const finish = (fatal) => {
        clearTimeout(timer);
        worker.removeEventListener("message", onMsg);
        resolve({ results, fatal });
      };
      const arm = () => {
        clearTimeout(timer);
        timer = setTimeout(onTimeout, this.timeout);
      };
      const onTimeout = () => {
        worker.terminate(); // seul moyen d'arrêter une boucle infinie
        this._spawn();
        const seconds = this.timeout / 1000;
        if (current < 0) return finish(`Temps dépassé (> ${seconds} s) pendant l'exécution du code (boucle infinie ?)`);
        results[current].ran = true;
        results[current].error = `Temps dépassé (> ${seconds} s)`;
        finish(null);
      };
      const onMsg = (e) => {
        const m = e.data;
        if (m.type === "fatal") return finish(m.error);
        if (m.type === "started") {
          current = m.i;
          arm();
        } else if (m.type === "result") {
          Object.assign(results[m.i], { ran: true, ok: m.ok, got: m.got, error: m.error, out: m.out });
          arm();
        } else if (m.type === "done") {
          finish(null);
        }
      };
      worker.addEventListener("message", onMsg);
      arm();
      worker.postMessage({ type: "run", code, func, tests });
    });
  }
}
