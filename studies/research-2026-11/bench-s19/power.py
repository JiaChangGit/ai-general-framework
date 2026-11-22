"""What the thresholds of M-s19.md can detect at a given number of runs per group.

    python3 -I power.py

Runs are treated as independent with one pass rate per group. The "no task 2 or more worse"
clause is left out, so the chance of saying 有好處 is an upper bound.
"""
from functools import lru_cache
from math import comb


def pmf(n: int, k: int, p: float) -> float:
    return comb(n, k) * p ** k * (1 - p) ** (n - k)


@lru_cache(None)
def fisher(a: int, n: int, b: int) -> float:
    passed = a + b

    def ways(x: int) -> int:
        return comb(n, x) * comb(n, passed - x) if 0 <= passed - x <= n else 0

    observed = ways(a)
    return sum(ways(x) for x in range(min(n, passed) + 1) if ways(x) <= observed) / comb(2 * n, passed)


def chances(n: int, base: float, new: float) -> tuple[float, float, float]:
    """Chance of +20 points observed, of that with p<0.05, and of any significant improvement."""
    threshold = conclusive = significant = 0.0
    for a in range(n + 1):
        for b in range(a + 1, n + 1):
            chance = pmf(n, a, base) * pmf(n, b, new)
            over = (b - a) * 5 >= n
            if over:
                threshold += chance
            if fisher(a, n, b) < 0.05:
                significant += chance
                if over:
                    conclusive += chance
    return threshold, conclusive, significant


def main() -> None:
    print("runs/group  control  no effect: says benefit  +20 true: says benefit  ...and p<0.05  any p<0.05")
    for n in (10, 20, 108):
        for base in (0.33, 0.5):
            none, real = chances(n, base, base), chances(n, base, base + 0.2)
            print(f"{n:10}  {base:7.2f}  {none[0]:23.2f}  {real[0]:22.2f}  {real[1]:13.2f}  {real[2]:10.2f}")


if __name__ == "__main__":
    main()
