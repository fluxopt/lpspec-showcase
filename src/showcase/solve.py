"""The solve job: one archive per scenario, written where the dashboard reads.

This is the only module that imports lpspec. It runs the pathway one period at
a time, each period inheriting the fleet the last one left, and archives the
spec, the sources and the answer under ``<runs>/<scenario>/``.

    showcase-solve --runs runs            # every scenario
    showcase-solve --runs runs base       # one of them
    showcase-solve --runs runs --replace  # over what a previous job wrote
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import lpspec as lps

from showcase.scenarios import SCENARIOS

MODEL = Path(__file__).parents[2] / 'models' / 'pathway.yaml'


def solve(scenario: str, runs: Path, *, replace: bool = False) -> Path:
    """Solve one scenario into ``runs/<scenario>/`` and return that directory.

    An archive is written whole, so a directory that already exists is refused
    unless ``replace`` is set, in which case it is removed first. Every period
    is asserted to have solved to optimality: a dashboard that quietly shows a
    partial pathway is worse than a job that fails.
    """
    target = runs / scenario
    if replace and target.exists():
        shutil.rmtree(target)
    runs_ = lps.solve_over(
        MODEL,
        SCENARIOS[scenario].sources(),
        lps.EachCoordinate('year'),
        carry={'existing': 'total'},
        archive=target,
    )
    conditions = runs_.objective['termination_condition'].to_list()
    assert all(c == 'optimal' for c in conditions), f'{scenario}: a period did not solve to optimality: {conditions}'
    return target


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='solve the pathway and archive each scenario')
    parser.add_argument('scenarios', nargs='*', choices=[*SCENARIOS, []], help='which to solve; all by default')
    parser.add_argument('--runs', type=Path, default=Path('runs'), help='the directory the dashboard reads')
    parser.add_argument('--replace', action='store_true', help='remove an archive that is already there')
    args = parser.parse_args(argv)
    for name in args.scenarios or list(SCENARIOS):
        target = solve(name, args.runs, replace=args.replace)
        print(f'{name}: archived at {target}')  # noqa: T201


if __name__ == '__main__':
    main()
