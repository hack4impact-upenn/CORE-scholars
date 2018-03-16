from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from ..models import EditableHTML

from . import main
from .forms import SavingsStartEndForm
from .. import db, csrf

import logging
import json

from datetime import datetime, timedelta

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

@main.route('/savings', methods=['GET', 'POST'])
@login_required
def savings():
    form = SavingsStartEndForm()
    if form.validate_on_submit():
        error_flag = False
        if form.start_date.data is not None and form.end_date.data is None:
            if form.start_date.data >= form.end_date.data:
                flash('The end date must be after the start date.', 'error')
                error_flag = True
        if not error_flag:
            current_user.savings_start_date = form.start_date.data
            current_user.savings_end_date = form.end_date.data
            flash('Your start and end dates have been saved.', 'success')
            db.session.commit()
    if current_user.savings_start_date is not None:
        form.start_date.data = current_user.savings_start_date
    if current_user.savings_end_date is not None:
        form.end_date.data = current_user.savings_end_date
    weeks = None
    if current_user.savings_start_date is not None and current_user.savings_end_date is not None:
        startd = current_user.savings_start_date
        endd = current_user.savings_end_date
        monday1 = (startd-timedelta(days=startd.weekday()))
        monday2 = (endd-timedelta(days=endd.weekday()))
        num_weeks = (monday2-monday1).days/7
        increment = current_user.goal_amount/float(num_weeks)
        weeks = []
        for i in range(num_weeks):
            weeks.append(round(increment*(i+1), 2))
    return render_template('main/savings.html', form=form, weeks=weeks)
