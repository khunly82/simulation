"""Logique métier : banque de questions, exécution des tests, session d'examen."""
from __future__ import annotations

import json
import random
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

PKG = Path(__file__).resolve().parent
BANK_PATH = PKG / "bank.json"
RUNNER = PKG / "runner.py"
RESULTS_DIR = PKG.parent / "results"

EXAM_SECONDS = 50 * 60
# 2 faciles, 2 moyennes, 1 difficile : présentées dans cet ordre.
TIER_PLAN = (("easy", 2), ("medium", 2), ("hard", 1))


# --------------------------------------------------------------------- banque
def load_bank(path: Path = BANK_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["questions"]


def pick_questions(bank: list[dict], rng: random.Random | None = None) -> list[dict]:
    rng = rng or random.Random()
    chosen: list[dict] = []
    for tier, n in TIER_PLAN:
        pool = [q for q in bank if q["tier"] == tier]
        chosen += rng.sample(pool, n)
    return chosen


# ---------------------------------------------------------------- exécution
@dataclass
class TestResult:
    index: int
    ok: bool = False
    args: list = field(default_factory=list)
    expected: str = ""
    got: str | None = None
    error: str | None = None
    out: str = ""
    ran: bool = True


@dataclass
class RunReport:
    results: list[TestResult]
    fatal: str | None = None  # erreur de syntaxe / fonction absente

    @property
    def passed(self) -> int:
        return sum(r.ok for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)


def _python_exe() -> str:
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):  # pas de console sous Windows
        exe = exe[:-5] + exe[-4:]
    return exe


def run_tests(code: str, func: str, tests: list[dict], per_test_timeout: float = 3.0) -> RunReport:
    """Lance `code` dans un sous-processus et évalue `func` sur chaque test."""
    results = [
        TestResult(i, args=t["args"], expected=t["expected"], ran=False) for i, t in enumerate(tests)
    ]
    payload = json.dumps(
        {"code": code, "func": func, "tests": tests, "timeout": per_test_timeout}
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    # garde-fou global : au pire chaque test consomme son timeout
    overall = per_test_timeout * len(tests) + 10
    try:
        proc = subprocess.run(
            [_python_exe(), "-I", str(RUNNER)],
            input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=overall, creationflags=flags,
        )
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"")
        stdout = stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout
        stdout = stdout or ""
        stderr = ""

    fatal = None
    for line in stdout.splitlines():
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if "fatal" in msg:
            fatal = msg["fatal"]
            break
        r = results[msg["i"]]
        r.ran = True
        r.ok, r.got, r.error, r.out = msg["ok"], msg["got"], msg["error"], msg["out"]
    if fatal is None and not any(r.ran for r in results) and stderr.strip():
        fatal = stderr.strip()[-1500:]
    return RunReport(results, fatal)


# ------------------------------------------------------------------ session
@dataclass
class QuestionGrade:
    question_id: str
    title: str
    tier: str
    passed: int
    total: int
    fatal: str | None = None

    @property
    def ratio(self) -> float:
        return self.passed / self.total if self.total else 0.0


@dataclass
class Report:
    candidate: str
    started: str
    seconds_used: int
    grades: list[QuestionGrade]
    answered: int

    @property
    def score(self) -> float:
        return sum(g.ratio for g in self.grades) / len(self.grades) * 100 if self.grades else 0.0


class Session:
    """Un passage de test : 5 questions, un seul chrono, aucun retour arrière."""

    def __init__(self, candidate: str, questions: list[dict],
                 duration: int = EXAM_SECONDS, clock: Callable[[], float] = time.monotonic):
        self.candidate = candidate
        self.questions = questions
        self.duration = duration
        self._clock = clock
        self.started_at = clock()
        self.started_iso = datetime.now().isoformat(timespec="seconds")
        self.index = 0
        self.codes: list[str | None] = [None] * len(questions)
        self.finished = False
        self.ended_at: float | None = None

    # -- état
    @property
    def current(self) -> dict:
        return self.questions[self.index]

    @property
    def is_last(self) -> bool:
        return self.index == len(self.questions) - 1

    def remaining(self) -> float:
        return max(0.0, self.duration - (self._clock() - self.started_at))

    def expired(self) -> bool:
        return self.remaining() <= 0

    # -- actions
    def run_samples(self, code: str) -> RunReport:
        """Seuls les cas d'exemple sont exécutés pendant le test."""
        if self.finished:
            raise RuntimeError("Le test est terminé.")
        q = self.current
        tests = [t for t in q["tests"] if t["sample"]]
        return run_tests(code, q["func"], tests)

    def submit(self, code: str) -> bool:
        """Fige la réponse courante et passe à la suivante. False si c'était la dernière."""
        if self.finished:
            raise RuntimeError("Le test est terminé.")
        self.codes[self.index] = code
        if self.is_last:
            self.finish()
            return False
        self.index += 1
        return True

    def finish(self, current_code: str | None = None) -> None:
        """Termine le test (dernière question, ou temps écoulé : le code en cours est conservé)."""
        if self.finished:
            return
        if current_code is not None and self.codes[self.index] is None:
            self.codes[self.index] = current_code
        self.finished = True
        self.ended_at = self._clock()

    def grade(self) -> Report:
        """Correction finale sur TOUS les tests (exemples + cachés)."""
        if not self.finished:
            raise RuntimeError("Le test n'est pas terminé.")
        grades = []
        for q, code in zip(self.questions, self.codes):
            total = len(q["tests"])
            if code is None:  # question jamais atteinte
                grades.append(QuestionGrade(q["id"], q["title"], q["tier"], 0, total))
                continue
            rep = run_tests(code, q["func"], q["tests"])
            grades.append(QuestionGrade(q["id"], q["title"], q["tier"], rep.passed, total, rep.fatal))
        used = int(min(self.duration, (self.ended_at or self._clock()) - self.started_at))
        return Report(self.candidate, self.started_iso, used, grades,
                      sum(c is not None for c in self.codes))

    def save(self, report: Report, directory: Path = RESULTS_DIR) -> Path:
        directory.mkdir(exist_ok=True)
        safe = "".join(c if c.isalnum() else "_" for c in self.candidate) or "candidat"
        path = directory / f"{datetime.now():%Y%m%d_%H%M%S}_{safe}.json"
        data = {
            "candidate": report.candidate,
            "started": report.started,
            "seconds_used": report.seconds_used,
            "score_percent": round(report.score, 1),
            "questions": [
                {"id": g.question_id, "tier": g.tier, "passed": g.passed, "total": g.total,
                 "error": g.fatal, "code": code}
                for g, code in zip(report.grades, self.codes)
            ],
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return path
