from flask import Flask, request, render_template, url_for, flash, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, EmailField, IntegerField, PasswordField, validators
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'dsjahfjshdfjasf54564'

UPLOAD_FOLDER = 'static/img/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Сначала нужно войти в аккаунт'


class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(70), nullable=False)
    review = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.Date, default=date.today())


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)

    img_1 = db.Column(db.String(150), nullable=False)
    img_2 = db.Column(db.String(150), nullable=False)
    img_3 = db.Column(db.String(150), nullable=False)


class ReviewForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    review = StringField('Отзыв', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Отправить')


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password_hash = PasswordField('Пароль', [validators.DataRequired(),
                                             validators.EqualTo('password_hash2', message='Пароли должны совпадать')])
    password_hash2 = PasswordField('Подтвердите Пароль')
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password_hash = PasswordField('Пароль', [validators.DataRequired()])
    submit = SubmitField("Войти")


class AddProductForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    stock = IntegerField("Количество", validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()], widget=TextArea())
    img_1 = FileField('Главное фото', validators=[DataRequired()])
    img_2 = FileField('Фото 2', validators=[DataRequired()])
    img_3 = FileField('Фото 3', validators=[DataRequired()])
    submit = SubmitField("Добавить")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    form = ReviewForm()
    reviews = Reviews.query.order_by(Reviews.date_added)
    if form.validate_on_submit() and request.method == 'POST':
        review = Reviews(username=form.username.data, review=form.review.data)
        db.session.add(review)
        db.session.commit()
        form.username.data = ''
        form.review.data = ''
    return render_template('reviews.html', form=form, reviews=reviews)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password_hash.data, 'sha256')
        user = User(name=form.name.data, email=form.email.data, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались')
        return redirect(url_for('index'))
    our_users = User.query.order_by(User.name)
    return render_template('register.html', form=form, our_users=our_users)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password_hash.data):
                login_user(user)
                flash('Вы успешно вошли!')
                return redirect(url_for('index'))
            else:
                flash('Неправильный пароль')
        else:
            flash('Такого пользователя не существует')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из аккаунта')
    return redirect(url_for('login'))


@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()
    if request.method == 'POST':
        name = form.name.data
        price = form.price.data
        stock = form.stock.data
        desc = form.description.data

        img_1 = request.files['img_1']
        pic_name1 = str(uuid.uuid1()) + '_' + secure_filename(img_1.filename)
        saver1 = request.files['img_1']
        saver1.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name1))
        img_1 = pic_name1

        img_2 = request.files['img_2']
        pic_name2 = str(uuid.uuid1()) + '_' + secure_filename(img_2.filename)
        saver2 = request.files['img_2']
        saver2.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name2))
        img_2 = pic_name2

        img_3 = request.files['img_3']
        pic_name3 = str(uuid.uuid1()) + '_' + secure_filename(img_3.filename)
        saver3 = request.files['img_3']
        saver3.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name3))
        img_3 = pic_name3

        product = Products(name=name, price=price, stock=stock, description=desc, img_1=img_1, img_2=img_2, img_3=img_3)
        db.session.add(product)
        flash('Товар был успешно добавлен')
        db.session.commit()
        return redirect(url_for('add_product'))

    return render_template('add-product.html', form=form)


@app.route('/admin')
@login_required
def admin():
    products = Products.query.all()
    return render_template('admin.html', products=products)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/catalog')
def catalog():
    return render_template('catalog.html')


@app.route('/guarantees')
def guarantees():
    return render_template('guarantees.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
