"""What the S22 benchmark design can detect, and what it costs.

    python3 -I design.py [--sims 4000] [--seed 20261123]

Score: each run of a task is graded on 5 independent items, so a run scores 0, 0.2, ... 1.0.
Analysis: per task, d = mean score with the framework minus mean score without it; the tasks
are the sample, not the runs and not the items (items of one run and runs of one task are
correlated). The verdict, from the 95% interval of the mean of d and the margin of 10 points:

    benefit          interval above 0 and the mean at least the margin
    harm             interval below 0
    not worth it     upper end below the margin
    inconclusive     anything else

The margin (what is worth paying for) is deliberately lower than the effect the design is sized
to detect. S19 set both to 20 points and could not pass more often than half the time.

Two stages: every task once; only if that is inconclusive, every task a second time. Each look
uses Pocock's boundary (two-sided 0.0294), so looking twice keeps the overall 5%.

The simulation's assumptions are not measurements: how much the effect differs between tasks
(tau), how alike the items of one run are (rho) and how many tasks the control already solves
(ceiling). They are varied below. Run costs and their noise are measured (S18-S21).
"""
from __future__ import annotations

import argparse
from math import exp, sqrt
import random

MARGIN = 0.10
LARGE = 0.25  # the effect the design is sized to detect
ITEMS = 5
# Two-sided 95% critical values of Student's t by degrees of freedom.
T95 = {5: 2.571, 7: 2.365, 11: 2.201, 15: 2.131, 17: 2.110, 19: 2.093, 23: 2.069, 29: 2.045, 35: 2.030}
# Two-sided 0.0294 (Pocock, two looks).
T_LOOK = {15: 2.408, 17: 2.379, 23: 2.323}
# t for 80% power, one-sided.
T80 = {5: 0.920, 7: 0.896, 11: 0.876, 15: 0.866, 17: 0.863, 19: 0.861, 23: 0.858, 29: 0.854, 35: 0.852}

# Measured, USD per run of Sonnet 5.5 without the framework (isolated S19-S21, S18 for the small
# tasks): a one-session task and a task of two sessions. Cost formula checked against every
# recorded session: median error 0.0%, cache writes at twice the input price (one-hour cache).
ONE_SESSION, TWO_SESSIONS = 0.08, 0.14
WITH_FRAMEWORK = 1.20  # S18: 1.17 to 1.24 on one-session tasks
PRICE = {"haiku-5-5": 0.055, "sonnet-5-5": 1.0, "opus-5-5": 2.0}  # same tokens, relative to Sonnet
NOISE = 0.10  # run-to-run SD of log cost: 0.07 on small tasks, 0.18 on real-bug fixes
COST_TAU = 0.10  # SD between tasks of the log cost ratio (S18)


def clip(value: float) -> float:
    return min(0.98, max(0.02, value))


def run_score(rng: random.Random, p: float, rho: float) -> float:
    q = rng.betavariate(p * (1 - rho) / rho, (1 - p) * (1 - rho) / rho) if rho else p
    return sum(rng.random() < q for _ in range(ITEMS)) / ITEMS


def population(rng, tasks, effect, tau, ceiling) -> list[tuple[float, float]]:
    """The true score of each task without and with the framework."""
    found = []
    for _ in range(tasks):
        if rng.random() < ceiling:
            base = treated = 0.95  # nothing left to gain
        else:
            base = rng.uniform(0.2, 0.65)
            change = effect / (1 - ceiling) + rng.gauss(0, tau)
            treated = clip(base + change)
        found.append((base, treated))
    return found


def measure(rng, truths, repeats, rho) -> list[float]:
    differences = []
    for base, treated in truths:
        control = sum(run_score(rng, base, rho) for _ in range(repeats)) / repeats
        framework = sum(run_score(rng, treated, rho) for _ in range(repeats)) / repeats
        differences.append(framework - control)
    return differences


