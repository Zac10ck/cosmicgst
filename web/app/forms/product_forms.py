"""Product and Category forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, BooleanField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange


class CategoryForm(FlaskForm):
    """Category form"""
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')


class ProductForm(FlaskForm):
    """Product form"""
    name = StringField('Product Name', validators=[DataRequired()])
    barcode = StringField('Barcode', validators=[Optional()])
    hsn_code = StringField('HSN Code', validators=[Optional()])
    unit = SelectField('Unit', choices=[
        ('NOS', 'Numbers (NOS)'),
        ('PCS', 'Pieces (PCS)'),
        ('BOX', 'Box (BOX)'),
        ('KG', 'Kilograms (KG)'),
        ('LTR', 'Liters (LTR)'),
        ('MTR', 'Meters (MTR)'),
        ('SET', 'Set (SET)'),
        ('PKT', 'Packet (PKT)'),
    ], default='NOS')
    price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    purchase_price = FloatField('Purchase Price', validators=[Optional(), NumberRange(min=0)], default=0)
    gst_rate = SelectField('GST Rate (%)', choices=[
        ('0', '0%'),
        ('5', '5%'),
        ('12', '12%'),
        ('18', '18%'),
        ('28', '28%'),
    ], default='18', coerce=str)
    stock_qty = FloatField('Stock Quantity', validators=[Optional(), NumberRange(min=0)], default=0)
    low_stock_alert = FloatField('Low Stock Alert', validators=[Optional(), NumberRange(min=0)], default=10)
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    # Batch and Expiry tracking (for pharmaceuticals)
    batch_number = StringField('Batch Number', validators=[Optional()])
    expiry_date = DateField('Expiry Date', validators=[Optional()], format='%Y-%m-%d')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Product')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Categories will be populated in the view
        self.category_id.choices = [(0, '-- No Category --')]
