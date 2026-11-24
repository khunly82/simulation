"""Harnais exécuté dans Pyodide (worker) : prépare le code du candidat puis lance un test à la fois."""
import contextlib
import io
import json
import sys
import traceback

_fn = None
MAX_OUT = 2000


def prepare(code, func):
    global _fn
    sys.stdin = io.StringIO("")
    ns = {"__name__": "__candidate__"}
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<votre_code>", "exec"), ns)
    except BaseException:
        return json.dumps({"fatal": traceback.format_exc(limit=3)})
    if not callable(ns.get(func)):
        return json.dumps({"fatal": f"La fonction {func} n'est pas définie."})
    _fn = ns[func]
    return json.dumps({"ok": True})


def run_one(args_json, expected):
    buf = io.StringIO()
    args = json.loads(args_json)  # copie fraîche à chaque test
    try:
        with contextlib.redirect_stdout(buf):
            value = _fn(*args)
    except BaseException:
        return json.dumps({"ok": False, "got": None, "error": traceback.format_exc(limit=4),
                           "out": buf.getvalue()[:MAX_OUT]})
    return json.dumps({"ok": str(value) == expected, "got": repr(value), "error": None,
                       "out": buf.getvalue()[:MAX_OUT]})
