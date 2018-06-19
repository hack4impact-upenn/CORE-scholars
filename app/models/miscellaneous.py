from .. import db


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
    item_id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String)

