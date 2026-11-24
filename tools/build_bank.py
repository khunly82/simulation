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
OUTS = [HERE.parent / "coderbyte_sim" / "bank.json", HERE.parent / "web" / "public" / "bank.json"]

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
    # ------------------------------------------------------ lot 2 : faciles
    (23, "easy", "SwapCase", "str", "",
     [(["Hello World"], "hELLO wORLD"), (["Hello-LOL"], "hELLO-lol")],
     [["abc"], ["ABC"], ["a1B2 c3"], ["Coderbyte!"], ["zZ"]]),
    (28, "easy", "MultiplicativePersistence", "num", "",
     [([39], 3), ([4], 0)],
     [[999], [25], [10], [77], [86]]),
    (40, "easy", "LargestPair", "num", "L'entrée est passée sous forme d'entier.",
     [([4759472], 94), ([453857], 85)],
     [[1005], [99], [12345], [9090], [10]]),
    (33, "easy", "HammingDistance", "strArr", "",
     [([["coder", "codec"]], 1), ([["10101", "10100"]], 1)],
     [[["abc", "abc"]], [["hello", "world"]], [["1111", "0000"]], [["a", "b"]]]),
    # ------------------------------------------------------ lot 2 : moyennes
    (17, "medium", "LetterCount1", "str",
     "Les lettres sont comparées sans tenir compte de la casse ; la ponctuation est ignorée. "
     "Renvoyer le mot tel qu'il apparaît dans la phrase.",
     [(["Today, is the greatest day ever!"], "greatest"), (["Hello apple pie"], "Hello")],
     [["a bb ccc"], ["No words here"], ["abc def"], ["Mississippi is fun"], ["Aa bb"],
      ["Look at that book"]]),
    (31, "medium", "OverlappingRanges", "arr", "Les bornes des intervalles sont incluses.",
     [([[4, 10, 2, 6, 3]], "true"), ([[5, 8, 1, 3, 4]], "false")],
     [[[1, 5, 5, 10, 1]], [[1, 5, 6, 10, 1]], [[1, 10, 1, 10, 10]], [[1, 10, 1, 10, 11]],
      [[3, 4, 1, 9, 2]]]),
    (38, "medium", "EvenPairs", "str",
     "Une suite de chiffres consécutifs peut être coupée en deux nombres : dans « 812 », "
     "8 et 12 forment une paire de nombres pairs.",
     [(["f178svg3k19k46"], "true"), (["7r5gg812"], "true")],
     [["abc"], ["24"], ["2"], ["a13b25"], ["1357"], ["2468"], ["9z2468q"], ["9z1357q"]]),
    (46, "medium", "BinaryReversal", "str",
     "La représentation binaire est complétée à gauche par des zéros jusqu'à un multiple de 8 bits.",
     [(["47"], 244), (["213"], 171)],
     [["1"], ["255"], ["256"], ["300"], ["109"], ["65535"]]),
    (51, "medium", "BasicRomanNumerals", "str", "",
     [(["XXIV"], 24), (["XIX"], 19)],
     [["MCMXCIV"], ["III"], ["IX"], ["MMXXIV"], ["CDXLIV"], ["LVIII"]]),
    # -------------------------------------------------- lot 2 : difficiles
    (43, "hard", "LongestIncreasingSequence", "arr", "La sous-suite doit être strictement croissante.",
     [([[4, 3, 5, 1, 6]], 3), ([[9, 9, 4, 4, 5, 5, 6, 6, 7, 7]], 4)],
     [[[10, 9, 2, 5, 3, 7, 101, 18]], [[5, 4, 3, 2, 1]], [[1]], [[1, 3, 6, 7, 9, 4, 10, 5, 6]],
      [[2, 2, 2]]]),
    (29, "hard", "OffLineMinimum", "strArr",
     "Renvoyer les entiers retirés (un par « E »), dans l'ordre des retraits, séparés par des virgules.",
     [([["5", "4", "6", "E", "1", "7", "E", "E", "3", "2"]], "4,1,5"),
      ([["1", "2", "5", "7", "E", "E", "4", "E"]], "1,2,4")],
     [[["3", "1", "E", "2", "E", "E"]], [["9", "8", "7", "E", "6", "E", "E"]],
      [["2", "1", "E", "3", "E", "4", "E", "E"]], [["4", "E", "3", "E", "2", "E"]]]),
    (37, "hard", "WaveSorting", "arr", "Les inégalités sont strictes ; une valeur peut apparaître plusieurs fois.",
     [([[0, 1, 2, 4, 1, 4]], "true"), ([[1, 1]], "false")],
     [[[3, 1, 2]], [[1, 2, 3, 4, 5]], [[2, 2, 2, 3]], [[1, 1, 1, 1]], [[5, 1, 5, 1, 5, 1]], [[1, 2]],
      [[7, 7, 7, 8, 8, 8, 9]]]),
    (73, "hard", "ClosestEnemyII", "strArr",
     "Distance minimale en nombre de cases ; la grille se referme sur elle-même (haut/bas et gauche/droite).",
     [([["0000", "1000", "0002", "0002"]], 2), ([["000", "100", "200"]], 1)],
     [[["0000", "2010", "0000", "2000"]], [["1000", "0000", "0000", "0002"]], [["01", "00"]],
      [["00000", "00100", "00000", "20000", "00000"]], [["2", "1"]]]),
    (53, "hard", "CorrectPath", "str",
     "Grille 5x5 ; départ en haut à gauche, arrivée en bas à droite ; "
     "r = droite, l = gauche, u = haut, d = bas.",
     [(["r?d?drdd"], "rrdrdrdd"), (["???rrurdr?"], "dddrrurdrd")],
     [["?dl?rrdldrrr"], ["??lddrrdru?d"], ["?rdldrrruulurrd?d?"], ["rdldddrrr??r?d"],
      ["drdrrulu?rd?d?"]]),
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
            if func == "CorrectPath":
                assert len(R.correct_path_solutions(args[0])) == 1, f"solution non unique: {args}"
            if func == "WaveSorting":
                assert len(args[0]) <= 8, "trop long pour la force brute"
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
    data = json.dumps({"questions": questions}, ensure_ascii=False, indent=1)
    for out in OUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data, encoding="utf-8")
    print(f"{len(questions)} questions, "
          f"{sum(len(q['tests']) for q in questions)} tests -> " + ", ".join(str(o) for o in OUTS))


if __name__ == "__main__":
    build()
