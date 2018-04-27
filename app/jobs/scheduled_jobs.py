from flask_rq2 import RQ
from twilio.rest import Client
import datetime
import logging

rq = RQ()

@rq.job
def savings_reminder():
    logging.error('in savings reminder')
    from ..models import User
    users = User.query.all()
    client = Client(current_app.config["TWILIO_ACCOUNT_SID"], current_app.config["TWILIO_AUTH_TOKEN"])
    for user in users:
        today = datetime.datetime.now()
        today = today.date()
        goal_balance = (today-user.savings_start_date)*user.goal_amount/(user.savings_end_date-user.savings_start_date)
        print(goal_balance, user.bank_balance)
        if user.bank_balance < goal_balance:
            try:
                client.api.account.messages.create(
                    to=user.mobile_phone,
                    from_=current_app.config["TWILIO_PHONE_NUMBER"],
                    body="This is a reminder that your current savings balance is " + str(user.bank_balance) + " and your goal balance for today is " + str(goal_balance) + ".")
                break
            except Exception:
                print('not working')
                logging.error('not working')
                pass
