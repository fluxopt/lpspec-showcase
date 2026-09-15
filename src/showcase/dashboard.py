"""The dashboard: a Streamlit page over the runs directory, importing no lpspec.

    SHOWCASE_RUNS=runs streamlit run src/showcase/dashboard.py

Three tabs read the model by name, because they tell the pathway's story. The
fourth, *Explore*, reads whatever the archives hold: it builds its selectors
off the dimension columns, so a different model needs no change here.
"""

from __future__ import annotations

import os
from pathlib import Path

import plotly.express as px
import polars as pl
import streamlit as st

from showcase import warehouse

RUNS = Path(os.environ.get('SHOWCASE_RUNS', 'runs'))

st.set_page_config(page_title='Pathway planner', layout='wide')
st.title('Capacity-expansion pathway')

if not any(RUNS.glob('*/answer/objective.parquet')):
    st.error(f'{RUNS.resolve()} holds no archive. Run `showcase-solve --runs {RUNS}` first.')
    st.stop()

records = warehouse.records(RUNS)
every_run = records['run'].unique().sort().to_list()
runs = st.sidebar.multiselect('Scenarios', every_run, default=every_run)
if not runs:
    st.stop()
records = records.filter(pl.col('run').is_in(runs))

pathway, dispatch, explore, provenance = st.tabs(['Pathway', 'Dispatch', 'Explore', 'Provenance'])

with pathway:
    left, right = st.columns(2)
    left.plotly_chart(
        px.line(records, x='year', y='objective', color='run', markers=True, title='Annualised cost per period'),
        width='stretch',
    )
    emissions = warehouse.frame(RUNS, 'expression', 'emissions').filter(pl.col('run').is_in(runs))
    right.plotly_chart(
        px.line(emissions, x='year', y='value', color='run', markers=True, title='CO2 emitted per period, t'),
        width='stretch',
    )
    chosen = st.selectbox('Fleet of', runs, key='fleet_run')
    total = warehouse.frame(RUNS, 'primal', 'total').filter(pl.col('run') == chosen)
    build = warehouse.frame(RUNS, 'primal', 'build').filter(pl.col('run') == chosen)
    left, right = st.columns(2)
    left.plotly_chart(
        px.bar(total, x='year', y='value', color='generator', title='Standing capacity, MW'), width='stretch'
    )
    right.plotly_chart(
        px.bar(build, x='year', y='value', color='generator', title='Built in the period, MW'), width='stretch'
    )

with dispatch:
    p = warehouse.frame(RUNS, 'primal', 'p')
    price = warehouse.frame(RUNS, 'dual', 'balance')
    load = warehouse.source(RUNS, 'load')
    one, two, three = st.columns(3)
    run = one.selectbox('Scenario', runs, key='dispatch_run')
    year = two.selectbox('Period', p['year'].unique().sort().to_list())
    day = three.selectbox('Typical day', p['day'].unique().to_list())
    here = (pl.col('run') == run) & (pl.col('year') == year) & (pl.col('day') == day)
    left, right = st.columns(2)
    output = px.area(p.filter(here), x='hour', y='value', color='generator', title='Output by hour, MW')
    met = load.filter(here).sort('hour')
    output.add_scatter(x=met['hour'], y=met['value'], name='load', mode='lines', line={'color': 'black', 'dash': 'dot'})
    left.plotly_chart(output, width='stretch')
    right.plotly_chart(
        px.line(price.filter(here), x='hour', y='value', markers=True, title='Price of one more MW of load'),
        width='stretch',
    )

with explore:
    st.caption('Everything the archives hold, keyed by whatever dimensions the model declared.')
    catalogue = warehouse.catalogue(RUNS)
    labels = [f'{row["kind"]}: {row["name"]}' for row in catalogue.iter_rows(named=True)]
    picked = catalogue.row(labels.index(st.selectbox('Quantity', labels)), named=True)
    table = warehouse.frame(RUNS, picked['kind'], picked['name']).filter(pl.col('run').is_in(runs))
    dims = [d for d in picked['dims'] if d != 'run']
    x = st.selectbox('Along', dims) if dims else None
    colour = st.selectbox('Coloured by', ['run', *[d for d in dims if d != x]])
    for dim in [d for d in dims if d not in {x, colour}]:
        labels_of = table[dim].unique().sort().to_list()
        table = table.filter(pl.col(dim) == st.selectbox(dim, labels_of))
    if x is None:
        st.plotly_chart(px.bar(table, x='run', y='value', title=picked['name']), width='stretch')
    else:
        st.plotly_chart(
            px.line(table.sort(x), x=x, y='value', color=colour, markers=True, title=picked['name']), width='stretch'
        )
    st.dataframe(table, width='stretch')

with provenance:
    st.subheader('Each solve')
    st.dataframe(
        records.select('run', 'year', 'status', 'termination_condition', 'objective', 'solved_at', 'spec_digest')
    )
    st.subheader('What it cost')
    st.dataframe(warehouse.metrics(RUNS).filter(pl.col('run').is_in(runs)))
    st.subheader('Which input differs')
    if len(runs) > 1:
        left, right = st.columns(2)
        base = left.selectbox('Between', runs, index=0)
        other = right.selectbox('and', runs, index=1)
        changed = warehouse.changed_inputs(RUNS, base, other)
        st.write(', '.join(f'`{s}`' for s in changed) if changed else 'the same bytes on every input')
    st.dataframe(warehouse.inputs(RUNS).filter(pl.col('run').is_in(runs)).pivot('run', index='source', values='digest'))
