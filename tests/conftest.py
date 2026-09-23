from pathlib import Path

import pytest

from showcase.scenarios import grid as grid_points
from showcase.solve import solve

SOLVED = ['base', 'cheap_solar']


@pytest.fixture(scope='session')
def runs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Two scenarios solved once for the whole session, into a directory the dashboard can read."""
    directory = tmp_path_factory.mktemp('runs')
    for name in SOLVED:
        solve(name, directory)
    return directory


#: Two corners of the what-if grid: no cap and the tightest, at the cheapest solar.
GRID = ['cap-none_solar-040', 'cap-0_solar-040']


@pytest.fixture(scope='session')
def grid(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A corner of the what-if grid, solved into a directory of its own as ``showcase-grid`` does."""
    directory = tmp_path_factory.mktemp('grid')
    for name in GRID:
        solve(name, directory, cases=grid_points())
    return directory
