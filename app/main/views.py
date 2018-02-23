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
