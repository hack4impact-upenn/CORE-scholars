from flask import abort, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from flask_rq import get_queue
from .forms import (ChangeAccountTypeForm, ChangeUserEmailForm, InviteUserForm,
                    NewUserForm, AirtableSurveyHTML, AirtableGridHTML, LinkBankAccount)
from . import admin
from .. import db, csrf
from ..decorators import admin_required
from ..email import send_email
from ..models import Role, User, EditableHTML, SiteAttributes, PlaidBankAccount, PlaidBankItem
from config import Config


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            bank_acct_open=form.bank_acct_open.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link, )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'
              .format(user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Role for user {} successfully changed to {}.'
              .format(user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/link-bank-account', methods=['GET', 'POST'])
@login_required
@admin_required
def link_bank_account(user_id):
    """Link a users' bank account"""
    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = LinkBankAccount()
    PlaidBankAccount.update_all_items()
    items = PlaidBankItem.query.filter_by(is_open=True).all()
    form.bank_item.choices = [(item.item_id, item.get_display_name()) for item in items]
    if form.validate_on_submit():
        item_id = form.bank_item.data
        user.bank_item = PlaidBankItem.query.filter_by(item_id=item_id).first()
        db.session.add(user)
        db.session.commit()
        flash('Bank account for user {} successfully updated to {}.'
              .format(user.full_name(), user.bank_item.get_display_name()), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200


@admin.route('/airtable', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_airtable():
    site = SiteAttributes.query.all()[0]
    grid_form = AirtableGridHTML()
    survey_form = AirtableSurveyHTML()
    if site.form_html != '':
        survey_form.airtable_html.data = site.form_html
    if site.grid_html != '':
        grid_form.airtable_html.data = site.grid_html
    if survey_form.validate_on_submit():
        site.form_html = survey_form.airtable_html.raw_data[0]
        db.session.add(site)
        db.session.commit()
    if grid_form.validate_on_submit():
        site.grid_html = grid_form.airtable_html.raw_data[0]
        db.session.add(site)
        db.session.commit()
    return render_template('admin/manage_airtable.html', grid_form=grid_form, survey_form=survey_form,
                           grid_html=site.grid_html)


@admin.route('/link-bank', methods=['GET'])
@login_required
@admin_required
def link_admin_bank():
    PlaidBankAccount.update_all_items()
    bank_accounts = PlaidBankAccount.query.all()
    bank_items = [account.items for account in bank_accounts]
    return render_template('admin/link_bank.html', config=Config, bank_accounts=bank_accounts, bank_items=bank_items)


@admin.route('/bank/<int:bank_id>/delete-account', methods=['GET'])
@admin_required
def delete_admin_bank(bank_id):
    bank_account = PlaidBankAccount.query.filter_by(id=bank_id).first()
    bank_account_name = bank_account.name
    if bank_account is None:
        abort(404)
    for item in bank_account.items:
        db.session.delete(item)
    db.session.delete(bank_account)
    db.session.commit()
    flash('Deleted bank account, ' + bank_account_name)
    return redirect(url_for('admin.link_admin_bank'))


@admin_required
@admin.route('/bank/<int:bank_id>/update-account-name', methods=['GET'])
def change_admin_account_name(bank_id):
    bank_account = PlaidBankAccount.query.filter_by(id=bank_id).first()
    if bank_account is None:
        abort(404)
    bank_account.name = request.args.get('new-name')
    db.session.add(bank_account)
    db.session.commit()
    flash('Updated bank account name')
    return redirect(url_for('admin.link_admin_bank'))


@admin.route("/get-access-token", methods=['POST'])
@csrf.exempt
def get_access_token():
    public_token = request.form['public_token']
    exchange_response = PlaidBankAccount.get_plaid_client().Item.public_token.exchange(public_token)
    new_bank_account = PlaidBankAccount(
        item_id=exchange_response['item_id'],
        access_token=exchange_response['access_token'])
    db.session.add(new_bank_account)
    db.session.commit()
    return redirect(url_for('admin.link_admin_bank'))