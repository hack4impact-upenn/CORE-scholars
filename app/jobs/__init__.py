from flask import Blueprint

jobs = Blueprint('jobs', __name__)

from scheduled_jobs import *
