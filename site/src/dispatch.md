---
title: Dispatch
sql:
  p: ./data/runs/primal/p.parquet
  price: ./data/runs/dual/balance.parquet
  load: ./data/runs/source/load.parquet
---

# One day's dispatch

Output by technology over a typical day, the load it meets, and the price of one more MW of load in each hour, which is the dual of the balance constraint.

```js
import {colorScale, surface} from "./components/palette.js";
```

```sql id=runs
select distinct run from p order by run
```

```sql id=years
select distinct year::integer as year from p order by year
```

```sql id=days
select distinct day from p order by day
```

```js
const run = view(Inputs.select(runs.toArray().map((d) => d.run), {label: "Scenario"}));
const year = view(Inputs.select(years.toArray().map((d) => d.year), {label: "Period", format: String}));
const day = view(Inputs.select(days.toArray().map((d) => d.day), {label: "Typical day"}));
```

```sql id=output
select hour::integer as hour, generator, value from p where run = ${run} and year = ${year} and day = ${day} order by hour, generator
```

```sql id=met
select hour::integer as hour, value from load where run = ${run} and year = ${year} and day = ${day} order by hour
```

```sql id=marginal
select hour::integer as hour, value from price where run = ${run} and year = ${year} and day = ${day} order by hour
```

```js
const technologies = [...new Set(output.toArray().map((d) => d.generator))];

function dispatch(width) {
  const rows = output.toArray();
  const loadRows = met.toArray();
  return Plot.plot({
    width,
    height: 320,
    marginLeft: 50,
    x: {label: "hour", ticks: 12},
    y: {grid: true, label: "MW"},
    color: colorScale(technologies, dark),
    marks: [
      Plot.areaY(rows, {x: "hour", y: "value", fill: "generator", stroke: surface, strokeWidth: 2, curve: "monotone-x"}),
      Plot.lineY(loadRows, {x: "hour", y: "value", stroke: "var(--theme-foreground)", strokeWidth: 2, strokeDasharray: "4 3", curve: "monotone-x"}),
      Plot.text([loadRows.reduce((a, b) => (b.value > a.value ? b : a))], {x: "hour", y: "value", text: ["load"], dy: -10, fill: "var(--theme-foreground)"}),
      Plot.ruleX(rows, Plot.pointerX({x: "hour", stroke: "var(--theme-foreground-faint)"})),
      Plot.tip(rows, Plot.pointerX({x: "hour", y: "value", channels: {technology: "generator"}, format: {y: ",.1f", fill: false}})),
    ],
  });
}

function prices(width) {
  const rows = marginal.toArray();
  return Plot.plot({
    width,
    height: 320,
    marginLeft: 60,
    x: {label: "hour", ticks: 12},
    y: {grid: true, label: "per MW", tickFormat: "s", zero: true},
    marks: [
      Plot.lineY(rows, {x: "hour", y: "value", stroke: "var(--theme-foreground)", strokeWidth: 2, curve: "step"}),
      Plot.dot(rows, {x: "hour", y: "value", fill: "var(--theme-foreground)", r: 3, stroke: surface, strokeWidth: 2}),
      Plot.ruleX(rows, Plot.pointerX({x: "hour", stroke: "var(--theme-foreground-faint)"})),
      Plot.tip(rows, Plot.pointerX({x: "hour", y: "value", format: {y: ",.0f"}})),
    ],
  });
}
```

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Output by hour, MW — ${run}, ${year}, ${day}</h2>
    ${resize(dispatch)}
  </div>
  <div class="card">
    <h2>Price of one more MW of load</h2>
    ${resize(prices)}
  </div>
</div>

<div class="card">
  <h2>The rows behind the chart</h2>
  ${Inputs.table(output, {format: {hour: (d) => String(d), value: (d) => d.toFixed(2)}})}
</div>
