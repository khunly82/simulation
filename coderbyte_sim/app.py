"""Interface Tkinter du simulateur d'entretien technique."""
from __future__ import annotations

import queue
import random
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from . import engine

TIER_LABEL = {"easy": "Facile", "medium": "Moyen", "hard": "Difficile"}
EDITOR_BG, EDITOR_FG = "#1e1e1e", "#d4d4d4"
MONO = ("Consolas", 11)


def fmt_clock(seconds: float) -> str:
    s = int(seconds + 0.999)  # arrondi au-dessus : 0:00 seulement quand c'est fini
    return f"{s // 60:02d}:{s % 60:02d}"


class CodeEditor(ttk.Frame):
    """Zone de code avec numéros de ligne, Tab = 4 espaces, indentation automatique."""

    def __init__(self, master):
        super().__init__(master)
        self.gutter = tk.Text(self, width=4, padx=4, takefocus=0, border=0, font=MONO,
                              background="#252526", foreground="#858585", state="disabled",
                              cursor="arrow")
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self._yview)
        self.text = tk.Text(self, undo=True, wrap="none", font=MONO, background=EDITOR_BG,
                            foreground=EDITOR_FG, insertbackground="#ffffff", border=0, padx=6,
                            selectbackground="#264f78", yscrollcommand=self._on_scroll, tabs="4c")
        xsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(xscrollcommand=xsb.set)
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.sb.grid(row=0, column=2, sticky="ns")
        xsb.grid(row=1, column=1, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.text.bind("<Tab>", self._on_tab)
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<<Modified>>", self._on_modified)
        self.gutter.bind("<MouseWheel>", lambda e: "break")

    def _yview(self, *args):
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _on_scroll(self, first, last):
        self.sb.set(first, last)
        self.gutter.yview_moveto(first)

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            lines = int(self.text.index("end-1c").split(".")[0])
            self.gutter.configure(state="normal")
            self.gutter.delete("1.0", "end")
            self.gutter.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
            self.gutter.tag_configure("r", justify="right")
            self.gutter.tag_add("r", "1.0", "end")
            self.gutter.configure(state="disabled")
            self.gutter.yview_moveto(self.text.yview()[0])
            self.text.edit_modified(False)

    def _on_tab(self, _event):
        self.text.insert("insert", "    ")
        return "break"

    def _on_return(self, _event):
        line = self.text.get("insert linestart", "insert")
        indent = line[: len(line) - len(line.lstrip(" "))]
        if line.rstrip().endswith(":"):
            indent += "    "
        self.text.insert("insert", "\n" + indent)
        self.text.see("insert")
        return "break"

    def get(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set(self, content: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.mark_set("insert", "1.0")

    def focus_editor(self):
        self.text.focus_set()


class App(tk.Tk):
    def __init__(self, minutes: float = 50, seed: int | None = None):
        super().__init__()
        self.title("Simulateur d'entretien technique — Python")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        ttk.Style(self).theme_use("clam")
        self.duration = int(minutes * 60)
        self.rng = random.Random(seed)
        self.session: engine.Session | None = None
        self.q: queue.Queue = queue.Queue()
        self._busy = False
        self._ended = False
        self.frame: tk.Widget | None = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_start()
        self.after(100, self._poll)

    # ------------------------------------------------------------ plumbing
    def _swap(self, frame: tk.Widget):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame
        frame.pack(fill="both", expand=True)

    def _poll(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _in_thread(self, work, done):
        def target():
            try:
                res = work()
            except Exception as exc:  # noqa: BLE001
                res = exc
            self.q.put(lambda: done(res))
        threading.Thread(target=target, daemon=True).start()

    def _on_close(self):
        if self.session and not self.session.finished:
            if not messagebox.askokcancel(
                    "Quitter", "Le test est en cours : quitter maintenant abandonne votre "
                               "passage sans correction. Quitter quand même ?"):
                return
        self.destroy()

    # --------------------------------------------------------------- start
    def show_start(self):
        f = ttk.Frame(self, padding=40)
        ttk.Label(f, text="Simulateur d'entretien technique", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(f, text="Langage : Python", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 20))
        mins = self.duration // 60
        rules = (
            f"• {sum(n for _, n in engine.TIER_PLAN)} questions tirées au sort "
            "(2 faciles, 2 moyennes, 1 difficile).\n"
            f"• {mins} minutes au total, un seul chronomètre pour l'ensemble du test.\n"
            "• Vous pouvez lancer les tests d'exemple autant de fois que vous voulez : ils ne "
            "couvrent qu'une partie des cas.\n"
            "• Votre solution sera corrigée à la fin sur l'ensemble des cas, y compris des cas "
            "cachés (cas limites).\n"
            "• Une fois passé à la question suivante, il est impossible de revenir en arrière.\n"
            "• Le test s'arrête automatiquement quand le temps est écoulé : le code en cours "
            "est alors conservé.\n"
            "• Bibliothèque standard Python uniquement ; les valeurs retournées sont comparées "
            "sous forme de texte."
        )
        ttk.Label(f, text=rules, justify="left", font=("Segoe UI", 11)).pack(anchor="w", pady=10)
        row = ttk.Frame(f)
        row.pack(anchor="w", pady=20)
        ttk.Label(row, text="Votre nom :", font=("Segoe UI", 11)).pack(side="left")
        self.name_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.name_var, width=32, font=("Segoe UI", 11))
        entry.pack(side="left", padx=10)
        entry.focus_set()
        btn = ttk.Button(row, text="Démarrer le test", command=self._start)
        btn.pack(side="left")
        entry.bind("<Return>", lambda e: self._start())
        self._swap(f)

    def _start(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Nom requis", "Saisissez votre nom pour démarrer.")
            return
        bank = engine.load_bank()
        self.session = engine.Session(name, engine.pick_questions(bank, self.rng), duration=self.duration)
        self._ended = False
        self._build_exam()
        self._load_question()
        self._tick()

    # ---------------------------------------------------------------- exam
    def _build_exam(self):
        f = ttk.Frame(self)
        top = ttk.Frame(f, padding=(12, 8))
        top.pack(fill="x")
        self.lbl_q = ttk.Label(top, font=("Segoe UI", 13, "bold"))
        self.lbl_q.pack(side="left")
        self.lbl_timer = ttk.Label(top, font=("Consolas", 20, "bold"))
        self.lbl_timer.pack(side="right")
        ttk.Label(top, text="Temps restant : ").pack(side="right")

        bottom = ttk.Frame(f, padding=(12, 8))
        bottom.pack(side="bottom", fill="x")
        self.btn_run = ttk.Button(bottom, text="▶  Exécuter les tests d'exemple", command=self._run)
        self.btn_run.pack(side="left")
        self.btn_next = ttk.Button(bottom, command=self._next)
        self.btn_next.pack(side="right")
        self.lbl_hint = ttk.Label(bottom, foreground="#666666",
                                  text="Aucun retour arrière possible après validation.")
        self.lbl_hint.pack(side="right", padx=12)

        main = ttk.PanedWindow(f, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8)
        left = ttk.Frame(main)
        self.txt_statement = tk.Text(left, wrap="word", font=("Segoe UI", 11), padx=12, pady=10,
                                     border=0, background="#fafafa", state="disabled", width=48)
        sbl = ttk.Scrollbar(left, command=self.txt_statement.yview)
        self.txt_statement.configure(yscrollcommand=sbl.set)
        sbl.pack(side="right", fill="y")
        self.txt_statement.pack(fill="both", expand=True)
        self.txt_statement.tag_configure("h", font=("Segoe UI", 13, "bold"))
        self.txt_statement.tag_configure("code", font=MONO, background="#eeeeee")
        self.txt_statement.tag_configure("note", foreground="#8a5a00", font=("Segoe UI", 10, "italic"))
        main.add(left, weight=2)

        right = ttk.PanedWindow(main, orient="vertical")
        self.editor = CodeEditor(right)
        right.add(self.editor, weight=3)
        outf = ttk.Frame(right)
        self.txt_out = tk.Text(outf, height=10, wrap="word", font=("Consolas", 10), border=0,
                               background="#f3f3f3", state="disabled", padx=8, pady=6)
        sbo = ttk.Scrollbar(outf, command=self.txt_out.yview)
        self.txt_out.configure(yscrollcommand=sbo.set)
        sbo.pack(side="right", fill="y")
        self.txt_out.pack(fill="both", expand=True)
        for tag, color in (("ok", "#1a7f37"), ("fail", "#c62828"), ("dim", "#666666")):
            self.txt_out.tag_configure(tag, foreground=color)
        self.txt_out.tag_configure("b", font=("Consolas", 10, "bold"))
        right.add(outf, weight=1)
        main.add(right, weight=3)
        self._swap(f)

    def _load_question(self):
        s = self.session
        q = s.current
        n = len(s.questions)
        self.lbl_q.configure(text=f"Question {s.index + 1} / {n}  ·  {TIER_LABEL[q['tier']]}")
        t = self.txt_statement
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", q["title"] + "\n", "h")
        t.insert("end", "\nFonction à écrire :  ")
        t.insert("end", f"{q['func']}({q['params']})\n\n", "code")
        t.insert("end", q["statement"].replace("\n", "\n\n") + "\n")
        if q["note"]:
            t.insert("end", "\nNote : " + q["note"] + "\n", "note")
        nsamples = sum(x["sample"] for x in q["tests"])
        t.insert("end", f"\n{nsamples} tests d'exemple sont exécutables ; d'autres cas, cachés, "
                        "seront évalués à la fin.\n", "note")
        t.configure(state="disabled")
        self.editor.set(q["starter"])
        self.editor.focus_editor()
        self._out_clear()
        self.btn_next.configure(
            text="Terminer le test ✔" if s.is_last else "Valider et question suivante  ▶")
        self.btn_run.configure(state="normal")
        self.btn_next.configure(state="normal")

    def _tick(self):
        if self._ended or self.session is None:
            return
        rem = self.session.remaining()
        self.lbl_timer.configure(text=fmt_clock(rem), foreground="#c62828" if rem < 300 else "#000000")
        if rem <= 0:
            messagebox.showinfo("Temps écoulé", "Le temps est écoulé : le test est terminé.")
            self._end_exam()
            return
        self.after(250, self._tick)

    # output helpers
    def _out_clear(self):
        self.txt_out.configure(state="normal")
        self.txt_out.delete("1.0", "end")
        self.txt_out.insert("end", "Les résultats des tests d'exemple s'afficheront ici.", "dim")
        self.txt_out.configure(state="disabled")

    def _out_show(self, rep: engine.RunReport):
        t = self.txt_out
        t.configure(state="normal")
        t.delete("1.0", "end")
        func = self.session.current["func"]
        if rep.fatal:
            t.insert("end", "Erreur :\n", ("fail", "b"))
            t.insert("end", rep.fatal + "\n", "fail")
        else:
            colour = "ok" if rep.passed == rep.total else "fail"
            t.insert("end", f"{rep.passed} / {rep.total} tests d'exemple réussis\n\n", (colour, "b"))
            for r in rep.results:
                args = ", ".join(repr(a) for a in r.args)
                if len(args) > 90:
                    args = args[:87] + "..."
                head = f"Test {r.index + 1} : {func}({args})\n"
                if not r.ran:
                    t.insert("end", "⏭  " + head + "    non exécuté\n", "dim")
                elif r.ok:
                    t.insert("end", "✔  " + head, "ok")
                else:
                    t.insert("end", "✘  " + head, "fail")
                    t.insert("end", f"    attendu : {r.expected!r}\n")
                    if r.error:
                        t.insert("end", "    " + r.error.strip().replace("\n", "\n    ") + "\n", "fail")
                    else:
                        t.insert("end", f"    obtenu  : {r.got}\n")
                if r.out:
                    t.insert("end", "    sortie standard : " + r.out.rstrip().replace("\n", "\n      ") + "\n", "dim")
            if rep.passed == rep.total:
                t.insert("end", "\nVos cas d'exemple passent. Pensez aux cas limites : d'autres "
                                "tests seront évalués à la fin.\n", "dim")
        t.configure(state="disabled")

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.btn_run.configure(state=state)
        self.btn_next.configure(state=state)

    def _run(self):
        if self._busy or self.session.finished:
            return
        self._set_busy(True)
        self.btn_run.configure(text="Exécution…")
        code = self.editor.get()
        idx = self.session.index

        def done(res):
            self.btn_run.configure(text="▶  Exécuter les tests d'exemple")
            if self.session.finished or self.session.index != idx:
                return  # la question a changé entre-temps : résultat périmé
            self._set_busy(False)
            if isinstance(res, Exception):
                messagebox.showerror("Erreur interne", str(res))
            else:
                self._out_show(res)

        self._in_thread(lambda: self.session.run_samples(code), done)

    def _next(self):
        if self._busy:
            return
        last = self.session.is_last
        msg = ("Terminer le test ? Vous ne pourrez plus modifier vos réponses." if last else
               "Passer à la question suivante ? Vous ne pourrez plus revenir à celle-ci.")
        if not messagebox.askyesno("Confirmation", msg):
            return
        if self.session.expired():
            self._end_exam()
            return
        if self.session.submit(self.editor.get()):
            self._load_question()
        else:
            self._end_exam()

    # ----------------------------------------------------------- end / grade
    def _end_exam(self):
        if self._ended:
            return
        self._ended = True
        s = self.session
        s.finish(self.editor.get())
        f = ttk.Frame(self, padding=60)
        ttk.Label(f, text="Test terminé", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(f, text="Correction en cours (tous les cas de test, y compris cachés)…",
                  font=("Segoe UI", 12)).pack(anchor="w", pady=20)
        bar = ttk.Progressbar(f, mode="indeterminate", length=400)
        bar.pack(anchor="w")
        bar.start(12)
        self._swap(f)

        def work():
            report = s.grade()
            return report, s.save(report)

        def done(res):
            if isinstance(res, Exception):
                messagebox.showerror("Erreur de correction", str(res))
                self.destroy()
                return
            self._show_result(*res)

        self._in_thread(work, done)

    def _show_result(self, report: engine.Report, path):
        f = ttk.Frame(self, padding=40)
        ttk.Label(f, text="Résultats", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(f, text=f"{report.candidate} — {fmt_clock(report.seconds_used)} utilisées sur "
                          f"{fmt_clock(self.duration)}", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 10))
        ttk.Label(f, text=f"Score global : {report.score:.0f} %", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        cols = ("q", "tier", "tests", "state")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=len(report.grades))
        for c, title, w in (("q", "Question", 280), ("tier", "Niveau", 120),
                            ("tests", "Cas réussis", 120), ("state", "Statut", 200)):
            tree.heading(c, text=title)
            tree.column(c, width=w, anchor="w")
        for i, g in enumerate(report.grades):
            if i >= report.answered:
                state = "non atteinte"
            elif g.fatal:
                state = "erreur de code"
            elif g.passed == g.total:
                state = "✔ réussie"
            else:
                state = "✘ partielle" if g.passed else "✘ échec"
            tree.insert("", "end", values=(f"{i + 1}. {g.title}", TIER_LABEL[g.tier],
                                           f"{g.passed} / {g.total}", state))
        tree.pack(anchor="w", pady=20)
        ttk.Label(f, text=f"Résultat détaillé et code enregistrés dans :\n{path}",
                  foreground="#555555").pack(anchor="w")
        ttk.Button(f, text="Fermer", command=self.destroy).pack(anchor="w", pady=20)
        self._swap(f)


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(prog="coderbyte_sim", description="Simulateur d'entretien technique Python.")
    ap.add_argument("--minutes", type=float, default=50, help="durée totale (défaut : 50)")
    ap.add_argument("--seed", type=int, default=None, help="graine du tirage (reproductible)")
    args = ap.parse_args(argv)
    App(minutes=args.minutes, seed=args.seed).mainloop()
