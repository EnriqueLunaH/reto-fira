"""Staff-only account CRUD. Reads the parcel catalog without changing it."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from accounts import (AccountError, allowed_parcels, check_password, email_address,
                      municipality_key, profile_fields, user_id)


def account_blueprint(accounts, sessions, authenticated, data):
    bp = Blueprint('accounts', __name__, url_prefix='/staff/usuarios')

    def producer(uid):
        profile = accounts.profile(user_id(uid), admin=True)
        if not profile or profile['role'] != 'productor':
            abort(404)
        return profile

    def editor(profile=None, error=None, status=200):
        parcels = data()['parcels']
        places = {municipality_key(p): {'state': p['state'], 'municipality': p['municipality']} for p in parcels}
        selected_ids = set(request.form.getlist('parcel_ids') if request.method == 'POST'
                           else (profile or {}).get('parcel_ids', []))
        selected_places = set(request.form.getlist('municipalities') if request.method == 'POST'
                             else [municipality_key(m) for m in (profile or {}).get('municipalities', [])])
        return render_template('account_edit.html', page='usuarios', profile=profile,
                               parcels=parcels, places=sorted(places.items(), key=lambda item: (item[1]['state'], item[1]['municipality'])),
                               selected_ids=selected_ids, selected_places=selected_places, error=error), status

    @bp.get('')
    @authenticated('staff')
    def index():
        try:
            page = max(1, min(100000, int(request.args.get('pagina', '1'))))
        except ValueError:
            abort(400)
        profiles = accounts.list_profiles(offset=(page - 1) * 50, limit=51)
        has_next = len(profiles) > 50
        parcels = data()['parcels']
        rows = [{**p, 'parcel_count': len(allowed_parcels(p, parcels))} for p in profiles[:50]]
        return render_template('accounts.html', page='usuarios', profiles=rows, current_page=page, has_next=has_next)

    @bp.route('/nuevo', methods=['GET', 'POST'])
    @authenticated('staff')
    def create():
        if request.method == 'POST':
            try:
                fields = profile_fields(request.form, data()['parcels'])
                accounts.create(email_address(request.form.get('email', '')),
                                check_password(request.form.get('password', '')), fields)
            except AccountError as exc:
                return editor(error=str(exc), status=exc.status)
            flash('Productor creado. Ya puede ingresar con el correo y la contraseña definidos.', 'success')
            return redirect(url_for('accounts.index'), code=303)
        return editor()

    @bp.route('/<uid>/editar', methods=['GET', 'POST'])
    @authenticated('staff')
    def edit(uid):
        profile = producer(uid)
        if request.method == 'POST':
            try:
                fields = profile_fields(request.form, data()['parcels'])
                accounts.update_profile(profile['id'], fields)
                if not fields['active']:
                    sessions.revoke_user(profile['id'])
            except AccountError as exc:
                return editor(profile, str(exc), exc.status)
            flash('Datos y asignaciones actualizados.', 'success')
            return redirect(url_for('accounts.edit', uid=profile['id']), code=303)
        return editor(profile)

    @bp.post('/<uid>/acceso')
    @authenticated('staff')
    def credentials(uid):
        profile = producer(uid)
        try:
            email = email_address(request.form.get('email', ''))
            password = request.form.get('password', '')
            if password:
                check_password(password)
            accounts.update_credentials(profile['id'], email, password)
            sessions.revoke_user(profile['id'])
        except AccountError as exc:
            flash(str(exc), 'error')
            return redirect(url_for('accounts.edit', uid=profile['id']), code=303)
        flash('Credenciales actualizadas. Las sesiones anteriores han sido cerradas.', 'success')
        return redirect(url_for('accounts.edit', uid=profile['id']), code=303)

    @bp.post('/<uid>/eliminar')
    @authenticated('staff')
    def delete(uid):
        profile = producer(uid)
        if request.form.get('confirm_email', '').strip().lower() != profile['email'].lower():
            flash('Para eliminar, escribe el correo exacto del productor.', 'error')
            return redirect(url_for('accounts.edit', uid=profile['id']), code=303)
        try:
            accounts.delete(profile['id'])
            sessions.revoke_user(profile['id'])
        except AccountError as exc:
            flash(str(exc), 'error')
            return redirect(url_for('accounts.edit', uid=profile['id']), code=303)
        flash('Productor eliminado y sus sesiones cerradas.', 'success')
        return redirect(url_for('accounts.index'), code=303)

    return bp
