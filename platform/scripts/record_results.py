"""Refresh only the measured production-results block; preserve the audit/citations.

Never record browser, Docker or test outcomes that this script has not measured.
"""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
START = '<!-- RESULTS_START -->'
END = '<!-- RESULTS_END -->'


def run():
    report = json.loads((BASE / 'artifacts/metrics.json').read_text(encoding='utf-8'))
    path = BASE / 'technical-documentation.md'
    text = path.read_text(encoding='utf-8')
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('Expected exactly one results block; documentation was not modified.')
    before, remainder = text.split(START)
    _, after = remainder.split(END)
    rows = [
        '| Evaluación actual | n | MAE (t/ha) | RMSE (t/ha) | R² |',
        '|---|---:|---:|---:|---:|',
    ]
    for label, result in [
        ('CV anidada aleatoria por parcela', report['parcel_cv']['model']),
        ('Referencia mediana global, mismos folds', report['parcel_cv']['baseline']),
        ('CV anidada por bloques de 20 km', report['spatial_cv']['model']),
        ('Referencia mediana global, bloques', report['spatial_cv']['baseline']),
        ('Calibración del ajuste final, muestra distinta', report['calibration_point_metrics']),
    ]:
        rows.append(f"| {label} | {result['n']} | {result['mae']:.6f} | {result['rmse']:.6f} | {result['r2']:.6f} |")
    rows += ['', f"El mínimo interno del ganador final es MAE **{report['selection']['mae']:.6f}** "
             f"sobre {report['n_fit']} casos internos; no sustituye la estimación externa. "
             f"La métrica de las {report['n_calibration']} parcelas de calibración tampoco reemplaza la OOF "
             f"de {report['n_training']}. El radio de intervalo final es "
             f"**{report['interval']['radius_t_ha']:.6f} t/ha**."]
    path.write_text(before + START + '\n' + '\n'.join(rows) + '\n' + END + after, encoding='utf-8')


if __name__ == '__main__':
    run()
