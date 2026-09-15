// The site is a reader of the archive directory, like a DuckDB shell would be:
// its one data loader shapes ../runs into a zip, and the pages query that in
// the browser. The loader runs under the repository's own Python environment.
export default {
  title: "lpspec showcase",
  root: "src",
  theme: "dashboard",
  toc: false,
  pages: [
    {name: "Model", path: "/model"},
    {name: "Dispatch", path: "/dispatch"},
    {name: "Explore", path: "/explore"},
    {name: "Provenance", path: "/provenance"},
    {name: "Session", path: "/session"},
  ],
  interpreters: {
    ".py": ["uv", "run", "--project", "..", "python"],
  },
  footer: `Built with <a href="https://observablehq.com/framework/">Observable Framework</a> on the archive that <a href="https://github.com/fluxopt/lpspec">lpspec</a> wrote. <a href="https://github.com/fluxopt/lpspec-showcase">Source</a>.`,
};
