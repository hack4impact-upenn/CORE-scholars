from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from ..models import EditableHTML, Module

from . import main
from .. import db, csrf

import logging
import json
import os
import time
import boto3

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
                           modules={module.module_num:module.filename for module in current_user.modules},
                           num_modules=8)

@main.route('/modules-update', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def modules_update():
    module_data = json.loads(request.form['data'])
    already_exists = False
    for i in range(len(current_user.modules)):
        module_num = current_user.modules[i].module_num
        if module_data['module_num'] == module_num:
            module = current_user.modules[i]
            module.filename = module_data['filename']
            module.certificate_url = module_data['certificate_url']
            already_exists = True
            break
    if not already_exists:
        module = Module(user_id=current_user.id, module_num=module_data['module_num'], filename=module_data['filename'], certificate_url=module_data['certificate_url'])
    db.session.commit()
    flash('Your progress has been updated.', 'success')
    return jsonify({'status': 200})

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
