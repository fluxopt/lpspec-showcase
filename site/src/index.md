---
title: Pathway
sql:
  objective: ./data/runs/objective.parquet
  total: ./data/runs/primal/total.parquet
  build: ./data/runs/primal/build.parquet
  emissions: ./data/runs/expression/emissions.parquet
---

# Capacity-expansion pathway

One model, four scenarios, each solved one investment period at a time with the fleet carried forward. Every number on this page is a query over the parquet that [lpspec](https://github.com/fluxopt/lpspec) archived, run by DuckDB in your browser.

```js
import {colorScale, surface} from "./components/palette.js";
```

```sql id=runs
select distinct run from objective order by run
```

```sql id=cost
select run, year::integer as year, objective as value from objective order by run, year
```

```sql id=co2
select run, year::integer as year, value from emissions order by run, year
```

```js
const scenarios = runs.toArray().map((d) => d.run);
const chosen = view(Inputs.checkbox(scenarios, {value: scenarios, label: "Scenarios"}));
const fleetOf = view(Inputs.select(scenarios, {label: "Fleet of"}));
```

```js
const pick = (table) => table.toArray().filter((d) => chosen.includes(d.run));

function byPeriod(rows, {label, width}) {
  return Plot.plot({
    width,
    height: 300,
    marginLeft: 60,
    x: {label: "period", tickFormat: "d", ticks: [...new Set(rows.map((d) => d.year))]},
    y: {grid: true, label, tickFormat: "s", zero: true},
    color: colorScale(scenarios, dark),
    marks: [
      Plot.lineY(rows, {x: "year", y: "value", stroke: "run", strokeWidth: 2}),
      Plot.dot(rows, {x: "year", y: "value", fill: "run", r: 4, stroke: surface, strokeWidth: 2}),
      Plot.ruleX(rows, Plot.pointerX({x: "year", stroke: "var(--theme-foreground-faint)"})),
      Plot.tip(rows, Plot.pointerX({x: "year", y: "value", channels: {scenario: "run"}, format: {x: "d", y: ",.0f", fill: false}})),
    ],
  });
}
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Annualised cost per period</h2>
    ${resize((width) => byPeriod(pick(cost), {label: "cost", width}))}
  </div>
  <div class="card">
    <h2>CO₂ emitted per period, t</h2>
    ${resize((width) => byPeriod(pick(co2), {label: "tonnes", width}))}
  </div>
</div>

```sql id=fleet
select year::integer as year, generator, value from total where run = ${fleetOf} order by year, generator
```

```sql id=built
select year::integer as year, generator, value from build where run = ${fleetOf} order by year, generator
```

```js
const technologies = [...new Set(fleet.toArray().map((d) => d.generator))];

function stacked(rows, {label, width}) {
  return Plot.plot({
    width,
    height: 300,
    marginLeft: 60,
    x: {label: "period", tickFormat: "d"},
    y: {grid: true, label},
    color: colorScale(technologies, dark),
    marks: [
      Plot.barY(rows, {x: "year", y: "value", fill: "generator", stroke: surface, strokeWidth: 2, tip: {format: {x: "d", y: ",.1f"}}}),
    ],
  });
}
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Standing capacity, MW — ${fleetOf}</h2>
    ${resize((width) => stacked(fleet.toArray(), {label: "MW", width}))}
  </div>
  <div class="card">
    <h2>Built in the period, MW — ${fleetOf}</h2>
    ${resize((width) => stacked(built.toArray(), {label: "MW", width}))}
  </div>
</div>

<div class="card">
  <h2>Every solve</h2>
  ${Inputs.table(pick(cost), {columns: ["run", "year", "value"], header: {value: "objective"}, format: {year: (d) => String(d), value: (d) => d.toLocaleString("en", {maximumFractionDigits: 0})}})}
</div>
