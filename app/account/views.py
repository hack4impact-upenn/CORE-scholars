from flask import flash, redirect, render_template, request, url_for, jsonify
from flask_login import (current_user, login_required, login_user,
                         logout_user)
from flask_rq import get_queue

from . import account
from .. import db, csrf
from ..email import send_email
from ..models import User, Module
from .forms import (ChangeEmailForm, ChangePasswordForm, CreatePasswordForm,
                    LoginForm, RegistrationForm, RequestResetPasswordForm,
                    ResetPasswordForm, ApplicantInfoForm, SavingsStartEndForm)
from wtforms.fields.core import Label
import logging
from datetime import datetime, timedelta
import json


@account.route('/')
def index():
    return render_template('account/index.html')


@account.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.password_hash is not None and \
                user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('You are now logged in. Welcome back!', 'success')
            return redirect(request.args.get('next') or url_for('main.index'))
        else:
            flash('Invalid email or password.', 'form-error')
    return render_template('account/login.html', form=form)


@account.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user, and send them a confirmation email."""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        confirm_link = url_for('account.confirm', token=token, _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='Confirm Your Account',
            template='account/email/confirm',
            user=user,
            confirm_link=confirm_link)
        flash('A confirmation link has been sent to {}.'.format(user.email),
              'warning')
        return redirect(url_for('main.index'))
    return render_template('account/register.html', form=form)


@account.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@account.route('/manage', methods=['GET', 'POST'])
@account.route('/manage/info', methods=['GET', 'POST'])
@login_required
def manage():
    """Display a user's account information."""
    return render_template('account/manage.html', user=current_user, form=None)


@account.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Respond to existing user's request to reset their password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            reset_link = url_for(
                'account.reset_password', token=token, _external=True)
            get_queue().enqueue(
                send_email,
                recipient=user.email,
                subject='Reset Your Password',
                template='account/email/reset_password',
                user=user,
                reset_link=reset_link,
                next=request.args.get('next'))
        flash('A password reset link has been sent to {}.'
              .format(form.email.data), 'warning')
        return redirect(url_for('account.login'))
    return render_template('account/reset_password.html', form=form)


@account.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset an existing user's password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Invalid email address.', 'form-error')
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.new_password.data):
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('account.login'))
        else:
            flash('The password reset link is invalid or has expired.',
                  'form-error')
            return redirect(url_for('main.index'))
    return render_template('account/reset_password.html', form=form)


@account.route('/manage/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change an existing user's password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('main.index'))
        else:
            flash('Original password is invalid.', 'form-error')
    return render_template('account/manage.html', form=form)


