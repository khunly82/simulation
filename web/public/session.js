// Logique d'une session d'examen (sans DOM) : tirage, chrono, pas de retour arrière, correction.
export const EXAM_SECONDS = 50 * 60;
// 2 faciles, 2 moyennes, 1 difficile, présentées dans cet ordre.
export const TIER_PLAN = [["easy", 2], ["medium", 2], ["hard", 1]];

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function pickQuestions(bank, rng = Math.random) {
  const out = [];
  for (const [tier, n] of TIER_PLAN) {
    const pool = bank.filter((q) => q.tier === tier);
    for (let i = pool.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [pool[i], pool[j]] = [pool[j], pool[i]];
    }
    out.push(...pool.slice(0, n));
  }
  return out;
}

export class Session {
  constructor({ candidate, questions, duration = EXAM_SECONDS, now = Date.now, startedAt, index = 0,
                codes, finished = false, endedAt = null }) {
    this.candidate = candidate;
    this.questions = questions;
    this.duration = duration;
    this._now = now;
    this.startedAt = startedAt ?? now();
    this.index = index;
    this.codes = codes ?? questions.map(() => null);
    this.finished = finished;
    this.endedAt = endedAt;
  }

  get current() { return this.questions[this.index]; }
  get isLast() { return this.index === this.questions.length - 1; }
  remaining() { return Math.max(0, this.duration - (this._now() - this.startedAt) / 1000); }
  expired() { return this.remaining() <= 0; }
  sampleTests() { return this.current.tests.filter((t) => t.sample); }

  /** Fige la réponse courante et passe à la suivante. false si c'était la dernière. */
  submit(code) {
    if (this.finished) throw new Error("Le test est terminé.");
    this.codes[this.index] = code;
    if (this.isLast) {
      this.finish();
      return false;
    }
    this.index += 1;
    return true;
  }

  /** Termine le test (dernière question ou temps écoulé : le code en cours est conservé). */
  finish(currentCode = null) {
    if (this.finished) return;
    if (currentCode !== null && this.codes[this.index] === null) this.codes[this.index] = currentCode;
    this.finished = true;
    this.endedAt = this._now();
  }

  /** Correction finale sur tous les tests (exemples + cachés). */
  async grade(runner) {
    if (!this.finished) throw new Error("Le test n'est pas terminé.");
    const grades = [];
    for (let i = 0; i < this.questions.length; i++) {
      const q = this.questions[i];
      const code = this.codes[i];
      const total = q.tests.length;
      if (code === null) {
        grades.push({ id: q.id, title: q.title, tier: q.tier, passed: 0, total, fatal: null });
        continue;
      }
      const rep = await runner.run(code, q.func, q.tests);
      grades.push({ id: q.id, title: q.title, tier: q.tier, total, fatal: rep.fatal,
                    passed: rep.results.filter((r) => r.ok).length });
    }
    const secondsUsed = Math.min(this.duration, Math.floor(((this.endedAt ?? this._now()) - this.startedAt) / 1000));
    const score = grades.reduce((s, g) => s + g.passed / g.total, 0) / grades.length * 100;
    return {
      candidate: this.candidate,
      started: new Date(this.startedAt).toISOString(),
      secondsUsed,
      score: Math.round(score * 10) / 10,
      answered: this.codes.filter((c) => c !== null).length,
      grades,
      codes: this.codes,
    };
  }

  toJSON() {
    return {
      candidate: this.candidate, questionIds: this.questions.map((q) => q.id), duration: this.duration,
      startedAt: this.startedAt, index: this.index, codes: this.codes, finished: this.finished,
      endedAt: this.endedAt,
    };
  }

  static restore(data, bank, now = Date.now) {
    const byId = new Map(bank.map((q) => [q.id, q]));
    const questions = data.questionIds.map((id) => byId.get(id));
    if (questions.some((q) => !q)) throw new Error("Banque de questions modifiée : session illisible.");
    return new Session({ ...data, questions, now });
  }
}
