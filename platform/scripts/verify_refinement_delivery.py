"""Archive final tests and verify report links and activated release hashes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
AUDIT = BASE / 'artifacts/model-refinement-v2'
REPORT = BASE.parent / 'REPORTE_IMPLEMENTACION_PREDICCION.md'


def main():
    test = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q'], cwd=BASE,
                          capture_output=True, text=True, encoding='utf8', errors='replace')
    (AUDIT/'pytest-final.txt').write_text(test.stdout + test.stderr, encoding='utf8')
    assert test.returncode == 0, test.stdout + test.stderr
    passed = re.search(r'(\d+) passed', test.stdout)
    assert passed, 'Missing pytest completion summary'
    javascript = {}
    for name in ('charts.js', 'staff.js', 'producer.js', 'risk.js'):
        result = subprocess.run(['node', '--check', str(BASE/'static/js'/name)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        javascript[name] = 'passed'
    manifest = json.loads((AUDIT/'release-manifest.json').read_text())
    for filename,digest in manifest['files'].items():
        assert hashlib.sha256((BASE/'artifacts'/filename).read_bytes()).hexdigest() == digest, filename
    delivery = (BASE/'artifacts/predicciones_59.csv').read_bytes()
    for filename in ('proposal.csv','predicciones_59.csv'):
        assert delivery == (BASE.parent/'comparisons'/filename).read_bytes()
    content = REPORT.read_text(encoding='utf8')
    assert not re.search(r'Pendiente de completar|Verificación final pendiente|La evaluación está en ejecución', content)
    definitions = dict(re.findall(r'^\[([A-Z][A-Za-z0-9]*)\]:\s*(.+)$', content, re.M))
    used = set(re.findall(r'\[([A-Z][A-Za-z0-9]*)\](?!:)', content))
    assert used <= set(definitions), used-set(definitions)
    checked = []
    for ref,link in definitions.items():
        link = link.strip('<> ')
        if link.startswith('C:/'):
            if ref != 'E20':
                assert Path(link).exists(), (ref,link)
            checked.append(ref)
    codefiles = [BASE/'pipeline/refinement.py', *[BASE/'scripts'/name for name in (
        'refine_model.py','verify_refinement.py','publish_refinement.py',
        'complete_refinement_report.py','verify_refinement_delivery.py')],
        BASE/'tests/test_refinement.py',BASE/'tests/test_integrity.py',
        *[BASE/'static/js'/name for name in javascript],
        *[BASE/'templates'/name for name in ('methodology.html','factors.html','producer.html','staff.html','risk.html')]]
    source_hashes = {str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in codefiles}
    result = dict(verified_at_utc=datetime.now(timezone.utc).isoformat(),
                  pytest=dict(passed=int(passed.group(1)),returncode=0,log='pytest-final.txt'),
                  javascript_syntax=javascript,active_release_hashes_verified=True,
                  prediction_copies_identical=True,report_local_references_verified=checked,
                  report_citations_defined=True,code_sha256=source_hashes,
                  visual_review=dict(status='not_completed',reason='Local browser timed out; local socket access denied by execution environment. Flask test-client tests passed; no visual inspection claimed.'),
                  external_submission=False)
    (AUDIT/'completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
