// Perspective as one self-contained module, bundled here rather than by the
// site's own bundler.
//
// The plugin packages import the viewer's TypeScript sources by their compiled
// `.js` names, which is TypeScript's convention and not Node's: `require.resolve`
// refuses `src/ts/extensions.js` where only `extensions.ts` exists, and that is
// the resolver the site's bundler uses. esbuild applies the TypeScript rule, so
// it is the one that can read these packages.
//
// The `inline` builds carry Perspective's WebAssembly inside the module, which
// is why this file is large. The alternative is registering the engine binary
// as a separate fetch, which needs a second loader to publish the `.wasm`.
import {build} from "esbuild";

const entry = `
export {default as perspective} from "@perspective-dev/client/inline";
import "@perspective-dev/viewer/inline";
import "@perspective-dev/viewer-datagrid";
import "@perspective-dev/viewer-charts";
`;

const result = await build({
  stdin: {contents: entry, resolveDir: new URL('.', import.meta.url).pathname, loader: 'js'},
  bundle: true,
  format: 'esm',
  write: false,
  logLevel: 'silent',
});

process.stdout.write(result.outputFiles[0].text);
