// A pivot table over one quantity, configured from the catalogue rather than
// from the model: the archive's own dimensions group the rows, the run splits
// the columns, and `value` is what is aggregated. Every quantity in the
// catalogue is therefore shown by the same code, whatever the model was.
//
// Perspective arrives as the module `perspective.js.js` bundles, because the
// site's own bundler cannot read its plugin packages; that file says why.

/** DuckDB hands an integer back as a BigInt, which is not a Perspective column type. */
const plain = (row) => Object.fromEntries(Object.entries(row).map(([k, v]) => [k, typeof v === "bigint" ? Number(v) : v]));

/**
 * A `<perspective-viewer>` over `rows`, opened on the quantity's own shape.
 *
 * One table per quantity, named and kept on the client, so returning to a
 * quantity already read does not send its rows again.
 */
export async function pivot(client, rows, {kind, name, dims}) {
  const table = `${kind}_${name}`;
  const held = await client.open_table(table).catch(() => null);
  if (!held) await client.table(rows.map(plain), {name: table});

  const viewer = document.createElement("perspective-viewer");
  await viewer.load(client);
  await viewer.restore({
    table,
    plugin: "Datagrid",
    group_by: dims,
    split_by: ["run"],
    columns: ["value"],
    aggregates: {value: "sum"},
    settings: true,
  });
  return viewer;
}
