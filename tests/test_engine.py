import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from coderbyte_sim import engine  # noqa: E402
import references  # noqa: E402

BANK = engine.load_bank()
# les références utilisent des helpers : on injecte le module complet comme "code candidat"
REFERENCE_CODE = Path(references.__file__).read_text(encoding="utf-8")


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class BankTests(unittest.TestCase):
    def test_structure(self):
        ids = [q["id"] for q in BANK]
        self.assertEqual(len(ids), len(set(ids)))
        for tier, n in engine.TIER_PLAN:
            self.assertGreaterEqual(sum(q["tier"] == tier for q in BANK), n)
        for q in BANK:
            self.assertIn(f"def {q['func']}(", q["starter"])
            samples = [t for t in q["tests"] if t["sample"]]
            self.assertTrue(samples, q["id"])
            self.assertGreater(len(q["tests"]), len(samples), f"{q['id']}: pas de cas cachés")

    def test_every_reference_passes_every_test(self):
        for q in BANK:
            with self.subTest(q["id"]):
                code = REFERENCE_CODE
                rep = engine.run_tests(code, q["func"], q["tests"])
                self.assertIsNone(rep.fatal)
                failed = [(r.args, r.expected, r.got, r.error) for r in rep.results if not r.ok]
                self.assertEqual(failed, [])

    def test_pick_questions_plan(self):
        qs = engine.pick_questions(BANK, random.Random(1))
        self.assertEqual([q["tier"] for q in qs], ["easy", "easy", "medium", "medium", "hard"])
        self.assertEqual(len({q["id"] for q in qs}), 5)


class RunnerTests(unittest.TestCase):
    TESTS = [{"args": [2], "expected": "4"}, {"args": [3], "expected": "9"}]

    def run_code(self, code, tests=None, **kw):
        return engine.run_tests(code, "f", tests or self.TESTS, **kw)

    def test_correct_and_wrong(self):
        self.assertEqual(self.run_code("def f(n):\n    return n*n").passed, 2)
        rep = self.run_code("def f(n):\n    return n+2")
        self.assertEqual([r.ok for r in rep.results], [True, False])  # 2+2 == 4 par hasard
        self.assertEqual(rep.results[1].got, "5")

    def test_syntax_error_and_missing_function(self):
        self.assertIn("SyntaxError", self.run_code("def f(n) return n").fatal)
        self.assertIn("n'est pas définie", self.run_code("x = 1").fatal)

    def test_exception_is_reported_per_test(self):
        rep = self.run_code("def f(n):\n    return 1/0")
        self.assertEqual(rep.passed, 0)
        self.assertIn("ZeroDivisionError", rep.results[0].error)

    def test_infinite_loop_times_out(self):
        rep = self.run_code("def f(n):\n    while True: pass", per_test_timeout=1)
        self.assertTrue(rep.results[0].error.startswith("Temps dépassé"))
        self.assertFalse(rep.results[1].ran)

    def test_prints_are_captured_and_do_not_break_protocol(self):
        rep = self.run_code("def f(n):\n    print('hello {\"i\": 0}')\n    return n*n")
        self.assertEqual(rep.passed, 2)
        self.assertIn("hello", rep.results[0].out)

    def test_input_does_not_hang(self):
        rep = self.run_code("def f(n):\n    return input()")
        self.assertEqual(rep.passed, 0)
        self.assertIn("EOFError", rep.results[0].error)

    def test_args_not_mutated_between_runs(self):
        tests = [{"args": [[3, 1, 2]], "expected": "[1, 2, 3]"}]
        rep = engine.run_tests("def f(a):\n    a.sort()\n    return a", "f", tests)
        self.assertEqual(rep.passed, 1)

    def test_deep_recursion_is_an_error_not_a_crash(self):
        rep = self.run_code("def f(n):\n    return f(n)")
        self.assertEqual(rep.passed, 0)
        self.assertIn("RecursionError", rep.results[0].error)


class SessionTests(unittest.TestCase):
    def make(self, clock=None):
        qs = engine.pick_questions(BANK, random.Random(3))
        return engine.Session("Test User", qs, clock=clock or FakeClock()), qs

    def solution(self, q):
        return REFERENCE_CODE

    def test_only_samples_are_run_during_exam(self):
        s, qs = self.make()
        rep = s.run_samples(self.solution(qs[0]))
        self.assertEqual(rep.total, sum(t["sample"] for t in qs[0]["tests"]))
        self.assertLess(rep.total, len(qs[0]["tests"]))

    def test_no_going_back_and_full_flow(self):
        s, qs = self.make()
        seen = [s.current["id"]]
        for _ in range(4):
            self.assertTrue(s.submit(self.solution(s.current)))
            seen.append(s.current["id"])
        self.assertEqual(seen, [q["id"] for q in qs])  # strictement vers l'avant
        self.assertFalse(s.submit(self.solution(s.current)))
        self.assertTrue(s.finished)
        with self.assertRaises(RuntimeError):
            s.submit("x")
        with self.assertRaises(RuntimeError):
            s.run_samples("x")
        rep = s.grade()
        self.assertEqual(rep.answered, 5)
        self.assertAlmostEqual(rep.score, 100.0)

    def test_timer_expiry_keeps_current_code_and_zeroes_unreached(self):
        clock = FakeClock()
        s, qs = self.make(clock)
        s.submit(self.solution(qs[0]))
        clock.t = engine.EXAM_SECONDS - 1
        self.assertFalse(s.expired())
        clock.t = engine.EXAM_SECONDS + 5
        self.assertTrue(s.expired())
        self.assertEqual(s.remaining(), 0)
        s.finish(self.solution(qs[1]))
        rep = s.grade()
        self.assertEqual(rep.answered, 2)
        self.assertEqual([g.passed == g.total for g in rep.grades], [True, True, False, False, False])
        self.assertEqual(rep.seconds_used, engine.EXAM_SECONDS)

    def test_duration_is_fifty_minutes(self):
        self.assertEqual(engine.EXAM_SECONDS, 3000)

    def test_save_report(self):
        s, qs = self.make()
        for _ in range(5):
            s.submit("def nothing(): pass")
        rep = s.grade()
        self.assertEqual(rep.score, 0.0)
        with tempfile.TemporaryDirectory() as d:
            p = s.save(rep, Path(d))
            self.assertTrue(p.exists())
            self.assertIn("Test_User", p.name)


if __name__ == "__main__":
    unittest.main()
