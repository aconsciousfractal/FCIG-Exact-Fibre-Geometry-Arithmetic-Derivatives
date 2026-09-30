"""Build the standalone paper with an existing pdflatex; never install packages."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT/'paper'
JOB = 'Exact-Fibre-Geometry-Arithmetic-Derivatives'
BUILD = PAPER/'build'

def main():
    engine = os.environ.get('PDFLATEX') or shutil.which('pdflatex')
    if not engine:
        print('Existing pdflatex required; set PDFLATEX or add it to PATH.', file=sys.stderr)
        return 2
    print('BUILD_DIRECTORY '+str(BUILD.resolve()))
    BUILD.mkdir(exist_ok=True)
    # Only the explicitly named job's generated auxiliaries; no recursive cleanup.
    for suffix in ('.aux', '.log', '.out', '.toc', '.pdf'):
        (BUILD/(JOB+suffix)).unlink(missing_ok=True)
    version = subprocess.run([engine, '--version'], capture_output=True, text=True)
    flags = ['-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-no-shell-escape']
    if 'MiKTeX' in version.stdout + version.stderr:
        flags.insert(0, '--disable-installer')
    for _ in range(3):
        run = subprocess.run([engine, *flags, '-output-directory='+str(BUILD), JOB+'.tex'], cwd=PAPER)
        if run.returncode:
            return run.returncode
    output = BUILD/(JOB+'.pdf')
    if not output.is_file():
        raise RuntimeError('pdflatex did not produce its expected PDF')
    shutil.copyfile(output, PAPER/(JOB+'.pdf'))
    print('PDF_BUILD_PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
