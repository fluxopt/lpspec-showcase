# lpspec-showcase

A capacity-expansion planner built on [lpspec](https://github.com/fluxopt/lpspec),
shaped the way a production application is: a **solve job** that writes
archives, an **archive directory** that is the contract between the halves, and
an **interactive site** that reads the archives in the browser and never
imports lpspec. GitHub Actions runs the job and publishes the site to GitHub
Pages, so there is no server anywhere.

**Live:** <https://fluxopt.github.io/lpspec-showcase/>

```text
showcase-solve ──▶ runs/<scenario>/ ──▶ observable build ──▶ GitHub Pages
   (lpspec)          (parquet + yaml)      (one Python loader)   (DuckDB-WASM + Plot)
```

The point of the repository is the middle box. lpspec archives a solve as tidy
parquet: one file per variable, dual and named expression, keyed by the model's
own dimensions, with a `value` column. A directory of archives is therefore a
table per glob, and anything that reads parquet is already a client. The site
is one such client. So is a DuckDB shell, a notebook, or a BI tool pointed at
the same directory.

## Run it

Requires Python 3.12, [uv](https://docs.astral.sh/uv/) and Node 20 or later.
lpspec is not on PyPI yet, so the `solve` extra pins it to a git tag.

```bash
uv sync --all-extras
uv run showcase-solve --runs runs       # four scenarios, four periods each, a few seconds
uv run marimo export html notebooks/session.py -o site/src/session.html
cd site && npm ci && npm run dev        # the site, live, with the loader re-run on edit
```

`showcase-solve base` solves one scenario. An archive is written whole, so a
directory that already exists is refused; `--replace` removes it first.

## What the model is

[`models/pathway.yaml`](models/pathway.yaml) is one investment period of a
pathway: what to build, and how the fleet runs on three typical days of 24
hours. It never mentions the period. The solve job slices every source to one
year, runs the periods in order, and hands each period's standing capacity to
the next as its `existing` fleet. The addition `total == existing + build` is a
constraint in the file, where a reviewer reads it, and not arithmetic in the
driver.

The file also names three expressions, `capex`, `opex` and `emissions`, and a
`carbon` constraint over the last of them. Naming a quantity once means the
number the constraint bounds and the number the site plots are one definition.

Four scenarios live in [`src/showcase/scenarios.py`](src/showcase/scenarios.py),
each a function that returns the model's sources. Only data differs:

| scenario | what changes |
|---|---|
| `base` | the reference assumptions |
| `cheap_solar` | solar builds at 60% of the reference cost |
| `high_demand` | demand grows twice as fast |
| `carbon_cap` | a CO2 cap that tightens every period, and binds in the last |

## What the archive holds

Every `runs/<scenario>/` is what `lps.solve_over(…, archive=)` wrote:

```text
runs/base/
    model.yaml                          the spec, as solved
    sources/<name>.parquet              every input, as solved
    sources.parquet                     (run, source, digest)
    axis.json                           how the sources were sliced
    answer/
        objective.parquet               (year, status, termination_condition, objective, …, run)
        metrics.parquet                 (year, rows, columns, nonzeros, build_seconds, solve_seconds, run)
        primal/<variable>/<slice>.parquet     (year, <dims…>, value)
        dual/<constraint>/<slice>.parquet     the same shape, for a shadow price
        expression/<name>/<slice>.parquet     the same shape, for a named expression
```

Three rules make a directory of these a warehouse, and
[`src/showcase/warehouse.py`](src/showcase/warehouse.py) is the whole Python
client:

- **The record tables carry `run`** on every row, so they concatenate across
  archives with `read_parquet('runs/*/answer/objective.parquet')`.
- **A value frame carries the model's columns only.** `run` is derived from
  the path, which DuckDB's `filename = true` gives for free.
- **The catalogue is the tree.** Which quantities exist, and which dimensions
  key each, is read off the directory names and the parquet schema. Nothing is
  declared twice.

From a DuckDB shell, the same directory:

```sql
select run, year, objective
from read_parquet('runs/*/answer/objective.parquet', union_by_name = true)
order by run, year;
```

## How the site reads it

The site is an [Observable Framework](https://observablehq.com/framework/)
app under [`site/`](site/). Its one data loader,
[`site/src/data/runs.zip.py`](site/src/data/runs.zip.py), runs the warehouse
queries above at build time and ships the result as a zip of parquet files,
one per quantity across every run. Each page registers the tables it needs in
its front matter and queries them with SQL, run by DuckDB-WASM in the
browser; the charts are [Observable Plot](https://observablehq.com/plot/), and
every input re-runs only the cells that depend on it.

A second loader, [`site/src/model.md.py`](site/src/model.md.py), prints a
whole page: the spec out of the archive, typeset as equations by the
language's own `to_markdown`, in the notation
[`models/pathway.symbols.yaml`](models/pathway.symbols.yaml) declares. A
symbol that names nothing in the model fails the build. It imports [math-spec](https://github.com/energy-models/math-spec),
the language package, which has no solver in it. No data binds and nothing is
solved to produce that page, so the math it shows is exactly what the YAML
states, and the other pages show what the solver made of it.

Three pages know the model by name, because they tell its story. **Pathway**
leads with four headline numbers, breaks the cost into building and running
per technology, sets emissions against the cap, and compares two scenarios as
a difference; clicking a period there selects it, and a link carries the
scenario and period into **Dispatch**, where a slider moves through the
periods over all three typical days with the net load drawn, and a heatmap
shows the price by hour and period. **Provenance** shows what was solved and
what differs between runs. **Explore** knows nothing. It lists
every quantity in the catalogue, offers the dimensions it finds as the axis,
the colour and the filters, and plots. Point the solve job at a different
lpspec model and that page shows it unchanged. That is the property this
repository exists to demonstrate.

## The modelling session

The site is what lpspec produces unattended. [`notebooks/session.py`](notebooks/session.py)
is the other half: a [marimo](https://marimo.io) notebook in which the model
is a document you edit by hand. A dispatch model sits in a code cell; change
it and the typeset math, the validation and the solve all re-run, because
every cell that reads it depends on it. A data editor changes the cost table,
and two sliders re-solve the pathway with a different cap and solar cost.

```bash
uv run marimo edit notebooks/session.py
```

The site's **Session** page embeds the notebook as it ran at the last build,
outputs included and controls inert, so the story is readable without a
kernel. `marimo export html` writes that file in CI before the site builds.

## What the checks say

`uv run pytest` solves two scenarios into a temporary directory and asserts:

- the archive holds the tree above, every period solved to optimality, and
  each period started from the fleet the last one left;
- the warehouse queries name the run on every row, list the catalogue from the
  tree, and name `invest` as the one input `cheap_solar` changed;
- nothing past the solve job imports lpspec; the site's data loader ships every
  table the pages read, or says what is missing; and the model page prints the
  archived spec as TeX in the site's own delimiters;
- the notebook runs top to bottom and exports with both solves optimal.

CI runs the same, then the pipeline end to end: the job, then the site build.
A push to `main` also deploys the site to GitHub Pages.

## What it is not

There is no hosted API, no scheduler beyond the workflow, no database and no
authentication. Each would sit on the same contract, and none is needed to
show it. The numbers are synthetic and chosen so that the periods and the
scenarios answer differently.
