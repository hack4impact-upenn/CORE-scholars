from flask import render_template, request, redirect, url_for
from flask_login import current_user
from ..models import EditableHTML

from . import main


@main.route('/')
def index():
	if current_user.is_authenticated:
		return redirect(url_for('account.index'))
	else:
		return redirect(url_for('account.login'))
    


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template('main/about.html',
                           editable_html_obj=editable_html_obj)

