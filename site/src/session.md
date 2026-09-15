---
title: Session
---

# A modelling session

The other pages are what lpspec produces unattended: a job solves, archives, and this site reads the archive. This page is the other half of the story, a [marimo](https://marimo.io) notebook in which the model is a document you edit by hand. Change the YAML and the typeset math, the validation and the solve follow. Change a number in the data table, or move a slider under the pathway, and the charts re-solve.

What you see below is the notebook as it ran at the last build, with its outputs and without a kernel, so the controls do not respond here. To run it live:

```bash
git clone https://github.com/fluxopt/lpspec-showcase && cd lpspec-showcase
uv sync --all-extras
uv run marimo edit notebooks/session.py
```

The notebook is [`notebooks/session.py`](https://github.com/fluxopt/lpspec-showcase/blob/main/notebooks/session.py), a plain Python file.

```js
const session = FileAttachment("session.html").href;
```

<p>${html`<a href="${session}" target="_blank">Open the executed notebook in its own tab ↗</a>`}</p>

${html`<iframe src="${session}" title="The modelling session, as it ran at the last build" style="width: 100%; height: 2400px; border: 1px solid var(--theme-foreground-faintest); border-radius: 8px; background: white;"></iframe>`}
