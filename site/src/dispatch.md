---
title: Dispatch
sql:
  p: ./data/runs/primal/p.parquet
  price: ./data/runs/dual/balance.parquet
  load: ./data/runs/source/load.parquet
  rate: ./data/runs/source/rate.parquet
---

<style>
.inputs { display: flex; flex-wrap: wrap; gap: 0.25rem 2rem; align-items: center; margin: 1rem 0; }
</style>

# How the fleet runs

Output by technology over each typical day, the load it meets, and what is left for dispatchable plant once zero-carbon output is netted off. Move the period to watch the midday net load sink as solar is built and the evening peak stay. The price is the dual of the balance constraint: what one more MW of load would cost in that hour.

```js
import {colorScale, surface} from "./components/palette.js";
import {sequential} from "./components/format.js";
const params = new URLSearchParams(location.search);
```

```sql id=runs
select distinct run from p order by run
```

```sql id=years
select distinct year::integer as year from p order by year
```

```sql id=rates
select run, generator, value from rate
```

```js
const scenarios = runs.toArray().map((d) => d.run);
const periods = years.toArray().map((d) => d.year);
const wanted = Number(params.get("year"));
```

<div class="inputs">

```js
const run = view(Inputs.select(scenarios, {label: "Scenario", value: scenarios.includes(params.get("run")) ? params.get("run") : scenarios[0]}));
```

```js
const step = view(Inputs.range([0, periods.length - 1], {label: "Period", step: 1, value: Math.max(0, periods.indexOf(wanted)), format: (i) => String(periods[i])}));
```

</div>

```js
const year = periods[step];
```

```sql id=output
select day, hour::integer as hour, generator, value from p where run = ${run} and year = ${year} order by day, hour, generator
```

```sql id=met
select day, hour::integer as hour, value from load where run = ${run} and year = ${year} order by day, hour
```

```sql id=marginal
select day, hour::integer as hour, value from price where run = ${run} and year = ${year} order by day, hour
```

```sql id=surface_
select year::integer as year, day, hour::integer as hour, value from price where run = ${run} order by year, day, hour
```

```js
const technologies = [...new Set(output.toArray().map((d) => d.generator))].sort();
const days = [...new Set(output.toArray().map((d) => d.day))];
const zeroCarbon = new Set(rates.toArray().filter((d) => d.run === run && d.value === 0).map((d) => d.generator));
const loadRows = met.toArray();
const clean = d3.rollup(output.toArray().filter((d) => zeroCarbon.has(d.generator)), (v) => d3.sum(v, (d) => d.value), (d) => d.day, (d) => d.hour);
const net = loadRows.map((d) => ({day: d.day, hour: d.hour, value: d.value - (clean.get(d.day)?.get(d.hour) ?? 0)}));
```

<div class="card">
  <h2>Output by hour, MW — ${run}, ${year}</h2>
  <p class="muted">Dashed: the load. Dotted: the net load after ${[...zeroCarbon].join(" and ") || "nothing"}, which is what the rest of the fleet has to cover.</p>
  ${resize((width) => Plot.plot({
    width, height: 320, marginLeft: 50, marginRight: 20,
    x: {label: "hour", ticks: 6},
    y: {grid: true, label: "MW"},
    fx: {label: null, domain: days},
    color: colorScale(technologies, dark),
    marks: [
      Plot.areaY(output, {x: "hour", y: "value", fx: "day", fill: "generator", stroke: surface, strokeWidth: 1.5, curve: "monotone-x"}),
      Plot.lineY(loadRows, {x: "hour", y: "value", fx: "day", stroke: "var(--theme-foreground)", strokeWidth: 2, strokeDasharray: "4 3", curve: "monotone-x"}),
      Plot.lineY(net, {x: "hour", y: "value", fx: "day", stroke: "var(--theme-foreground)", strokeWidth: 2, strokeDasharray: "2 4", curve: "monotone-x"}),
      Plot.ruleX(output, Plot.pointerX({x: "hour", fx: "day", stroke: "var(--theme-foreground-faint)"})),
      Plot.tip(output, Plot.pointerX({x: "hour", y: "value", fx: "day", channels: {technology: "generator"}, format: {y: ",.1f", fill: false, fx: false}})),
    ],
  }))}
</div>

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Price of one more MW of load — ${year}</h2>
    ${resize((width) => Plot.plot({
      width, height: 280, marginLeft: 60, marginRight: 20,
      x: {label: "hour", ticks: 6},
      y: {grid: true, label: "per MW", tickFormat: "s", zero: true},
      fx: {label: null, domain: days},
      marks: [
        Plot.lineY(marginal, {x: "hour", y: "value", fx: "day", stroke: "var(--theme-foreground)", strokeWidth: 2, curve: "step"}),
        Plot.ruleX(marginal, Plot.pointerX({x: "hour", fx: "day", stroke: "var(--theme-foreground-faint)"})),
        Plot.tip(marginal, Plot.pointerX({x: "hour", y: "value", fx: "day", format: {y: ",.0f", fx: false}})),
      ],
    }))}
  </div>
  <div class="card">
    <h2>Price by hour and period — ${run}</h2>
    <p class="muted">Every period at once: how the price structure moves as the fleet changes.</p>
    ${resize((width) => Plot.plot({
      width, height: 280, marginLeft: 50, marginRight: 20,
      x: {label: "hour", ticks: d3.range(0, 24, 6)},
      y: {label: "period", tickFormat: "d", reverse: true},
      fx: {label: null, domain: days},
      color: {type: "linear", range: sequential, interpolate: "rgb", legend: true, label: "price per MW", tickFormat: "s"},
      marks: [
        Plot.cell(surface_, {x: "hour", y: "year", fx: "day", fill: "value", inset: 0.5, tip: {format: {y: "d", fill: ",.0f", fx: false}}}),
      ],
    }))}
  </div>
</div>

<div class="card">
  <h2>The rows behind the chart</h2>
  ${Inputs.table(output, {format: {hour: (d) => String(d), value: (d) => d.toFixed(2)}})}
</div>
