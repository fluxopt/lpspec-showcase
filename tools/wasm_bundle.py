"""Put beside the browser notebook what Pyodide cannot fetch from PyPI: our wheels, and the pathway model.

    uv run python -m tools.wasm_bundle site/dist/session-app

lpspec and math-spec are git dependencies, so micropip cannot resolve them by
name; this builds each as a wheel from the pin in pyproject.toml and lists them
in ``wheels/manifest.json``, which the notebook's bootstrap cell reads. The
pathway model is copied under ``models/`` because the notebook reads it by
path when it runs locally and fetches it by the same path in the browser.
"""

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]


def pins() -> list[str]:
    """The git-pinned requirements of the ``solve`` extra, and math-spec at the tag lpspec pins."""
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    lpspec = next(r for r in project['optional-dependencies']['solve'] if r.startswith('lpspec'))
    return [lpspec]


def main(out: Path) -> None:
    wheels = out / 'wheels'
    wheels.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '-q', '-w', str(wheels), *pins()], check=True)
    lpspec_wheel = next(wheels.glob('lpspec-*.whl'))
    math_spec = _requirement(lpspec_wheel, 'math-spec')
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '-q', '-w', str(wheels), math_spec], check=True)
    subprocess.run(['uv', 'build', '--wheel', '-q', '-o', str(wheels)], cwd=ROOT, check=True)
    order = ['math_spec', 'lpspec-', 'lpspec_showcase']
    names = sorted(
        (w.name for w in wheels.glob('*.whl')), key=lambda n: next(i for i, p in enumerate(order) if n.startswith(p))
    )
    (wheels / 'manifest.json').write_text(json.dumps(names, indent=1))
    (out / 'models').mkdir(exist_ok=True)
    shutil.copy(ROOT / 'models' / 'pathway.yaml', out / 'models' / 'pathway.yaml')
    print(f'{out}: {", ".join(names)}, models/pathway.yaml')


def _requirement(wheel: Path, name: str) -> str:
    """The requirement string a wheel declares for one dependency, git URL included."""
    import zipfile

    with zipfile.ZipFile(wheel) as zf:
        metadata = next(n for n in zf.namelist() if n.endswith('METADATA'))
        for line in zf.read(metadata).decode().splitlines():
            if line.startswith('Requires-Dist:') and line.split(':', 1)[1].strip().startswith(name):
                return line.split(':', 1)[1].strip()
    raise LookupError(f'{wheel.name} declares no dependency on {name}')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
