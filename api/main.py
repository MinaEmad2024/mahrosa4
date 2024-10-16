from datetime import date
import werkzeug
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column,foreign
from sqlalchemy import Integer, String, Text, DateTime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import smtplib
import pip._vendor.requests
import flask_excel as excel
import xlsxwriter


# Import your forms from the forms.py
from api.forms import CreatePostForm,RegisterUser,LoginUser,CommentPostForm,Booking,OpenResevation

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''
admin = False
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY') #'8BYkEfBA6O6donzWlSihBXox7C0sKR6b' #os.environ.get('FLASK_KEY') 
ckeditor = CKEditor(app)
ckeditor.autoParagraph = False
ckeditor.enterMode = 2
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# TODO: Configure Flask-Login


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db") #'sqlite:///posts.db' #os.environ.get("DB_URI", "sqlite:///posts.db") 
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="BlogPosts")
    Comments: Mapped[list["Comment"]] = relationship(back_populates="blog_post")


# TODO: Create a User table for all your registered users.
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    BlogPosts: Mapped[list["BlogPost"]] = relationship(back_populates="user")
    Comments: Mapped[list["Comment"]] = relationship(back_populates="user")
    Reservations: Mapped[list["Reservation"]] = relationship()


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="Comments")
    blog_post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    blog_post: Mapped["BlogPost"] = relationship(back_populates="Comments")

class Reservation(db.Model):
    __tablename__ = "reservations"
    id:Mapped[int] = mapped_column(Integer, primary_key=True)    
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    phone:Mapped[int] = mapped_column(Integer, nullable=False)
    room:Mapped[str] = mapped_column(String(250), nullable=False)
    from_date:Mapped[str] = mapped_column(String, nullable=False)
    to_date:Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    season:Mapped[str] = mapped_column(String(250),nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

class Status_Of_Reservation(db.Model):
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    status:Mapped[str] = mapped_column(String,nullable=False)




# class Role(db.Model):
#     __tablename__ = "role"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     name: Mapped[str] = mapped_column(String(100), unique=True)


# # Define the UserRoles association table
# class UserRoles(db.Model):
#         __tablename__ = 'user_roles'
#         id: Mapped[int] = mapped_column(Integer, primary_key=True)
#         user.id

excel.init_excel(app) # required since version 0.0.7

with app.app_context():
    db.create_all()

# LoginManager is needed for our application
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)


# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def load_user(user_id):
    #print(user_id)
    return User.query.get(user_id)


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterUser()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            flash("user already exits , please login")
            #error = 'Invalid credentials'
            return redirect(url_for("login"))
        else:
            hashed_password = werkzeug.security.generate_password_hash(form.password.data,
                method="pbkdf2:sha256", salt_length=8)
            new_user = User(
                email=form.email.data,
                password=hashed_password,
                name=form.name.data,
            )
            db.session.add(new_user)
            db.session.commit()
            load_user(new_user.id)
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=["GET", "POST"])
def login():
    global admin
    form = LoginUser()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if werkzeug.security.check_password_hash(user.password, password):
                login_user(user)
                #flash('You were successfully logged in')
                if user.id == 1:
                    admin = True
                    print(admin)
                else:
                    admin = False
                    print(admin)
                return redirect(url_for("get_all_posts")) #, admin  , name=user.name))
            else:
                flash("password incorrect, please try again")
                #error = 'Invalid credentials'
                return redirect(url_for("login"))
        else:
            flash("email incorrect, please try again")
            #error = 'Invalid credentials'
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


def admin_only():
    global admin
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.id != 1:    #admin == False:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    year = date.today().year
    status_exists = db.session.query(Status_Of_Reservation.query.filter_by(id=1).exists()).scalar() #check for the existence of the first record 
    if  status_exists:
        result =db.get_or_404(Status_Of_Reservation,1)
        status = result.status
        print(status)
    else:
        new_status = Status_Of_Reservation(
            status = '1'
        ) 
        db.session.add(new_status)
        db.session.commit() 
        status = db.session.execute(db.select(Status_Of_Reservation).where(Status_Of_Reservation.id == 1)).scalar()
        print(status)

    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, status=status, year=year)


# TODO: Allow logged-in users to comment on posts
# @app.route("/post/<int:post_id>", methods=["GET", "POST"])
# def show_post(post_id):
#     form = CommentPostForm()
#     requested_post = db.get_or_404(BlogPost, post_id)
#     post_comments = db.session.execute(db.select(Comment).where(Comment.blog_post_id == post_id)).scalars()
#     if form.validate_on_submit():
#         new_comment = Comment(
#             text=form.body.data,
#             user_id=current_user.id,
#             blog_post_id=requested_post.id
#         )
#         db.session.add(new_comment)
#         db.session.commit()
#         #return redirect(url_for('get_all_posts'))
#         return redirect(url_for('show_post', post_id=post_id))

#     return render_template("post.html", post=requested_post, form=form, comments=post_comments)


