"""Shape the runs directory into the one zip the pages read: every table, across every run.

Reads the directory the solve job wrote and solves nothing itself, so the site
is a reader of the archive like any other. ``SHOWCASE_RUNS`` names the
directory; the default is ``../runs``, which is the repository root's when the
site builds from ``site/``.
"""

import io
import json
import os
import sys
import zipfile
from pathlib import Path

from showcase import warehouse

runs = Path(os.environ.get('SHOWCASE_RUNS', '../runs'))
if not any(runs.glob('*/answer/objective.parquet')):
    sys.exit(f'{runs.resolve()} holds no archive: run `showcase-solve --runs {runs}` first')


def parquet(table) -> bytes:
    buffer = io.BytesIO()
    table.write_parquet(buffer)
    return buffer.getvalue()


catalogue = warehouse.catalogue(runs)
out = io.BytesIO()
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('objective.parquet', parquet(warehouse.records(runs)))
    zf.writestr('metrics.parquet', parquet(warehouse.metrics(runs)))
    zf.writestr('sources.parquet', parquet(warehouse.inputs(runs)))
    for row in catalogue.iter_rows(named=True):
        zf.writestr(f'{row["kind"]}/{row["name"]}.parquet', parquet(warehouse.frame(runs, row['kind'], row['name'])))
    zf.writestr('catalogue.json', json.dumps(catalogue.to_dicts(), indent=1))
    zf.writestr('model.yaml', next(iter(sorted(runs.glob('*/model.yaml')))).read_text())
sys.stdout.buffer.write(out.getvalue())
