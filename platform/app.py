from datetime import timedelta
from functools import wraps
import csv
import io
import json
from pathlib import Path
import secrets
from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for, Response, send_file
from accounts import AccountError, SessionStore, SupabaseAccounts, allowed_parcels, read_env
from account_routes import account_blueprint
from flask_osbi import OSBI
from risk import risk_context, simulate_risk, RiskDataError, RiskInputError

BASE = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__)
    settings = read_env(BASE / '.env')
    instance = BASE / '.instance'
    instance.mkdir(exist_ok=True)
    key_file = instance / 'session-key'
    if not key_file.exists():
        try:
            with key_file.open('x', encoding='ascii') as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config.update(SECRET_KEY=settings.get('SECRET_KEY') or key_file.read_text(encoding='ascii'),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=settings.get('COOKIE_SECURE') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=16384)
    if test_config:
        app.config.update(test_config)
    # Presentation assets and Jinja components only.
    OSBI(app)
    accounts = app.config.get('ACCOUNT_BACKEND') or SupabaseAccounts(settings)
    sessions = SessionStore(app.config.get('AUTH_SESSION_DB', instance / 'auth-sessions.sqlite3'))
    app.extensions['accounts'] = accounts
    app.extensions['account_sessions'] = sessions

    def data():
        path = BASE / 'artifacts/dashboard.json'
        if not path.exists():
            abort(503, description='Faltan los resultados. Ejecuta python -m pipeline.train.')
        return json.loads(path.read_text(encoding='utf-8'))

    def authenticated(role=None):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                if not hasattr(g, 'account'):
                    g.account = sessions.resolve(session.get('auth_sid'), accounts)
                if not g.account:
                    session.clear()
                    if request.path.startswith('/api/'):
                        abort(401)
                    return redirect(url_for('login', role=role or 'productor'))
                session['role'] = g.account['role']
                if role and g.account['role'] != role:
                    abort(403)
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    @app.before_request
    def csrf_check():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = request.form.get('csrf_token', '')
            if not token or not secrets.compare_digest(token, session.get('csrf_token', '')):
                abort(400, description='La sesión del formulario expiró. Recarga la página.')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        if request.path.startswith(('/api/', '/productor', '/staff', '/export')):
            response.headers['Cache-Control'] = 'no-store'
        if request.path.startswith('/login'):
            response.headers['Cache-Control'] = 'no-store'
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.context_processor
    def token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return {'csrf_token': session['csrf_token']}

    @app.get('/')
    def landing():
        return render_template('landing.html')

    @app.get('/timeline')
    def timeline():
        return render_template('timeline.html')

    @app.route('/login/<role>', methods=['GET', 'POST'])
    def login(role):
        if role not in ('staff', 'productor'):
            abort(404)
        error = None
        status = 200
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            try:
                sessions.reserve_attempt(request.remote_addr or 'local', email)
                tokens = accounts.sign_in(email, request.form.get('password', ''))
                identity = accounts.get_user(tokens['access_token'])
                profile = accounts.profile(identity['id'], token=tokens['access_token'])
                if not profile or not profile['active'] or profile['role'] != role:
                    try:
                        accounts.sign_out(tokens['access_token'])
                    except AccountError:
                        pass
                    raise AccountError('Correo o contraseña incorrectos, o cuenta sin acceso a este espacio.', 401)
                sid = sessions.create(tokens, profile)
                sessions.pop(session.get('auth_sid'))
                session.clear()
                session.update(role=role, auth_sid=sid, csrf_token=secrets.token_urlsafe(32))
                session.permanent = True
                return redirect(url_for(role))
            except AccountError as exc:
                error, status = str(exc), exc.status
        return render_template('login.html', role=role, error=error), status

    @app.post('/logout')
    def logout():
        token = sessions.pop(session.get('auth_sid'))
        session.clear()
        if token:
            try:
                accounts.sign_out(token)
            except AccountError:
                pass  # Local invalidation already completed, even during an outage.
        return redirect(url_for('landing'))

    app.register_blueprint(account_blueprint(accounts, sessions, authenticated, data))

    @app.get('/productor')
    @authenticated('productor')
    def productor():
        return render_template('producer.html', page='productor')

    @app.get('/staff')
    @app.get('/staff/<section>')
    @authenticated('staff')
    def staff(section='resumen'):
        sections = {
            'resumen': 'Resumen de rendimiento',
            'predicciones': 'Predicciones por parcela',
            'validacion': 'Calidad de predicción',
            'factores': 'Factores del modelo',
            'metodologia': 'Metodología y límites',
            'riesgo': 'Riesgo económico',
        }
        if section not in sections:
            abort(404)
        return render_template('staff.html', page='staff', staff_section=section,
                               staff_title=sections[section])

    def filtered_parcels():
        rows = allowed_parcels(g.account, data()['parcels'])
        state = request.args.get('state', '')
        if state:
            if state not in {r['state'] for r in rows}:
                abort(400, description='Estado desconocido.')
            rows = [r for r in rows if r['state'] == state]
        search = request.args.get('search', '').strip().lower()
        if search:
            rows = [r for r in rows if search in (r['id'] + ' ' + r['municipality']).lower()]
        return rows

    @app.get('/api/parcels')
    @authenticated()
    def parcels():
        return jsonify(filtered_parcels())

    @app.get('/api/parcels/<parcel_id>')
    @authenticated()
    def parcel_detail(parcel_id):
        payload = data()
        parcel = next((row for row in allowed_parcels(g.account, payload['parcels']) if row['id'] == parcel_id), None)
        if parcel is None:
            abort(404)
        return jsonify(parcel=parcel, history=[r for r in payload['history'] if r['id'] == parcel_id], metadata=payload['metadata'])

    @app.get('/api/geometry')
    @authenticated()
    def geometry():
        payload = json.loads((BASE / 'artifacts/parcels.geojson').read_text(encoding='utf-8'))
        hidden = {r['id'] for r in allowed_parcels(g.account, data()['parcels'])}
        payload['features'] = [f for f in payload['features'] if f['properties']['ID_POLIGONO'] in hidden]
        return jsonify(payload)

    @app.get('/api/dashboard')
    @authenticated('staff')
    def dashboard():
        payload = data()
        # The snapshot contains only reviewed model outputs and held-out observations.
        return jsonify({k: payload[k] for k in ['metadata','parcels','metrics','importance','validation','spatial_validation']})

    @app.get('/api/risk/context')
    @authenticated('staff')
    def economic_risk_context():
        try:
            return jsonify(risk_context(data(), BASE / 'artifacts'))
        except RiskDataError as exc:
            abort(503, description=str(exc))

    @app.post('/api/risk/simulate')
    @authenticated('staff')
    def economic_risk_simulate():
        if any(len(request.form.getlist(key)) != 1 for key in request.form):
            abort(400, description='Cada campo del escenario debe tener un solo valor.')
        try:
            return jsonify(simulate_risk(request.form, data(), BASE / 'artifacts'))
        except RiskInputError as exc:
            abort(400, description=str(exc))
        except RiskDataError as exc:
            abort(503, description=str(exc))

    @app.get('/staff/riesgo/presupuesto.pdf')
    @authenticated('staff')
    def economic_risk_budget():
        path = BASE.parent / 'data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf'
        if not path.is_file():
            abort(503, description='No está disponible el presupuesto original de FIRA.')
        return send_file(path, mimetype='application/pdf', as_attachment=True)

    @app.get('/staff/riesgo/documentacion.md')
    @authenticated('staff')
    def economic_risk_documentation():
        path = BASE / 'docs/riesgo-economico.md'
        if not path.is_file():
            abort(503, description='No está disponible la documentación del módulo.')
        return send_file(path, mimetype='text/markdown', as_attachment=True)

    @app.get('/export/predictions.csv')
    @authenticated('staff')
    def export():
        rows = filtered_parcels()
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(['ID_parcela','Rendimiento_predicho_t_ha'])
        writer.writerows((r['id'], f'{r["yield"]:.4f}') for r in rows)
        return Response(buffer.getvalue(), content_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename=predicciones_59.csv'})

    @app.get('/health')
    def health():
        return jsonify(status='ok' if (BASE / 'artifacts/dashboard.json').exists() else 'not_ready'), 200 if (BASE / 'artifacts/dashboard.json').exists() else 503

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(429)
    @app.errorhandler(503)
    def error_page(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return render_template('error.html', error=error), error.code

    @app.errorhandler(AccountError)
    def account_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=str(error)), error.status
        return render_template('error.html', error={'description': str(error), 'code': error.status}), error.status

    return app


app = create_app()
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=int(read_env(BASE / '.env').get('PORT', '5000')))
