from flask_wtf import Form
from wtforms import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import PasswordField, StringField, SubmitField, TextAreaField, SelectField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import Email, EqualTo, InputRequired, Length

from .. import db
from ..models import Role, User, PlaidBankAccount


class ChangeUserEmailForm(Form):
    email = EmailField(
        'New email', validators=[InputRequired(), Length(1, 64), Email()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeAccountTypeForm(Form):
    role = QuerySelectField(
        'New account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    submit = SubmitField('Update role')


class LinkBankAccount(Form):
    # account_owner = SelectField('Admin Account', validators=[InputRequired()])
    bank_item = SelectField('Bank Account')
    submit = SubmitField('Update Bank Account')


class InviteUserForm(Form):
    role = QuerySelectField(
        'Account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    first_name = StringField(
        'First name', validators=[InputRequired(), Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(), Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(), Length(1, 64), Email()])
    bank_acct_open = DateField(
        'Bank Account Open Date', format='%Y-%m-%d', validators=[InputRequired()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(), EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')


class AirtableFormHTML(Form):
    airtable_html = TextAreaField('Airtable Form', validators=[InputRequired()],
                                  description= 'Airtable allows you to create a customizable form and access the '
                                               'responses in the form of a beautiful and powerful spreadsheet. Please '
                                               'copy and paste the HTML for your embedded form below. This will be the '
                                               'form that all users must fill out before they can use the application '
                                               'for the first time.')
    submit = SubmitField('Submit')