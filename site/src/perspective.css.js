// Perspective's own stylesheet, read out of the installed package rather than
// copied into the tree: it carries the labels its settings panel prints, so a
// copy here would drift from the version that renders them.
//
// Neither theme file scopes itself to a colour scheme, so loading both flat
// leaves the last one winning. They are scoped here the way the site's own
// theme is scoped.
import {readFileSync} from "node:fs";
import {createRequire} from "node:module";

const require = createRequire(import.meta.url);
const theme = (name) => readFileSync(require.resolve(`@perspective-dev/viewer/themes/${name}.css`), "utf8");

process.stdout.write(`@media (prefers-color-scheme: light) {\n${theme('pro')}\n}\n`);
process.stdout.write(`@media (prefers-color-scheme: dark) {\n${theme('pro-dark')}\n}\n`);
