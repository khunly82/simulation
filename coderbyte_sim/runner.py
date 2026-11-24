"""Exécute le code d'un candidat dans un processus séparé.

Protocole : JSON sur stdin {code, func, tests:[{args, expected}], timeout}
            -> une ligne JSON par test sur stdout (flush immédiat).
Lancé par engine.py avec `python -I runner.py`.
"""
import copy
import io
import json
import os
import sys
import threading
import traceback

MAX_OUT = 2000


def main():
    # -I ignore PYTHONIOENCODING : on force l'UTF-8 (sinon cp1252 sous Windows)
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    real_out = sys.stdout
    payload = json.loads(sys.stdin.read())

    def emit(obj):
        real_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
        real_out.flush()

    sys.stdin = io.StringIO("")
    namespace = {"__name__": "__candidate__"}
    try:
        exec(compile(payload["code"], "<votre_code>", "exec"), namespace)
    except BaseException:
        emit({"fatal": traceback.format_exc(limit=3)})
        return
    fn = namespace.get(payload["func"])
    if not callable(fn):
        emit({"fatal": f"La fonction {payload['func']} n'est pas définie."})
        return

    threading.stack_size(64 * 1024 * 1024)
    timeout = payload.get("timeout", 3)
    for i, test in enumerate(payload["tests"]):
        buf = io.StringIO()
        box = {}

        def call():
            try:
                box["value"] = fn(*copy.deepcopy(test["args"]))
            except BaseException:
                box["error"] = traceback.format_exc(limit=4)

        sys.stdout = buf
        t = threading.Thread(target=call, daemon=True)
        t.start()
        t.join(timeout)
        sys.stdout = real_out

        res = {"i": i, "out": buf.getvalue()[:MAX_OUT]}
        if t.is_alive():
            res.update(ok=False, got=None, error=f"Temps dépassé (> {timeout} s)", timeout=True)
            emit(res)
            real_out.flush()
            os._exit(0)  # le thread bloqué ne peut pas être tué : on arrête tout
        if "error" in box:
            res.update(ok=False, got=None, error=box["error"])
        else:
            got = box["value"]
            res.update(ok=str(got) == str(test["expected"]), got=repr(got), error=None)
        emit(res)


if __name__ == "__main__":
    main()
