"""The what-if grid: one archive per point, whose inputs a reader takes from the sources rather than the name."""

from pathlib import Path

import polars as pl
from conftest import GRID

from showcase import warehouse
from showcase.scenarios import GRID_CAPS, GRID_SOLAR, INVEST, SCENARIOS, YEARS
from showcase.scenarios import grid as grid_points


def test_every_point_is_a_scenario_of_the_same_model():
    points = grid_points()
    assert len(points) == len(GRID_CAPS) * len(GRID_SOLAR)
    names = set(SCENARIOS['base'].sources())
    for point in points.values():
        assert set(point.sources()) == names, f'{point.name} supplies exactly the names the model declares'


def test_a_point_caps_only_the_last_period():
    sources = grid_points()['cap-10000_solar-060'].sources()
    cap = dict(sources['cap'].select('year', 'value').iter_rows())
    assert cap[YEARS[-1]] == 10_000
    assert all(cap[y] >= 1e12 for y in YEARS[:-1]), 'the earlier periods are left uncapped'
    solar = sources['invest'].filter(pl.col('generator') == 'solar')
    assert dict(solar.select('year', 'value').iter_rows()) == {y: INVEST[y]['solar'] * 0.6 for y in YEARS}


def test_the_archive_holds_the_inputs_the_page_reads(grid: Path):
    """The page keys each point by the cap and solar cost in the archived sources, not by parsing its name."""
    cap = warehouse.frame(grid, 'source', 'cap').filter(pl.col('year') == YEARS[-1])
    assert dict(cap.select('run', 'value').iter_rows()) == {'cap-none_solar-040': 1e12, 'cap-0_solar-040': 0.0}
    records = warehouse.records(grid)
    assert set(records['run']) == set(GRID)
    assert records['termination_condition'].unique().to_list() == ['optimal']


def test_the_carbon_price_is_zero_until_the_cap_binds(grid: Path):
    price = warehouse.frame(grid, 'dual', 'carbon').filter(pl.col('year') == YEARS[-1])
    by_run = dict(price.select('run', 'value').iter_rows())
    assert by_run['cap-none_solar-040'] == 0
    assert by_run['cap-0_solar-040'] < 0, 'a binding cap carries a price, which the page shows negated'