@account.route('/manage/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    """Respond to existing user's request to change their email."""
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            change_email_link = url_for(
                'account.change_email', token=token, _external=True)
            get_queue().enqueue(
                send_email,
                recipient=new_email,
                subject='Confirm Your New Email',
                template='account/email/change_email',
                # current_user is a LocalProxy, we want the underlying user
                # object
                user=current_user._get_current_object(),
                change_email_link=change_email_link)
            flash('A confirmation link has been sent to {}.'.format(new_email),
                  'warning')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'form-error')
    return render_template('account/manage.html', form=form)


@account.route('/manage/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    """Change existing user's email with provided token."""
    if current_user.change_email(token):
        flash('Your email address has been updated.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))


@account.route('/confirm-account')
@login_required
def confirm_request():
    """Respond to new user's request to confirm their account."""
    token = current_user.generate_confirmation_token()
    confirm_link = url_for('account.confirm', token=token, _external=True)
    get_queue().enqueue(
        send_email,
        recipient=current_user.email,
        subject='Confirm Your Account',
        template='account/email/confirm',
        # current_user is a LocalProxy, we want the underlying user object
        user=current_user._get_current_object(),
        confirm_link=confirm_link)
    flash('A new confirmation link has been sent to {}.'.format(
        current_user.email), 'warning')
    return redirect(url_for('main.index'))


@account.route('/confirm-account/<token>')
@login_required
def confirm(token):
    """Confirm new user's account with provided token."""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm_account(token):
        flash('Your account has been confirmed.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))


@account.route(
    '/join-from-invite/<int:user_id>/<token>', methods=['GET', 'POST'])
def join_from_invite(user_id, token):
    """
    Confirm new user's account with provided token and prompt them to set
    a password.
    """
    if current_user is not None and current_user.is_authenticated:
        flash('You are already logged in.', 'error')
        return redirect(url_for('main.index'))

    new_user = User.query.get(user_id)
    if new_user is None:
        return redirect(404)

    if new_user.password_hash is not None:
        flash('You have already joined.', 'error')
        return redirect(url_for('main.index'))

    if new_user.confirm_account(token):
        form = CreatePasswordForm()
        if form.validate_on_submit():
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()
            flash('Your password has been set. After you log in, you can '
                  'go to the "Your Account" page to review your account '
                  'information and settings.', 'success')
            return redirect(url_for('account.login'))
        return render_template('account/join_invite.html', form=form)
    else:
        flash('The confirmation link is invalid or has expired. Another '
              'invite email with a new link has been sent to you.', 'error')
        token = new_user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user_id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=new_user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=new_user,
            invite_link=invite_link)
    return redirect(url_for('main.index'))


@account.before_app_request
def before_request():
    """Force user to confirm email before accessing login-required routes."""
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:8] != 'account.' \
            and request.endpoint != 'static':
        return redirect(url_for('account.unconfirmed'))


@account.route('/unconfirmed')
def unconfirmed():
    """Catch users with unconfirmed emails."""
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('account/unconfirmed.html')


@account.route('/manage/applicant-information', methods=['GET', 'POST'])
def applicant_info():
    form = ApplicantInfoForm()
    if form.validate_on_submit():
        flash('Thank you!', 'success')
        current_user.dob = form.dob.data
        current_user.gender = form.gender.data
        current_user.ethnicity = form.ethnicity.data
        current_user.mobile_phone = form.mobile_phone.data
        current_user.home_phone = form.home_phone.data
        current_user.marital_status = form.marital_status.data
        current_user.household_status = form.household_status.data
        current_user.citizenship_status = form.citizenship_status.data
        current_user.work_status = form.work_status.data
        current_user.street = form.street.data
        current_user.city = form.city.data
        current_user.state = form.state.data
        current_user.zip = form.zip.data
        current_user.tanf = form.tanf.data
        current_user.etic = form.etic.data
        current_user.number_of_children = form.number_of_children.data
        current_user.completed_forms = True

        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('account.index'))
    else:
        logging.error(str(form.errors))

    return render_template('account/user-info.html', form=form)


@account.route('/manage/applicant-information-edit', methods=['GET', 'POST'])
def applicant_info_edit():
    form = ApplicantInfoForm()
    current_user.id
    if current_user.completed_forms:
        form.dob.data =  datetime.strptime(current_user.dob, '%Y-%m-%d')
        form.gender.data = current_user.gender
        form.ethnicity.data = current_user.ethnicity
        form.mobile_phone.data = current_user.mobile_phone
        form.home_phone.data = current_user.home_phone
        form.marital_status.data = current_user.marital_status
        form.household_status.data = current_user.household_status
        form.citizenship_status.data = current_user.citizenship_status
        form.work_status.data = current_user.work_status
        form.street.data = current_user.street
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.zip.data = current_user.zip
        form.tanf.data = current_user.tanf
        form.etic.data = current_user.etic
        form.number_of_children.data = current_user.number_of_children
        form.submit.label = Label('submit', 'Save Information')

    if form.validate_on_submit():
        flash('Thank you!', 'success')
        current_user.dob = form.dob.data
        current_user.gender = form.gender.data
        current_user.ethnicity = form.ethnicity.data
        current_user.mobile_phone = form.mobile_phone.data
        current_user.home_phone = form.home_phone.data
        current_user.marital_status = form.marital_status.data
        current_user.household_status = form.household_status.data
        current_user.citizenship_status = form.citizenship_status.data
        current_user.work_status = form.work_status.data
        current_user.street = form.street.data
        current_user.city = form.city.data
        current_user.state = form.state.data
        current_user.zip = form.zip.data
        current_user.tanf = form.tanf.data
        current_user.etic = form.etic.data
        current_user.number_of_children = form.number_of_children.data

        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('account.index'))
    else:
        logging.error(str(form.errors))

    return render_template('account/user-info.html', form=form)


@account.route('/modules')
@login_required
def modules():
    logging.error(str(current_user.modules))
    return render_template('main/modules.html',
                           modules={module.module_num:module for module in current_user.modules},
                           num_modules=8)


@account.route('/modules-update', methods=['GET', 'POST'])
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
        module = Module(user_id=current_user.id, module_num=module_data['module_num'],
                        filename=module_data['filename'], certificate_url=module_data['certificate_url'])
        current_user.modules.append(module)
    db.session.commit()
    flash('Your progress has been updated.', 'success')
    return jsonify({'status': 200})


@account.route('/savings', methods=['GET', 'POST'])
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