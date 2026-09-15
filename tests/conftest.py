from pathlib import Path

import pytest

from showcase.solve import solve

SOLVED = ['base', 'cheap_solar']


@pytest.fixture(scope='session')
def runs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Two scenarios solved once for the whole session, into a directory the dashboard can read."""
    directory = tmp_path_factory.mktemp('runs')
    for name in SOLVED:
        solve(name, directory)
    return directory
