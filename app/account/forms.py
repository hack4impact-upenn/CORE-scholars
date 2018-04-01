from flask import url_for
from flask_wtf import Form
from wtforms import ValidationError
from wtforms.fields import (BooleanField, PasswordField, StringField, SelectField, IntegerField, SubmitField,
                            TextAreaField)
from wtforms.fields.html5 import EmailField, DateField, TelField, IntegerField
from wtforms.validators import Email, EqualTo, InputRequired, Length, Regexp, NumberRange
from ..utils import CustomSelectField
from ..models import User

import datetime


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


phone_validator = Regexp('(^$|((\+[0-9]{2})? ?\(?[0-9]{3}\)? ?-?.?[0-9]{3} ?-?.?[0-9]{4}))',
                         message="Not a valid phone number. Try the format 111-111-1111")

year_validator = Regexp('(^$|((\+[0-9]{2})? ?\(?[0-9]{3}\)? ?-?.?[0-9]{3} ?-?.?[0-9]{4}))',
                         message="Not a valid phone number. Try the format 111-111-1111")


class ApplicantProfileForm(Form):
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[InputRequired()])
    gender = CustomSelectField('Gender', validators=[InputRequired(), Length(1, 64)], choices=
        ['Male', 'Female', 'Trans', 'Non-binary', 'Bigender'], multiple=True)
    ethnicity = CustomSelectField('Ethnicity', validators=[InputRequired(), Length(1, 64)], choices=
        ['American Indian', 'Asian', 'Black', 'Hispanic or Latino', 'Multiracial','White', 'Decline to Identify'])
    mobile_phone = TelField('Mobile Phone', validators=[InputRequired(), phone_validator, Length(1, 64)])
    home_phone = TelField('Home Phone', validators=[phone_validator, Length(0, 64)])
    marital_status = CustomSelectField('Marital Status', validators=[InputRequired(), Length(1, 64)], choices=
        ['Single', 'Married', 'Divorced'])
    household_status = CustomSelectField('Household Status', validators=[InputRequired(), Length(1, 64)], choices=
        ['One-person', 'Non-family Household', 'Family Household', 'Married Couple'])
    citizenship_status = CustomSelectField('Citizenship Status', validators=[InputRequired(), Length(1, 64)], choices=
        ['US Citizen'])
    work_status = CustomSelectField('Work', validators=[InputRequired(), Length(1, 64)], choices=
        ['Student', 'Full-time Employed', 'Part-time Employed', 'Unemployed'])
    street = StringField('Street Address', validators=[InputRequired(), Length(1, 64)])
    city = StringField('City', validators=[InputRequired(), Length(1, 64)])
    state = StringField('State', validators=[InputRequired(), Length(1, 64)])
    zip = StringField('Zip', validators=[InputRequired(), Length(1, 64)])
    tanf = CustomSelectField('TANF', validators=[InputRequired(), Length(1, 64)], choices=['TANF', 'Not TANF'])
    etic = CustomSelectField('ETIC', validators=[InputRequired(), Length(1, 64)], choices=['ETIC', 'Declined'])
    number_of_children = IntegerField('Number of Children', validators=
        [InputRequired(), NumberRange(min=0, max=10)], default=0)

    submit = SubmitField('Submit')


current_year = datetime.datetime.now().year


class EducationProfileForm(Form):
    current_education = SelectField('Education Status', choices=[('high-school', 'Graduating High School Senior'),
        ('college', 'Current or Accepted College, Technical School or Vocational School Student')])

    high_school_name = StringField('High School Name', validators=[Length(1, 64)])
    college_name = StringField('College or School Name', validators=[Length(1, 64)])
    degree_program = StringField('Name of Degree Program', validators=[Length(1, 128)])
    graduation_year = IntegerField('Graduation Year', validators=
        [NumberRange(min=current_year, max=current_year+8)], default=current_year+4)
    submit = SubmitField('Submit')


class SavingsStartEndForm(Form):
    start_date = DateField(
        'Start Date', validators=[])
    end_date = DateField(
        'End Date', validators=[])
    submit = SubmitField('Save')