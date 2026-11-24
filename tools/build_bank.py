"""Génère coderbyte_sim/bank.json à partir des énoncés, des solutions de
référence et des entrées de test définies ci-dessous.

Usage :  python tools/build_bank.py

- `samples`  : cas visibles par le candidat (issus des énoncés) ; leur sortie
               attendue est écrite à la main puis vérifiée contre la référence.
- `hidden`   : entrées supplémentaires ; sortie attendue calculée par la référence.
Les sorties sont comparées sous forme de chaînes (str(valeur)).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import references as R  # noqa: E402

STATEMENTS = json.loads((HERE / "statements.json").read_text(encoding="utf-8"))
OUT = HERE.parent / "coderbyte_sim" / "bank.json"

# (num source, tier, fonction, paramètres, note, samples[(args, attendu)], hidden[args])
Q = [
    # ---------------------------------------------------------------- easy
    (2, "easy", "FirstFactorial", "num", "",
     [([4], 24), ([8], 40320)],
     [[1], [5], [12], [18], [2]]),
    (3, "easy", "LetterChanges", "str", "",
     [(["hello*3"], "Ifmmp*3"), (["fun times!"], "gvO Ujnft!")],
     [["zzz"], ["a b c"], ["123"], ["xyz abc"], ["coderbyte"], ["z"]]),
    (8, "easy", "TimeConvert", "num", "",
     [([63], "1:3"), ([126], "2:6")],
     [[45], [0], [60], [1000], [59]]),
    (18, "easy", "SecondGreatLow", "arr", "",
     [([[1, 42, 42, 180]], "42 42"), ([[4, 90]], "90 4")],
     [[[7, 7, 12, 98, 106]], [[1, 2]], [[5, 3, 9, 1]], [[-4, 0, 10, 3]]]),
    (22, "easy", "DashInsert", "str", "L'entrée est passée sous forme de chaîne de chiffres.",
     [(["454793"], "4547-9-3"), (["99946"], "9-9-946")],
     [["56730"], ["1357"], ["2468"], ["10305"], ["7"]]),
    (27, "easy", "AdditivePersistence", "num", "",
     [([4], 0), ([19], 2)],
     [[2718], [5], [999999999999], [1234567], [10]]),
    (15, "easy", "ArithGeo", "arr", "",
     [([[2, 4, 6, 8]], "Arithmetic"), ([[2, 6, 18, 54]], "Geometric")],
     [[[5, 10, 15]], [[2, 4, 16, 24]], [[1, 2, 3, 4, 5]], [[3, 9, 27, 81]],
      [[-2, -4, -8]], [[1, 3, 6, 10]], [[-1, 1, 3, 5]], [[1, -2, 4, -8]]]),
    (21, "easy", "MeanMode", "arr", "",
     [([[5, 3, 3, 3, 1]], 1), ([[1, 2, 2, 3]], 1)],
     [[[4, 4, 4, 6, 10]], [[10, 10, 10, 2, 8]], [[1, 3, 3, 3, 5]], [[9]], [[3, 3, 3, 4, 5, 6]]]),
    # -------------------------------------------------------------- medium
    (20, "medium", "CountingMinutes1", "str", "",
     [(["9:00am-10:00am"], 60), (["1:00pm-11:00am"], 1320)],
     [["12:30pm-12:00am"], ["12:00am-12:01am"], ["11:59pm-12:00am"], ["5:15pm-3:45pm"],
      ["12:00pm-1:00pm"], ["6:30am-6:29am"]]),
    (19, "medium", "DivisionStringified", "num1, num2", "Arrondir à l'entier le plus proche (0,5 arrondi vers le haut).",
     [([2, 3], "1"), ([123456789, 10000], "12,346")],
     [[1000000, 3], [10, 5], [1234567, 1], [5000, 10], [9999999999, 7]]),
    (25, "medium", "ThirdGreatest", "strArr", "",
     [([["hello", "world", "before", "all"]], "world"), ([["hello", "world", "after", "all"]], "after")],
     [[["coder", "byte", "code"]], [["a", "bb", "ccc", "dd"]], [["abc", "abcd", "ab", "a"]],
      [["one", "two", "three", "four", "five"]]]),
    (16, "medium", "ArrayAddition", "arr", "",
     [([[4, 6, 23, 10, 1, 3]], "true"), ([[5, 7, 16, 1, 2]], "false")],
     [[[3, 5, -1, 8, 12]], [[2, 3, 4]], [[1, 2, 3]], [[100, 1, 2, 3]], [[1, 2, 3, 4, 5, 6, 40, 20]]]),
    (30, "medium", "ChangingSequence", "arr", "",
     [([[1, 2, 4, 6, 4, 3, 1]], 3), ([[-4, -2, 9, 10]], -1)],
     [[[10, 8, 5, 6]], [[1, 3, 2]], [[3, 2, 1]], [[1, 2, 3, 2, 1]], [[9, 8, 7, 8, 9]]]),
    (42, "medium", "TwoSum", "arr", "",
     [([[7, 3, 5, 2, -4, 8, 11]], "5,2 -4,11"), ([[6, 3, 1]], -1)],
     [[[10, 1, 2, 3, 4, 5, 6, 7, 8, 9]], [[4, 1, 2]], [[5, 2, 3, 4, 1]], [[1, -1, 2, 5]]]),
    (57, "medium", "TimeDifference", "strArr", "L'horloge est circulaire : minuit est franchi (23:50 et 00:10 sont distantes de 20 minutes).",
     [([["2:10pm", "1:30pm", "10:30am", "4:42pm"]], 40), ([["11:50pm", "12:10am", "6:00am"]], 20)],
     [[["1:10pm", "4:40am", "5:00pm"]], [["12:00pm", "12:01pm"]], [["1:00am", "11:00pm", "12:00pm"]],
      [["9:15am", "9:45am", "3:30pm", "3:00pm"]]]),
    # ---------------------------------------------------------------- hard
    (44, "hard", "PalindromeCreator", "str", "",
     [(["abjchba"], "jc"), (["mmop"], "not possible"), (["kjjjhjjj"], "k")],
     [["racecar"], ["abcd"], ["aabb"], ["aabaacd"], ["abcdcbae"], ["xabcbay"]]),
    (54, "hard", "ScaleBalancing", "strArr", "Les poids utilisés sont renvoyés par ordre croissant, séparés par une virgule.",
     [([["[5, 9]", "[1, 2, 6, 7]"]], "2,6"), ([["[3, 4]", "[1, 2, 7, 7]"]], "1")],
     [[["[13, 4]", "[1, 2, 3, 6, 14]"]], [["[7, 3]", "[8, 2, 5, 1]"]], [["[1, 2]", "[10, 20]"]],
      [["[20, 5]", "[4, 6, 12, 40]"]]]),
    (75, "hard", "StringPeriods", "str", "",
     [(["abcababcababcab"], "abcab"), (["abababababab"], "ababab")],
     [["abcxabc"], ["a"], ["aaaa"], ["abcabcabcabc"], ["xyzxyz"], ["abcd"]]),
    (59, "hard", "VowelSquare", "strArr", "",
     [([["abcd", "eikr", "oufj"]], "1-0"), ([["aqrst", "ukaei", "ffooo"]], "1-2"), ([["gg", "ff"]], "not found")],
     [[["aei", "eio", "uae"]], [["bab", "eae", "ooo"]], [["xxxx", "xaex", "xiox", "xxxx"]],
      [["ae", "ex", "oi"]]]),
    (81, "hard", "MovingMedian", "arr", "Le test ne contient que des médianes entières.",
     [([[3, 1, 3, 5, 10, 6, 4, 3, 1]], "1,2,3,5,6,6,4,3")],
     [[[2, 4, 6, 8, 10]], [[1, 5, 2, 8]], [[4, 5, 5, 5, 5, 5]], [[3, 10, 20, 30, 40]]]),
    (39, "hard", "NextPalindrome", "num", "",
     [([24], 33), ([99], 101)],
     [[123], [1], [9], [12921], [808], [999], [1234], [98765]]),
    (45, "hard", "ProductDigits", "num", "",
     [([24], 2), ([90], 3)],
     [[7], [6], [100], [143], [1000], [1]]),
]


def build():
    questions = []
    for src, tier, func, params, note, samples, hidden in Q:
        ref = getattr(R, func)
        text = STATEMENTS[str(src)]["text"]
        tests = []
        for args, expected in samples:
            got = ref(*args)
            assert str(got) == str(expected), f"{func}{args}: ref={got!r} != énoncé={expected!r}"
            tests.append({"args": args, "expected": str(expected), "sample": True})
        for args in hidden:
            if func == "PalindromeCreator":
                cands = R.palindrome_creator_candidates(args[0])
                assert len(cands) <= 1 or R.PalindromeCreator(*args) == "palindrome", f"ambigu: {args}"
            if func == "ScaleBalancing":
                assert len(R.scale_candidates(*args)) <= 1, f"ambigu: {args}"
            if func == "MovingMedian":
                assert R.moving_median_is_integral(args[0]), f"médiane non entière: {args}"
            tests.append({"args": args, "expected": str(ref(*args)), "sample": False})
        questions.append({
            "id": f"{src:02d}-{func}",
            "title": func,
            "tier": tier,
            "func": func,
            "params": params,
            "statement": text,
            "note": note,
            "starter": f"def {func}({params}):\n    # écrivez votre code ici\n    return 0\n",
            "tests": tests,
        })
    OUT.write_text(json.dumps({"questions": questions}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(questions)} questions, "
          f"{sum(len(q['tests']) for q in questions)} tests -> {OUT}")


if __name__ == "__main__":
    build()
