from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from ..models import EditableHTML, Module

from . import main
from .forms import SavingsStartEndForm
from .. import db, csrf

import logging
import json
import os
import time
import boto3

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
    logging.error(str(current_user.modules))
    return render_template('main/modules.html',
                           modules={module.module_num:module for module in current_user.modules},
                           num_modules=8)

@main.route('/modules-update', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def modules_update():
    module_data = json.loads(request.form['data'])
    logging.error('here')
    logging.error(str(module_data))
    already_exists = False
    for i in range(len(current_user.modules)):
        module_num = current_user.modules[i].module_num
        if module_data['module_num'] == module_num:
            module = current_user.modules[i]
            module.filename = module_data['filename']
            module.certificate_url = module_data['certificate_url']
            logging.error(module.certificate_url)
            already_exists = True
            break
    if not already_exists:
        module = Module(user_id=current_user.id, module_num=module_data['module_num'], filename=module_data['filename'], certificate_url=module_data['certificate_url'])
        current_user.modules.append(module)
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

@main.route('/sign-s3/')
def sign_s3():
    # Load necessary information into the application
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_REGION = os.environ.get('S3_REGION')
    TARGET_FOLDER = 'json/'
    # Load required data from the request
    pre_file_name = request.args.get('file-name') 
    file_name = ''.join(pre_file_name.split('.')[:-1]) + str(time.time()).replace('.','-') + '.' + ''.join(pre_file_name.split('.')[-1:])
    file_type = request.args.get('file-type')

  # Initialise the S3 client
    s3 = boto3.client('s3', 'us-west-2')

    # Generate and return the presigned URL
    presigned_post = s3.generate_presigned_post(
            Bucket = S3_BUCKET,
            Key = TARGET_FOLDER + file_name,
            Fields = {"acl": "public-read", "Content-Type": file_type},
            Conditions = [
                {"acl": "public-read"},
                {"Content-Type": file_type}
                ],
            ExpiresIn = 6000
            )

    # Return the data to the client
    return json.dumps({
        'data': presigned_post,
        'url_upload': 'https://%s.%s.amazonaws.com' % (S3_BUCKET, S3_REGION),
        'url': 'https://%s.amazonaws.com/%s/json/%s' % (S3_REGION, S3_BUCKET, file_name)
        })
