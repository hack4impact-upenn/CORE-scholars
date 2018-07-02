from .. import db
from config import Config
import plaid


class EditableHTML(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    editor_name = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)

    @staticmethod
    def get_editable_html(editor_name):
        editable_html_obj = EditableHTML.query.filter_by(
            editor_name=editor_name).first()

        if editable_html_obj is None:
            editable_html_obj = EditableHTML(editor_name=editor_name, value='')
        return editable_html_obj


class PhoneNumberState(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String)
    verification_code = db.Column(db.Integer)


class SiteAttributes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    airtable_html = db.Column(db.Text)

    @staticmethod
    def create_entry():
        entry = SiteAttributes(airtable_html=str())
        db.session.add(entry)
        db.session.commit()


class PlaidBankAccount(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    name = db.Column(db.String, default="Unnamed")
    access_token = db.Column(db.String)
    items = db.relationship('PlaidBankItem', backref='admin_bank', lazy='dynamic')

    def update_items(self):
        db_items = {item.item_id:item for item in self.items}
        request_items = self.get_plaid_client().Auth.get(self.access_token)
        request_item_ids = set()
        for item in request_items['accounts']:
            item_id = item['account_id']
            request_item_ids.add(item_id)
            balance = item['balances']['available'] if item['balances']['available'] else item['balances']['current']
            if item_id in db_items:
                db_items[item_id].balance = balance
                db.session.add(db_items[item_id])
            else:
                new_item = PlaidBankItem(item_id=item_id, official_name=item['official_name'],
                                         subtype=item['subtype'], mask=item['mask'], balance=balance)
                db.session.add(new_item)
                self.items.append(new_item)
        closed_items = [item for item_id, item in db_items.items() if item_id not in request_item_ids]
        for closed_item in closed_items:
            closed_item.is_open = False
            db.session.add(closed_item)
        db.session.commit()

    @staticmethod
    def update_all_items():
        for bank in PlaidBankAccount.query.all():
            bank.update_items()

    @staticmethod
    def get_plaid_client():
        return plaid.Client(client_id=Config.PLAID_CLIENT_ID, secret=Config.PLAID_SECRET,
                            public_key=Config.PLAID_PUBLIC_KEY, environment=Config.PLAID_ENV)


class PlaidBankItem(db.Model):
    __tablename__ = 'bank_items'
    id = db.Column(db.Integer, primary_key=True)
    is_open = db.Column(db.Boolean, default=True)
    item_id = db.Column(db.String)
    admin_bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'))
    official_name = db.Column(db.String)
    subtype = db.Column(db.String)
    mask = db.Column(db.String)
    balance = db.Column(db.Integer)

    def get_display_name(self):
        return f'{self.subtype.title()} {self.mask} - ${self.balance}'
