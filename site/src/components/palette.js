// One categorical palette, validated for both surfaces, assigned by entity in a
// fixed order: a scenario or technology keeps its hue whatever else is on screen.
const STEPS = {
  light: {blue: "#2a78d6", orange: "#eb6834", aqua: "#1baf7a", yellow: "#eda100"},
  dark: {blue: "#3987e5", orange: "#d95926", aqua: "#199e70", yellow: "#c98500"},
};
const ORDER = ["blue", "orange", "aqua", "yellow"];

// Names this model uses. Anything else takes the next free hue, in ORDER.
const KNOWN = {
  base: "blue", carbon_cap: "orange", cheap_solar: "aqua", high_demand: "yellow",
  gas: "blue", solar: "yellow", wind: "aqua",
};

export function colorScale(names, dark) {
  const steps = STEPS[dark ? "dark" : "light"];
  const taken = new Set(names.map((n) => KNOWN[n]).filter(Boolean));
  const free = ORDER.filter((h) => !taken.has(h));
  const range = names.map((n) => steps[KNOWN[n] ?? free.shift() ?? ORDER[names.indexOf(n) % ORDER.length]]);
  return {domain: names, range, legend: true};
}

// The 2px surface ring and gap the marks carry, in the page's own surface colour.
export const surface = "var(--theme-background)";