def one_trial(rng, tasks, repeats, effect, tau, rho, ceiling) -> tuple[list[float], float]:
    truths = population(rng, tasks, effect, tau, ceiling)
    return measure(rng, truths, repeats, rho), sum(new - old for old, new in truths) / tasks


def interval(differences: list[float], critical: dict[int, float] = T95) -> tuple[float, float]:
    n = len(differences)
    mean = sum(differences) / n
    sd = sqrt(sum((d - mean) ** 2 for d in differences) / (n - 1))
    return mean, critical[n - 1] * sd / sqrt(n)


def verdict(differences: list[float], critical: dict[int, float] = T95) -> str:
    mean, half = interval(differences, critical)
    if mean - half > 0 and mean >= MARGIN - 1e-9:
        return "benefit"
    if mean + half < 0:
        return "harm"
    if mean + half < MARGIN:
        return "not worth it"
    return "inconclusive"


def simulate(seed, sims, tasks, repeats, effect, tau=0.15, rho=0.4, ceiling=0.25) -> dict:
    rng = random.Random(f"{seed}/{tasks}/{repeats}/{effect}/{tau}/{rho}/{ceiling}")
    counts = {"benefit": 0, "harm": 0, "not worth it": 0, "inconclusive": 0}
    halves, true = [], 0.0
    for _ in range(sims):
        differences, realised = one_trial(rng, tasks, repeats, effect, tau, rho, ceiling)
        counts[verdict(differences)] += 1
        halves.append(interval(differences)[1])
        true += realised
    halves.sort()
    return {**{key: value / sims for key, value in counts.items()}, "half": halves[sims // 2], "true": true / sims}


def two_stages(seed, sims, tasks, effect, tau=0.15, rho=0.4, ceiling=0.25) -> dict:
    rng = random.Random(f"two/{seed}/{tasks}/{effect}/{tau}/{rho}/{ceiling}")
    counts = {"benefit": 0, "harm": 0, "not worth it": 0, "inconclusive": 0}
    second = small = 0
    true = 0.0
    for _ in range(sims):
        truths = population(rng, tasks, effect, tau, ceiling)
        true += sum(new - old for old, new in truths) / tasks
        used = measure(rng, truths, 1, rho)
        found = verdict(used, T_LOOK)
        if found == "inconclusive":
            second += 1
            again = measure(rng, truths, 1, rho)
            used = [(a + b) / 2 for a, b in zip(used, again)]
            found = verdict(used, T_LOOK)
        mean, half = interval(used, T_LOOK)
        small += mean + half < LARGE  # whatever the verdict, a large benefit is ruled out
        counts[found] += 1
    return {**{key: value / sims for key, value in counts.items()}, "second": second / sims, "small": small / sims, "true": true / sims}


def suite_cost(tasks: int, repeats: int, negatives: int, model: str, arms: tuple[float, ...] = (1.0, WITH_FRAMEWORK)) -> float:
    """A quarter of the tasks takes two sessions; the negative controls run once in each arm."""
    runs = tasks * repeats + negatives
    per_run = 0.75 * ONE_SESSION + 0.25 * TWO_SESSIONS
    return runs * per_run * sum(arms) * PRICE[model]


def cost_resolution(tasks: int, repeats: int) -> tuple[float, float]:
    """95% half-width of the cost ratio, and the smallest difference detected 80% of the time."""
    error = sqrt(COST_TAU ** 2 / tasks + 2 * NOISE ** 2 / (repeats * tasks))
    return exp(T95[tasks - 1] * error) - 1, exp((T95[tasks - 1] + T80[tasks - 1]) * error) - 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sims", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=20261123)
    args = parser.parse_args()
    go = lambda *a, **k: simulate(args.seed, args.sims, *a, **k)

    print("1. Many tasks or many repeats (tau 0.15, rho 0.4, 25% of tasks at the control's ceiling)")
    print("tasks reps runs | says benefit when true effect is 0 / +10 / +20 / +25 / +30 | no effect: says not worth it | +/-  ")
    for tasks, repeats in ((8, 1), (8, 3), (12, 1), (12, 2), (12, 3), (16, 1), (16, 2), (18, 2), (20, 1), (24, 1), (24, 2), (36, 1)):
        results = {effect: go(tasks, repeats, effect) for effect in (0.0, 0.10, 0.20, 0.25, 0.30)}
        benefit = " / ".join(f"{results[effect]['benefit']:.2f}" for effect in results)
        print(f"{tasks:5} {repeats:4} {2 * tasks * repeats:4} | {benefit} | {results[0.0]['not worth it']:.2f} | {results[0.0]['half']:.3f}")

    print("\n2. If the assumptions are wrong")
    print("tasks reps   tau  rho ceiling | false benefit | realised effect -> says benefit (asked +20) | (asked +30)")
    for tasks, repeats in ((12, 2), (24, 1), (24, 2)):
        for tau, rho, ceiling in ((0.05, 0.2, 0.25), (0.15, 0.4, 0.0), (0.15, 0.4, 0.5), (0.25, 0.4, 0.25), (0.15, 0.7, 0.25), (0.25, 0.7, 0.25)):
            none, some, large = (go(tasks, repeats, effect, tau, rho, ceiling) for effect in (0.0, 0.20, 0.30))
            print(f"{tasks:5} {repeats:4}  {tau:.2f} {rho:.2f}  {ceiling:.2f}   | {none['benefit']:.3f} | "
                  f"{some['true']:+.2f} -> {some['benefit']:.2f} | {large['true']:+.2f} -> {large['benefit']:.2f}")

    print("\n3. Cost of the framework: 95% half-width / detected 80% of the time")
    for tasks, repeats in ((12, 2), (16, 1), (24, 1), (24, 2)):
        half, detected = cost_resolution(tasks, repeats)
        print(f"{tasks:5} {repeats:4} | +/-{half:.1%} / {detected:.1%}")

    print("\n4. Expected spend in USD, without or with the framework (2 arms); 6 negative controls once per arm")
    for tasks, repeats in ((12, 2), (16, 1), (24, 1), (24, 2), (36, 1)):
        spend = " ".join(f"{model} {suite_cost(tasks, repeats, 6, model):6.2f}" for model in PRICE)
        three = suite_cost(tasks, repeats, 6, "opus-5-5", (1.0, 1.10, WITH_FRAMEWORK))
        print(f"{tasks:5} {repeats:4} | {spend} | opus with a rules-only arm {three:6.2f}")

    print("\n5. Two stages, 24 tasks: one repeat, a second one only if inconclusive (Opus 5.5)")
    print(" tau  rho ceiling effect realised | benefit harm not-worth inconclusive | rules out +25 | needs stage 2 | expected USD")
    first, both = suite_cost(24, 1, 6, "opus-5-5"), suite_cost(24, 2, 6, "opus-5-5")
    for tau, rho, ceiling in ((0.15, 0.4, 0.25), (0.05, 0.2, 0.25), (0.25, 0.4, 0.25), (0.15, 0.7, 0.25), (0.25, 0.7, 0.25), (0.15, 0.4, 0.5)):
        for effect in (0.0, 0.10, 0.20, 0.25, 0.30):
            found = two_stages(args.seed, args.sims, 24, effect, tau, rho, ceiling)
            spend = first + found["second"] * (both - first)
            print(f"{tau:.2f} {rho:.2f}  {ceiling:.2f}   +{effect:.2f}   {found['true']:+.2f}   | {found['benefit']:.3f} {found['harm']:.3f} "
                  f"{found['not worth it']:.3f} {found['inconclusive']:.3f} | {found['small']:.3f} | {found['second']:.2f} | {spend:5.2f}")


if __name__ == "__main__":
    main()