# TODO: Use a decorator so only an admin user can create a new post
# @app.route("/new-post", methods=["GET", "POST"])
# @admin_only()
# def add_new_post():
#     form = CreatePostForm()
#     if form.validate_on_submit():
#         new_post = BlogPost(
#             title=form.title.data,
#             subtitle=form.subtitle.data,
#             body=form.body.data,
#             img_url=form.img_url.data,
#             author=current_user.name,
#             date=date.today().strftime("%B %d, %Y"),
#             user_id=current_user.id
#         )
#         db.session.add(new_post)
#         db.session.commit()
#         return redirect(url_for("get_all_posts"))
#     return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
# @app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
# @admin_only()
# def edit_post(post_id):
#     post = db.get_or_404(BlogPost, post_id)
#     edit_form = CreatePostForm(
#         title=post.title,
#         subtitle=post.subtitle,
#         img_url=post.img_url,
#         author=post.author,
#         body=post.body
#     )
#     if edit_form.validate_on_submit():
#         post.title = edit_form.title.data
#         post.subtitle = edit_form.subtitle.data
#         post.img_url = edit_form.img_url.data
#         post.author = current_user.name
#         post.body = edit_form.body.data
#         db.session.commit()
#         return redirect(url_for("show_post", post_id=post.id))
#     return render_template("make-post.html", form=edit_form, is_edit=True)


# # TODO: Use a decorator so only an admin user can delete a post
# @app.route("/delete/<int:post_id>")
# @admin_only()
# def delete_post(post_id):
#     post_to_delete = db.get_or_404(BlogPost, post_id)
#     db.session.delete(post_to_delete)
#     db.session.commit()
#     return redirect(url_for('get_all_posts'))

@app.route("/reservations", methods=['GET', 'POST'])
@admin_only()
def reservations():
    open_form = OpenResevation()
    result = db.session.execute(db.select(Reservation))
    reservations = result.scalars().all()
    status =db.get_or_404(Status_Of_Reservation,1)
    print(status.status)
    if open_form.validate_on_submit():
        status.status = open_form.status.data
        db.session.commit()
        return redirect(url_for('reservations'))

    return render_template("reservations.html", all_reservations=reservations, form=open_form, status=status.status)


@app.route("/booking", methods=['GET', 'POST'])
@login_required
def booking():
    year = date.today().year
    status =db.get_or_404(Status_Of_Reservation,1)
    if status.status == "1":
        booking_form = Booking()
        if booking_form.validate_on_submit():
            new_reservation = Reservation(
                name=booking_form.name.data,
                phone=booking_form.phone.data,
                room=booking_form.room.data,
                from_date=booking_form.startdate.data,
                to_date=booking_form.enddate.data,
                date=date.today().strftime("%B %d, %Y"),
                season = date.today().year,
                user_id=1 #current_user.id
            )
            db.session.add(new_reservation)
            db.session.commit()
            return "<h1>تم استقبال طلب الحجز بنجاح و سيتم التواصل تليفونيا  معكم لتاكيد الحجز قريبا</h1> <h2>ليتم تحويلكم للصفحة الرئيسية </h2> <a style='color: red;' href='https://st-george-mahrosa.vercel.app/'>اضغط هنا</a>"


        return render_template("booking.html", form=booking_form)
    else:
        return redirect(url_for("get_all_posts"))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():

    if request.method == "POST": 
        data = request.form   
        my_email = "minamaestro2023@gmail.com"
        password = "tjyi kzjq iwbe jndg"
        email = data['email']
        name =data['name']
        phone = data['phone']
        subject = data['message']
        connection = smtplib.SMTP("smtp.gmail.com", 587, timeout=120)
        connection.ehlo()
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email,
                            to_addrs="drmina2007@yahoo.com",
                            msg=f"subject:This is message from {name}\n\n sender phone no. : {phone}\n sender email : {email}\n {subject}"
                            )
        connection.close()
        return render_template("contact.html", msg_sent=True)

    return render_template("contact.html", msg_sent=False)



@app.route("/download_excel", methods=['GET', 'POST'])
def download_excel():
    result = db.session.execute(db.select(Reservation))
    reservations = result.scalars().all()
    #column_names = ['id', 'name', 'phone', 'room', 'from_date', 'to_date', 'date', 'season', 'user_id']
    #return excel.make_response_from_query_sets(reservations, column_names, "xlsx")
    workbook = xlsxwriter.Workbook('reservations.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.add_table('A1:I100000', {'data':reservations, 'columns': [{'header': 'id'},
                                          {'header': 'name'},
                                          {'header': 'phone'},
                                          {'header': 'room'},
                                          {'header': 'from_date'},
                                          {'header': 'to_date'},
                                          {'header': 'date'},
                                          {'header': 'season'},
                                          {'header': 'user_id'},
                                          ]})
    #workbook = excel.make_response_from_query_sets(reservations, column_names, "xlsx")
    return workbook



if __name__ == "__main__":
    app.run(debug=[False], port=5002)