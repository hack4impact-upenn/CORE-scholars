from flask import url_for
from flask_wtf import Form
from wtforms import ValidationError
from wtforms.fields import (BooleanField, PasswordField, StringField, SubmitField,
                            RadioField, IntegerField, FormField, SelectField)
from wtforms.fields.html5 import EmailField, DateField, TelField
from wtforms.validators import Email, EqualTo, InputRequired, Length, Regexp
from wtforms.widgets import Input

from ..models import User


class LoginForm(Form):
    email = EmailField(
        'Email', validators=[InputRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')


class RegistrationForm(Form):
    first_name = StringField(
        'First name', validators=[InputRequired(), Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(), Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(), Length(1, 64), Email()])
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(), EqualTo('password2', 'Passwords must match')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered. (Did you mean to '
                                  '<a href="{}">log in</a> instead?)'
                                  .format(url_for('account.login')))


class RequestResetPasswordForm(Form):
    email = EmailField(
        'Email', validators=[InputRequired(), Length(1, 64), Email()])
    submit = SubmitField('Reset password')

    # We don't validate the email address so we don't confirm to attackers
    # that an account with the given email exists.


class ResetPasswordForm(Form):
    email = EmailField(
        'Email', validators=[InputRequired(), Length(1, 64), Email()])
    new_password = PasswordField(
        'New password',
        validators=[
            InputRequired(), EqualTo('new_password2', 'Passwords must match.')
        ])
    new_password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Reset password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class CreatePasswordForm(Form):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(), EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Set password')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[InputRequired()])
    new_password = PasswordField(
        'New password',
        validators=[
            InputRequired(), EqualTo('new_password2', 'Passwords must match.')
        ])
    new_password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Update password')


class ChangeEmailForm(Form):
    email = EmailField(
        'New email', validators=[InputRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeLocationForm(Form):
    location = StringField('location', validators=[InputRequired(), Length(1, 64)])
    submit = SubmitField('Change Location')


phone_validator = Regexp('(^$|((\+[0-9]{2})? ?\(?[0-9]{3}\)? ?-?.?[0-9]{3} ?-?.?[0-9]{4}))',
                         message="Not a valid phone number. Try the format 111-111-1111")


class ApplicantInfoForm(Form):
    first_name = StringField('First Name', validators=[InputRequired(), Length(1, 64)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(1, 64)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[InputRequired()])
    gender = StringField('Gender', validators=[InputRequired()])
    ethnicity = StringField('Ethnicity', validators=[InputRequired()])
    mobile_phone = TelField('Mobile Phone', validators=[InputRequired(), phone_validator])
    home_phone = TelField('Home Phone', validators=[phone_validator])
    marital_status = StringField('Marital Status', validators=[InputRequired()])
    household_status = StringField('Household Status', validators=[InputRequired()])
    citizenship_status = StringField('Citizenship Status', validators=[InputRequired()])
    work_status = StringField('Work', validators=[InputRequired()])
    street = StringField('Street Address', validators=[InputRequired(), Length(1, 64)])
    city = StringField('City', validators=[InputRequired(), Length(1, 64)])
    state = StringField('State', validators=[InputRequired(), Length(1, 64)])
    zip = StringField('Zip', validators=[InputRequired(), Length(1, 64)])
    tanf = StringField('TANF', validators=[InputRequired()])
    etic = StringField('ETIC', validators=[InputRequired()])

    submit = SubmitField('Submit')