from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, EmailField, IntegerField, PasswordField, validators
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField


class ReviewForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    review = StringField('Отзыв', validators=[DataRequired()], widget=TextArea())
    submit = SubmitField('Отправить')


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password_hash = PasswordField('Пароль', validators=[validators.Length(min=6, max=10),
                                                        validators.EqualTo('password_hash2',
                                                                           message='Пароли должны совпадать')])
    password_hash2 = PasswordField('Подтвердите Пароль', validators=[validators.Length(min=6, max=10)])
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password_hash = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField("Войти")


class PaymentForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    card_number = IntegerField("Номер карты", validators=[DataRequired()])
    submit = SubmitField("Оплатить")


class AddProductForm(FlaskForm):
    name = StringField("Название", validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    stock = IntegerField("Количество", validators=[DataRequired()])
    description = CKEditorField('Описание', validators=[DataRequired()])
    keys = FileField('Ключи Активации(.txt)', validators=[DataRequired()])
    img_1 = FileField('Главное фото', validators=[DataRequired()])
    img_2 = FileField('Фото 2', validators=[DataRequired()])
    img_3 = FileField('Фото 3', validators=[DataRequired()])
    submit = SubmitField("Добавить")


class SearchForm(FlaskForm):
    searched = StringField("Поиск", validators=[DataRequired()])
    submit = SubmitField("Кнопка")
