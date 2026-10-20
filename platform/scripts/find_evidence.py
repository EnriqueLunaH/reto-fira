import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'work/sources'
patterns = {
    '02': ['cloud', 'barley', 'yield'],
    'last': ['cloud', 'barley', 'yield'],
    'An Introduction': ['test MSE', 'cross-validation', 'validation set approach'],
    'The Elements': ['Model Assessment', 'training error', 'cross-validation'],
    'Geographic': ['spatial autocorrelation', 'coordinate reference', 'spatial cross'],
    'Interpretable': ['correlated features', 'permutation feature importance', 'prediction interval'],
    'Introduction to Data Mining': ['missing values', 'Data Quality', 'overfitting'],
    'Python_Datascience': ['Pipeline', 'cross-validation', 'missing data'],
    'Python-for-Data': ['missing data', 'fillna', 'dropna'],
    'Ecuaciones': ['NDVI', 'DSWI', 'VI6T'],
}
for path in root.glob('*.json'):
    key = next(k for k in patterns if path.stem.startswith(k))
    pages = json.loads(path.read_text(encoding='utf-8'))
    print('\nFILE', path.stem, 'PAGE1', pages[0]['text'][:1300])
    for term in patterns[key]:
        found = []
        for page in pages:
            text = re.sub(r'\s+', ' ', page['text'])
            match = re.search(re.escape(term), text, re.I)
            if match and len(text) > 700:
                found.append((page['pdf_page'], text[max(0,match.start()-180):match.end()+550]))
        print(term, found[:4])
