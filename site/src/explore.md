---
title: Explore
---

# Explore the archive

This page knows nothing about the model. It lists every quantity the archives hold, reads each one's dimensions off the parquet, and offers them as the axis, the colour and the filters. Point the solve job at a different lpspec model and this page shows it unchanged.

```js
import {colorScale, surface} from "./components/palette.js";

const archive = FileAttachment("data/runs.zip").zip();
```

```js
const catalogue = await archive.file("catalogue.json").json();
const entries = catalogue.map((d) => ({...d, label: `${d.kind}: ${d.name}`, table: `${d.kind}_${d.name}`}));
const db = await DuckDBClient.of(Object.fromEntries(entries.map((d) => [d.table, archive.file(`${d.kind}/${d.name}.parquet`)])));
```

```js
const picked = view(Inputs.select(entries, {label: "Quantity", format: (d) => d.label, value: entries.find((d) => d.kind === "primal") ?? entries[0]}));
```

```js
const table = await db.query(`select * from "${picked.table}"`);
const plain = (row) => Object.fromEntries(Object.entries(row).map(([k, v]) => [k, typeof v === "bigint" ? Number(v) : v]));
const rows = table.toArray().map(plain);
const dims = ["run", ...picked.dims];
const distinct = (dim) => [...new Set(rows.map((d) => d[dim]))].sort((a, b) => (a > b) - (a < b));
```

```js
const along = view(Inputs.select(picked.dims.length ? picked.dims : ["run"], {label: "Along"}));
```

```js
const colour = view(Inputs.select(dims.filter((d) => d !== along), {label: "Coloured by"}));
```

```js
const rest = dims.filter((d) => d !== along && d !== colour);
const filters = view(Inputs.form(Object.fromEntries(rest.map((dim) => [dim, Inputs.select(distinct(dim), {label: dim, format: String})]))));
```

```js
const shown = rows.filter((d) => rest.every((dim) => d[dim] === filters[dim]));
const series = distinct(colour);
const ordinal = typeof shown[0]?.[along] === "string";

function chart(width) {
  const scale = colorScale(series, dark);
  const identity = along === colour;
  return Plot.plot({
    width,
    height: 340,
    marginLeft: 70,
    x: {label: along, tickFormat: ordinal ? undefined : "d"},
    y: {grid: true, label: "value", tickFormat: "s", zero: true},
    color: scale,
    marks: ordinal
      ? [Plot.barY(shown, {x: along, y: "value", fill: colour, stroke: surface, strokeWidth: 2, tip: true})]
      : [
          Plot.lineY(shown, {x: along, y: "value", stroke: colour, strokeWidth: 2, sort: along}),
          Plot.dot(shown, {x: along, y: "value", fill: colour, r: 4, stroke: surface, strokeWidth: 2}),
          Plot.ruleX(shown, Plot.pointerX({x: along, stroke: "var(--theme-foreground-faint)"})),
          Plot.tip(shown, Plot.pointerX({x: along, y: "value", channels: {[colour]: colour}, format: {x: ordinal ? undefined : "d", fill: false}})),
        ],
  });
}
```

<div class="card">
  <h2>${picked.name} <span class="muted">(${picked.kind}), keyed by ${picked.dims.join(", ") || "nothing"}</span></h2>
  ${resize(chart)}
</div>

```js
const integers = Object.keys(shown[0] ?? {}).filter((k) => shown.every((d) => Number.isInteger(d[k])));
```

<div class="card">
  ${Inputs.table(shown, {format: Object.fromEntries(integers.map((k) => [k, String]))})}
</div>
