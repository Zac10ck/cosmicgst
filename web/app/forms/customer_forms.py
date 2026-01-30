"""Customer forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Regexp

# Indian state codes for GST
STATE_CODES = [
    ('32', '32 - Kerala'),
    ('33', '33 - Tamil Nadu'),
    ('29', '29 - Karnataka'),
    ('36', '36 - Telangana'),
    ('37', '37 - Andhra Pradesh'),
    ('27', '27 - Maharashtra'),
    ('06', '06 - Haryana'),
    ('07', '07 - Delhi'),
    ('09', '09 - Uttar Pradesh'),
    ('10', '10 - Bihar'),
    ('19', '19 - West Bengal'),
    ('21', '21 - Odisha'),
    ('08', '08 - Rajasthan'),
    ('24', '24 - Gujarat'),
    ('03', '03 - Punjab'),
    ('01', '01 - Jammu & Kashmir'),
    ('02', '02 - Himachal Pradesh'),
    ('04', '04 - Chandigarh'),
    ('05', '05 - Uttarakhand'),
    ('11', '11 - Sikkim'),
    ('12', '12 - Arunachal Pradesh'),
    ('13', '13 - Nagaland'),
    ('14', '14 - Manipur'),
    ('15', '15 - Mizoram'),
    ('16', '16 - Tripura'),
    ('17', '17 - Meghalaya'),
    ('18', '18 - Assam'),
    ('20', '20 - Jharkhand'),
    ('22', '22 - Chhattisgarh'),
    ('23', '23 - Madhya Pradesh'),
    ('25', '25 - Daman & Diu'),
    ('26', '26 - Dadra & Nagar Haveli'),
    ('30', '30 - Goa'),
    ('31', '31 - Lakshadweep'),
    ('34', '34 - Puducherry'),
    ('35', '35 - Andaman & Nicobar Islands'),
    ('38', '38 - Ladakh'),
]


class CustomerForm(FlaskForm):
    """Customer form"""
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    gstin = StringField('GSTIN', validators=[
        Optional(),
        Length(max=15),
        Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$|^$',
               message='Invalid GSTIN format')
    ])
    state_code = SelectField('State', choices=STATE_CODES, default='32')
    pin_code = StringField('PIN Code', validators=[Optional(), Length(max=10)])
    credit_limit = FloatField('Credit Limit', validators=[Optional(), NumberRange(min=0)], default=0)
    # Drug License Number (for pharmaceutical customers)
    dl_number = StringField('Drug License Number (DL No.)', validators=[Optional(), Length(max=50)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Customer')
