from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditorField
from wtforms.fields import DateField, DateTimeLocalField, FieldList 
import datetime
from datetime import UTC


rooms = [('Single Room','Single Room'),('Double Room','Double Room'),('Triple Room','Triple Room'),('Small Suite','Small Suite'),('غرفة ضخمة','غرفة ضخمة')]
status= [('1','فتح الحجز'),('2','اغلاق الحجز')]
# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterUser(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign me up ")


# TODO: Create a LoginForm to login existing users
class LoginUser(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# TODO: Create a CommentForm so users can leave comments below posts
class CommentPostForm(FlaskForm):
    body = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class Booking(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Mobile No.", validators=[DataRequired(), Length(min=10, max=10, message="At least 10 numbers")])
    room = SelectField("Choose Room", choices=rooms, validators=[DataRequired()])
    startdate  =  DateTimeLocalField('Expiration date', 
                                      validators=[DataRequired()], 
                                      format="%Y-%m-%dT%H:%M", default=lambda : datetime.datetime.utcnow(),#+relativedelta(months=+6),
                                      render_kw={
                                          'min': datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M"),
                                                                                      # 'max': str((datetime.datetime.utcnow()+relativedelta(months=+6)).strftime("%Y-%m-%dT%H:%M")),
                                          }
                                    )                                                                       #DateField("Start Date", format='%Y-%m-%d', validators=[DataRequired()])
    enddate = DateTimeLocalField('Expiration date', 
                                      validators=[DataRequired()], 
                                      format="%Y-%m-%dT%H:%M", default=lambda : datetime.datetime.utcnow(),#+relativedelta(months=+6),
                                      render_kw={
                                          'min': datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M"),
                                                                                      # 'max': str((datetime.datetime.utcnow()+relativedelta(months=+6)).strftime("%Y-%m-%dT%H:%M")),
                                          }
                                    )                                                                                  #DateField("End Date", format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField("Submit")

class OpenResevation(FlaskForm):
    status = SelectField("Reservation Status", choices=status, validators=[DataRequired()])
    submit = SubmitField("Submit")