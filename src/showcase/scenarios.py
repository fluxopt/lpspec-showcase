"""The cases the planner solves: one set of sources per scenario.

A scenario is a function from nothing to the sources the model declares. Every
table that varies by period carries a ``year`` column, which is the axis the
solve job slices on; every other table passes through to each period unchanged.
The numbers are synthetic and chosen to make the periods answer differently.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import polars as pl

YEARS = [2030, 2035, 2040, 2045]
DAYS = ['winter', 'shoulder', 'summer']
HOURS = list(range(24))
GENERATORS = ['solar', 'wind', 'gas']

#: How many real days each typical day stands for; the three sum to a year.
WEIGHT = {'winter': 120.0, 'shoulder': 125.0, 'summer': 120.0}

#: Peak demand in MW on each typical day, before growth.
PEAK = {'winter': 100.0, 'shoulder': 80.0, 'summer': 90.0}

#: Demand relative to the base year; each period is solved against its own.
GROWTH = {2030: 1.0, 2035: 1.2, 2040: 1.4, 2045: 1.6}

#: Annualised build cost per MW. Solar and wind get cheaper; gas does not.
INVEST = {
    2030: {'solar': 42000.0, 'wind': 60000.0, 'gas': 55000.0},
    2035: {'solar': 34000.0, 'wind': 54000.0, 'gas': 55000.0},
    2040: {'solar': 28000.0, 'wind': 50000.0, 'gas': 55000.0},
    2045: {'solar': 24000.0, 'wind': 47000.0, 'gas': 55000.0},
}

#: Gas fuel cost per MWh, rising each period.
FUEL = {2030: 55.0, 2035: 70.0, 2040: 85.0, 2045: 100.0}

#: Tonnes of CO2 per MWh.
RATE = {'solar': 0.0, 'wind': 0.0, 'gas': 0.4}

#: The fleet the pathway starts from: some gas, and nothing else.
EXISTING = {'solar': 0.0, 'wind': 0.0, 'gas': 60.0}


def _load_shape(day: str, hour: int) -> float:
    """Demand as a fraction of the day's peak: a morning shoulder and an evening peak."""
    evening = math.exp(-((hour - 18) ** 2) / 12)
    morning = 0.6 * math.exp(-((hour - 8) ** 2) / 10)
    floor = 0.45 if day == 'winter' else 0.4
    return floor + (1 - floor) * max(evening, morning)


def _solar(day: str, hour: int) -> float:
    """A daylight bell, taller and wider in summer."""
    daylight = {'winter': 8.0, 'shoulder': 11.0, 'summer': 14.0}[day]
    peak = {'winter': 0.35, 'shoulder': 0.6, 'summer': 0.85}[day]
    half = daylight / 2
    if abs(hour - 12.5) >= half:
        return 0.0
    return peak * math.cos(math.pi * (hour - 12.5) / daylight)


def _wind(day: str, hour: int) -> float:
    """Windier in winter and at night, and never quite still."""
    base = {'winter': 0.45, 'shoulder': 0.35, 'summer': 0.25}[day]
    return base + 0.15 * math.cos(2 * math.pi * (hour - 3) / 24)


def sources(
    *,
    growth: dict[int, float] = GROWTH,
    invest: dict[int, dict[str, float]] = INVEST,
    fuel: dict[int, float] = FUEL,
    cap: dict[int, float] | None = None,
) -> dict[str, pl.DataFrame]:
    """The sources for one scenario, each keyword replacing one input.

    ``cap`` is the CO2 cap per year in tonnes; ``None`` leaves the cap far above
    what any fleet here could emit, so the constraint binds nowhere.
    """
    cap = cap or dict.fromkeys(YEARS, 1e12)
    return {
        'day': pl.DataFrame({'day': DAYS}),
        'hour': pl.DataFrame({'hour': HOURS}),
        'generator': pl.DataFrame({'generator': GENERATORS}),
        'weight': pl.DataFrame({'day': DAYS, 'value': [WEIGHT[d] for d in DAYS]}),
        'load': pl.DataFrame(
            [
                {'year': y, 'day': d, 'hour': h, 'value': round(PEAK[d] * growth[y] * _load_shape(d, h), 3)}
                for y in YEARS
                for d in DAYS
                for h in HOURS
            ]
        ),
        'avail': pl.DataFrame(
            [
                {'day': d, 'hour': h, 'generator': g, 'value': round(_avail(g, d, h), 4)}
                for d in DAYS
                for h in HOURS
                for g in GENERATORS
            ]
        ),
        'invest': pl.DataFrame([{'year': y, 'generator': g, 'value': invest[y][g]} for y in YEARS for g in GENERATORS]),
        'cost': pl.DataFrame(
            [{'year': y, 'generator': g, 'value': fuel[y] if g == 'gas' else 0.0} for y in YEARS for g in GENERATORS]
        ),
        'rate': pl.DataFrame({'generator': GENERATORS, 'value': [RATE[g] for g in GENERATORS]}),
        'cap': pl.DataFrame({'year': YEARS, 'value': [cap[y] for y in YEARS]}),
        'existing': pl.DataFrame({'generator': GENERATORS, 'value': [EXISTING[g] for g in GENERATORS]}),
    }


def _avail(generator: str, day: str, hour: int) -> float:
    if generator == 'solar':
        return _solar(day, hour)
    if generator == 'wind':
        return _wind(day, hour)
    return 1.0


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    sources: Callable[[], dict[str, pl.DataFrame]]


def _cheap_solar() -> dict[str, pl.DataFrame]:
    invest = {y: {**INVEST[y], 'solar': INVEST[y]['solar'] * 0.6} for y in YEARS}
    return sources(invest=invest)


def _high_demand() -> dict[str, pl.DataFrame]:
    return sources(growth={2030: 1.0, 2035: 1.35, 2040: 1.7, 2045: 2.1})


def _carbon_cap() -> dict[str, pl.DataFrame]:
    return sources(cap={2030: 120_000.0, 2035: 80_000.0, 2040: 40_000.0, 2045: 10_000.0})


SCENARIOS: dict[str, Scenario] = {
    s.name: s
    for s in [
        Scenario('base', 'the reference assumptions', sources),
        Scenario('cheap_solar', 'solar builds at 60% of the reference cost', _cheap_solar),
        Scenario('high_demand', 'demand grows twice as fast', _high_demand),
        Scenario('carbon_cap', 'a CO2 cap that tightens every period', _carbon_cap),
    ]
}
