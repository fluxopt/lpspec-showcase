// Formatting shared by the pages: compact numbers for tiles, and one tile markup.
import {html} from "npm:htl";

const compact = new Intl.NumberFormat("en", {notation: "compact", maximumFractionDigits: 1});
const plain = new Intl.NumberFormat("en", {maximumFractionDigits: 0});

export const fmt = {
  compact: (d) => compact.format(d),
  plain: (d) => plain.format(d),
  percent: (d) => `${(d * 100).toFixed(0)}%`,
  signed: (d) => `${d >= 0 ? "+" : "−"}${compact.format(Math.abs(d))}`,
};

// A stat tile: a label, one number, and a line of context under it.
export function tile(label, value, note) {
  return html`<div class="card tile">
    <div class="tile-label">${label}</div>
    <div class="tile-value">${value}</div>
    <div class="tile-note">${note ?? ""}</div>
  </div>`;
}

// The diverging pair for a signed delta: blue for more, red for less.
export const diverging = {more: "#2a78d6", less: "#e34948"};

// The single-hue sequential ramp for a magnitude, light to dark.
export const sequential = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"];
