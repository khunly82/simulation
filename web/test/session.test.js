import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { Session, pickQuestions, mulberry32, EXAM_SECONDS } from "../public/session.js";

const bank = JSON.parse(fs.readFileSync(new URL("../public/bank.json", import.meta.url), "utf-8")).questions;

const fakeRunner = (okFor = () => true) => ({
  async run(code, func, tests) {
    const ok = okFor(code);
    return { fatal: null, results: tests.map((t, i) => ({ index: i, ok, ran: true })) };
  },
});

function make(clock = { t: 1_000_000 }) {
  const questions = pickQuestions(bank, mulberry32(3));
  return { clock, s: new Session({ candidate: "Test", questions, now: () => clock.t }), questions };
}

test("la durée est de 50 minutes", () => assert.equal(EXAM_SECONDS, 3000));

test("tirage : 2 faciles, 2 moyennes, 1 difficile, sans doublon", () => {
  const qs = pickQuestions(bank, mulberry32(1));
  assert.deepEqual(qs.map((q) => q.tier), ["easy", "easy", "medium", "medium", "hard"]);
  assert.equal(new Set(qs.map((q) => q.id)).size, 5);
});

test("tirage reproductible avec la même graine, et non mutant pour la banque", () => {
  const before = bank.map((q) => q.id).join();
  const a = pickQuestions(bank, mulberry32(5)).map((q) => q.id);
  const b = pickQuestions(bank, mulberry32(5)).map((q) => q.id);
  assert.deepEqual(a, b);
  assert.equal(bank.map((q) => q.id).join(), before);
});

test("seuls les tests d'exemple sont exposés pendant l'examen", () => {
  const { s } = make();
  const samples = s.sampleTests();
  assert.ok(samples.length > 0 && samples.length < s.current.tests.length);
  assert.ok(samples.every((t) => t.sample));
});

test("parcours strictement vers l'avant puis blocage", async () => {
  const { s, questions } = make();
  const seen = [s.current.id];
  for (let i = 0; i < 4; i++) {
    assert.equal(s.submit(`code${i}`), true);
    seen.push(s.current.id);
  }
  assert.deepEqual(seen, questions.map((q) => q.id));
  assert.equal(s.submit("last"), false);
  assert.ok(s.finished);
  assert.throws(() => s.submit("x"));
  const rep = await s.grade(fakeRunner());
  assert.equal(rep.score, 100);
  assert.equal(rep.answered, 5);
});

test("expiration : le code en cours est conservé, les questions non atteintes valent 0", async () => {
  const { s, clock } = make();
  s.submit("q1");
  clock.t += (EXAM_SECONDS - 1) * 1000;
  assert.equal(s.expired(), false);
  clock.t += 6000;
  assert.equal(s.expired(), true);
  assert.equal(s.remaining(), 0);
  s.finish("q2-en-cours");
  assert.deepEqual(s.codes, ["q1", "q2-en-cours", null, null, null]);
  const rep = await s.grade(fakeRunner());
  assert.deepEqual(rep.grades.map((g) => g.passed === g.total), [true, true, false, false, false]);
  assert.equal(rep.secondsUsed, EXAM_SECONDS);
  assert.equal(rep.score, 40);
});

test("sérialisation / reprise après rechargement : le chrono et l'index sont conservés", () => {
  const { s, clock } = make();
  s.submit("a");
  clock.t += 120_000;
  const restored = Session.restore(JSON.parse(JSON.stringify(s)), bank, () => clock.t);
  assert.equal(restored.index, 1);
  assert.deepEqual(restored.codes, ["a", null, null, null, null]);
  assert.equal(Math.round(restored.remaining()), EXAM_SECONDS - 120);
  assert.equal(restored.current.id, s.current.id);
});
