from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from ..models import EditableHTML

from . import main
from .. import db, csrf

import logging
import json

@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template('main/about.html',
                           editable_html_obj=editable_html_obj)

@main.route('/modules')
@login_required
def modules():
    return render_template('main/modules.html',
                           modules=current_user.modules)

@main.route('/modules-update', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def modules_update():
    module_data = json.loads(request.form['data'])
    new_module_string = ""
    for i in range(len(current_user.modules)):
        new_module_string += '1' if module_data[str(i+1)] else '0'
    current_user.modules = new_module_string
    db.session.commit()
    flash('Your progress has been updated.', 'success')
    return jsonify({'status': 200})
