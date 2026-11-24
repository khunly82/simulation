"""Solutions de référence (jamais livrées aux candidats).

Servent à calculer les sorties attendues des cas de test cachés et à vérifier
que la banque de questions est cohérente (tests/test_bank.py).
Chaque fonction porte le nom exact de la fonction demandée au candidat.
"""
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from itertools import combinations
import re


def FirstFactorial(num):
    r = 1
    for i in range(2, num + 1):
        r *= i
    return r


def LetterChanges(str):
    out = []
    for c in str:
        if c.isalpha():
            c = chr((ord(c.lower()) - 97 + 1) % 26 + 97)
            if c in "aeiou":
                c = c.upper()
        out.append(c)
    return "".join(out)


def TimeConvert(num):
    return f"{num // 60}:{num % 60}"


def SecondGreatLow(arr):
    u = sorted(set(arr))
    return f"{u[1]} {u[-2]}"


def DashInsert(str):
    out = str[0]
    for prev, cur in zip(str, str[1:]):
        if int(prev) % 2 == 1 and int(cur) % 2 == 1:
            out += "-"
        out += cur
    return out


def AdditivePersistence(num):
    n = 0
    while num >= 10:
        num = sum(int(d) for d in f"{num}")
        n += 1
    return n


def ArithGeo(arr):
    if all(arr[i + 1] - arr[i] == arr[1] - arr[0] for i in range(len(arr) - 1)):
        return "Arithmetic"
    if all(arr[i + 1] * arr[i - 1] == arr[i] ** 2 for i in range(1, len(arr) - 1)):
        return "Geometric"
    return -1


def MeanMode(arr):
    mode, _ = Counter(arr).most_common(1)[0]
    return 1 if sum(arr) == mode * len(arr) else 0


def CountingMinutes1(str):
    def parse(t):
        hm, ap = t[:-2], t[-2:]
        h, m = (int(x) for x in hm.split(":"))
        h %= 12
        if ap == "pm":
            h += 12
        return h * 60 + m

    a, b = str.split("-")
    return (parse(b) - parse(a)) % 1440


def DivisionStringified(num1, num2):
    q = (Decimal(num1) / Decimal(num2)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return f"{int(q):,}"


def ThirdGreatest(strArr):
    return sorted(strArr, key=len, reverse=True)[2]


def ArrayAddition(arr):
    arr = list(arr)
    big = max(arr)
    arr.remove(big)
    sums = {0}
    for x in arr:
        sums |= {s + x for s in sums}
    # sous-ensemble non vide
    for r in range(1, len(arr) + 1):
        for c in combinations(arr, r):
            if sum(c) == big:
                return "true"
    return "false"


def ChangingSequence(arr):
    first = arr[1] - arr[0] > 0
    for i in range(1, len(arr) - 1):
        if (arr[i + 1] - arr[i] > 0) != first:
            return i
    return -1


def TwoSum(arr):
    pairs = []
    for i in range(1, len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] + arr[j] == arr[0]:
                pairs.append(f"{arr[i]},{arr[j]}")
    return " ".join(pairs) if pairs else -1


def TimeDifference(strArr):
    def parse(t):
        hm, ap = t[:-2], t[-2:]
        h, m = (int(x) for x in hm.split(":"))
        h %= 12
        if ap == "pm":
            h += 12
        return h * 60 + m

    ts = sorted(parse(t) for t in strArr)
    diffs = [b - a for a, b in zip(ts, ts[1:])]
    diffs.append(ts[0] + 1440 - ts[-1])
    return min(diffs)


def _is_pal(s):
    return s == s[::-1]


def PalindromeCreator(str):
    if _is_pal(str):
        return "palindrome"
    n = len(str)
    for k in (1, 2):
        found = []
        for idx in combinations(range(n), k):
            rest = "".join(c for i, c in enumerate(str) if i not in idx)
            if len(rest) >= 3 and _is_pal(rest):
                found.append("".join(str[i] for i in idx))
        if found:
            return found[0]
    return "not possible"


def palindrome_creator_candidates(s):
    """Utilisé au build pour vérifier qu'une entrée n'a qu'une réponse possible."""
    n = len(s)
    for k in (1, 2):
        found = set()
        for idx in combinations(range(n), k):
            rest = "".join(c for i, c in enumerate(s) if i not in idx)
            if len(rest) >= 3 and _is_pal(rest):
                found.add("".join(s[i] for i in idx))
        if found:
            return found
    return set()


def _ints(s):
    return [int(x) for x in re.findall(r"\d+", s)]


def scale_candidates(strArr):
    left, right = _ints(strArr[0])
    ws = _ints(strArr[1])
    diff = abs(left - right)
    singles = {(w,) for w in ws if w == diff}
    if singles:
        return singles
    pairs = set()
    for a, b in combinations(ws, 2):
        if a + b == diff or abs(a - b) == diff:
            pairs.add(tuple(sorted((a, b))))
    return pairs


def ScaleBalancing(strArr):
    c = scale_candidates(strArr)
    if not c:
        return "not possible"
    return ",".join(f"{x}" for x in sorted(c)[0])


def StringPeriods(str):
    n = len(str)
    for size in range(n // 2, 0, -1):
        if n % size == 0 and str == str[:size] * (n // size):
            return str[:size]
    return -1


def VowelSquare(strArr):
    for r in range(len(strArr) - 1):
        for c in range(len(strArr[r]) - 1):
            if all(
                strArr[rr][cc] in "aeiou"
                for rr in (r, r + 1)
                for cc in (c, c + 1)
            ):
                return f"{r}-{c}"
    return "not found"


def _median(window):
    s = sorted(window)
    n = len(s)
    if n % 2:
        return Decimal(s[n // 2])
    return (Decimal(s[n // 2 - 1]) + Decimal(s[n // 2])) / 2


def MovingMedian(arr):
    n, nums = arr[0], arr[1:]
    out = []
    for i in range(len(nums)):
        m = _median(nums[max(0, i - n + 1): i + 1])
        out.append(f"{m.normalize():f}")
    return ",".join(out)


def moving_median_is_integral(arr):
    n, nums = arr[0], arr[1:]
    return all(
        _median(nums[max(0, i - n + 1): i + 1]) == _median(nums[max(0, i - n + 1): i + 1]).to_integral_value()
        for i in range(len(nums))
    )


def NextPalindrome(num):
    n = num + 1
    while True:
        s = f"{n}"
        if s == s[::-1]:
            return n
        n += 1


def ProductDigits(num):
    best = None
    for a in range(1, int(num ** 0.5) + 1):
        if num % a == 0:
            d = len(f"{a}") + len(f"{num // a}")
            best = d if best is None else min(best, d)
    return best
