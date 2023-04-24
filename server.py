from flask import Flask, request, render_template, url_for, flash, redirect, current_app, session, jsonify
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from webforms import ReviewForm, PaymentForm, SearchForm, LoginForm, RegisterForm, AddProductForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_ckeditor import CKEditor
from flask_restful import Api, abort, Resource

import os
import smtplib
import uuid

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'dsjahfjshdfjasf54564'
api = Api(app)

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

    keys = db.relationship("ActivationKeys", back_populates='product')


class ActivationKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(70), nullable=False)
    product_id = db.Column(db.Integer,
                           db.ForeignKey("products.id"))
    product = db.relationship('Products')


# api ресурсы
def abort_if_not_found(id, model):
    response = model.query.get_or_404(id)
    if not response:
        abort(404, message=f'Id {id} not found')


class ProductResource(Resource):
    def get(self, id):
        abort_if_not_found(id, Products)
        product = Products.query.get_or_404(id)
        return jsonify(
            {'response':
                {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock': product.stock,
                }
            })

    @login_required
    def delete(self, id):
        # пока не добавится авторизация через api воспользоваться будет невозможно ☹︎
        if current_user.id != 1:
            return jsonify({'message': '403 forbidden'})
        abort_if_not_found(id, Products)
        product = db.session.query(Products).get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': 'OK'})


class ProductListResource(Resource):
    def get(self):
        products = Products.query.all()
        return jsonify(
            {
                'response': [{
                    'id': el.id,
                    'name': el.name,
                    'price': el.price,
                    'stock': el.stock,
                } for el in products],
            }
        ) 


class UserResource(Resource):
    def get(self, id):
        abort_if_not_found(id, User)
        user = User.query.get_or_404(id)
        return jsonify(
            {
                'response': {
                    'id' : user.id,
                    'name': user.name,
                    'email': user.email,
                }
            }
        )

    @login_required
    def delete(self, id):
        # работает идентично product (никак)
        if current_user.id != 1:
            return jsonify({'message': '403 forbidden'})
        abort_if_not_found(id, User)
        user = db.session.query(User).get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return jsonify(
            {
                'response': [{
                    'id' : el.id,
                    'name': el.name,
                    'email': el.email,
                } for el in users]
            }
        )


# определение url адресов для запросов к api
api.add_resource(ProductResource, '/api/v1/products/<int:id>')
api.add_resource(ProductListResource, '/api/v1/products')
api.add_resource(UserResource, '/api/v1/users/<int:id>')
api.add_resource(UserListResource, '/api/v1/users')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    form = ReviewForm()
    reviews = Reviews.query.order_by(Reviews.date_added.desc())
    if form.validate_on_submit() and request.method == 'POST':
        review = Reviews(username=form.username.data, review=form.review.data)
        db.session.add(review)
        db.session.commit()
        form.username.data = ''
        form.review.data = ''
    return render_template('reviews.html', form=form, reviews=reviews)


@app.route('/reviews/delete/<int:id>')
@login_required
def delete_review(id):
    review_to_delete = Reviews.query.get_or_404(id)
    id = current_user.id
    if id == 1:
        try:
            db.session.delete(review_to_delete)
            db.session.commit()
            flash('Отзыв успешно удалён!')
            return redirect(url_for('reviews'))
        except:
            flash('Произошла ошибка при удалении отзыва!')
            return redirect(url_for('reviews'))
    else:
        flash('У тебя нет прав для удаления этого отзыва!')
        return redirect(url_for('reviews'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password_hash.data, 'sha256')
            user = User(name=form.name.data, email=form.email.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
            flash('Вы успешно зарегистрировались')
            return redirect(url_for('index'))
        else:
            flash('Пользователь с такой почтой уже существует')
    return render_template('register.html', form=form)


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


def create_product_photo(file):
    img = file
    pic_name = str(uuid.uuid1()) + '_' + secure_filename(img.filename) + '.png'
    saver = file
    saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
    return pic_name


@app.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.id == 1:
        form = AddProductForm()
        if request.method == 'POST':
            name = form.name.data
            price = form.price.data
            stock = form.stock.data
            desc = form.description.data

            img_1 = create_product_photo(request.files['img_1'])
            img_2 = create_product_photo(request.files['img_2'])
            img_3 = create_product_photo(request.files['img_3'])

            product = Products(name=name, price=price, stock=stock, description=desc, img_1=img_1, img_2=img_2,
                               img_3=img_3)
            db.session.add(product)
            db.session.commit()

            keys = request.files['keys']
            filename = secure_filename(keys.filename)
            keys.save(os.path.join("static", filename))
            with open(f"static/{filename}") as f:
                file_content = f.read().split('\n')
                for key in file_content:
                    activate_key = ActivationKeys(key=key)
                    product.keys.append(activate_key)
                    db.session.commit()
            if os.path.isfile(f"static/{filename}"):
                os.remove(f"static/{filename}")

            flash('Товар был успешно добавлен')
            return redirect(url_for('add_product'))

        return render_template('add-product.html', form=form)
    else:
        flash('У вас нет прав доступа')
        return redirect(url_for('index'))


@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if current_user.id == 1:
        form = AddProductForm()
        form.submit.label.text = 'Редактировать'
        product = Products.query.get_or_404(id)
        if request.method == 'POST':
            product.name = form.name.data
            product.price = form.price.data
            product.stock = form.stock.data
            product.description = form.description.data

            keys = request.files['keys']
            filename = secure_filename(keys.filename)
            keys.save(os.path.join("static", filename))
            with open(f"static/{filename}") as f:
                file_content = f.read().split('\n')
                for key in file_content:
                    if key:
                        activate_key = ActivationKeys(key=key)
                        product.keys.append(activate_key)
                        db.session.commit()
            if os.path.isfile(f"static/{filename}"):
                os.remove(f"static/{filename}")

            if request.files.get('img_1'):
                try:
                    os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_1))
                    product.img_1 = create_product_photo(request.files['img_1'])
                except:
                    product.img_1 = create_product_photo(request.files['img_1'])
            if request.files.get('img_2'):
                try:
                    os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_2))
                    product.img_2 = create_product_photo(request.files['img_2'])
                except:
                    product.img_2 = create_product_photo(request.files['img_2'])
            if request.files.get('img_3'):
                try:
                    os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_3))
                    product.img_3 = create_product_photo(request.files['img_3'])
                except:
                    product.img_3 = create_product_photo(request.files['img_3'])
            db.session.commit()
            flash('Товар успешо изменён')
            return redirect(url_for('admin'))
        else:
            form.name.data = product.name
            form.price.data = product.price
            form.stock.data = product.stock
            form.description.data = product.description
            return render_template('edit_product.html', form=form)
    else:
        flash('У вас нет прав доступа')
        return redirect(url_for('index'))


@app.route('/delete-product/<int:id>', methods=['POST'])
def delete_product(id):
    if current_user.id == 1:
        product = Products.query.get_or_404(id)
        if request.method == 'POST':
            try:
                os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_1))
                os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_2))
                os.unlink(os.path.join(current_app.root_path, 'static/img/products/' + product.img_3))
            except:
                print('ERROR')
            db.session.delete(product)
            db.session.commit()
            flash('Товар успешно удалён')
        return redirect(url_for('admin'))
    else:
        flash('У вас нет прав доступа')
        return redirect(url_for('index'))


@app.route('/product/<int:id>')
def product(id):
    product = Products.query.get_or_404(id)
    return render_template('product.html', product=product)


def MagerDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False


@app.route('/add-cart', methods=['POST'])
def add_cart():
    try:
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        product = Products.query.filter_by(id=product_id).first()
        if product_id and quantity and request.method == 'POST':
            dictItems = {product_id: {'name': product.name, 'price': product.price, 'quantity': quantity,
                                      'image': product.img_1}}
            if 'Shoppingcart' in session:
                if product_id in session['Shoppingcart']:
                    session.modified = True
                    for key, item in session['Shoppingcart'].items():
                        if int(product.stock) >= int(item['quantity']) + int(quantity):
                            if int(key) == int(product_id):
                                item['quantity'] = int(item['quantity']) + int(quantity)
                        else:
                            item['quantity'] = int(product.stock)
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], dictItems)
                    return redirect(request.referrer)
            else:
                session['Shoppingcart'] = dictItems
                return redirect(request.referrer)
    except:
        pass
    finally:
        return redirect(request.referrer)


@app.route('/cart')
def get_cart():
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('catalog'))
    grandtotal = 0
    product_id = {}
    for key, product in session['Shoppingcart'].items():
        prod = Products.query.get_or_404(key)
        grandtotal += int(product['price']) * int(product['quantity'])
        product_id[key] = int(prod.stock)
    return render_template('cart.html', grandtotal=grandtotal, product_id=product_id)


@app.route('/update-cart/<int:id>', methods=['POST'])
def update_cart(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('index'))
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        try:
            session.modified = True
            for key, item in session['Shoppingcart'].items():
                if int(key) == id:
                    item['quantity'] = quantity
                    flash('Товар обновлён')
                    return redirect(url_for('get_cart'))

        except Exception as e:
            print(e)
            return redirect(url_for('get_cart'))


@app.route('/delete-item/<int:id>')
def delete_item(id):
    if 'Shoppingcart' not in session or len(session['Shoppingcart']) <= 0:
        return redirect(url_for('index'))
    try:
        session.modified = True
        for key, item in session['Shoppingcart'].items():
            if int(key) == id:
                session['Shoppingcart'].pop(key, None)
                return redirect(url_for('get_cart'))
    except Exception as e:
        print(e)
        return redirect(url_for('get_cart'))


@app.route('/clear-cart')
def clear_cart():
    try:
        session.pop('Shoppingcart', None)
        return redirect(url_for('index'))
    except Exception as e:
        print(e)


def send_notification(email, txt):
    msg = MIMEMultipart()
    msg['From'] = 'makeev12358@yandex.ru'
    msg['To'] = email
    msg['Subject'] = 'ProgramStore ключ'
    message = txt
    msg.attach(MIMEText(message))
    try:
        mailserver = smtplib.SMTP('smtp.yandex.ru', 587)
        mailserver.set_debuglevel(True)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login('makeev12358@yandex.ru', 'dhepsvxameykejpq')
        mailserver.sendmail('makeev12358@yandex.ru', email, msg.as_string())
        mailserver.quit()
        print("Письмо успешно отправлено")
    except smtplib.SMTPException:
        print("Ошибка: Невозможно отправить сообщение")


@app.route('/pay', methods=['GET', 'POST'])
def pay():
    form = PaymentForm()
    if form.validate_on_submit():
        email = form.email.data
        card_num = form.card_number.data
        keys = []
        for key, prod in session['Shoppingcart'].items():
            count = int(prod['quantity'])
            name = prod['name']
            product = Products.query.get_or_404(key)
            for i in range(count):
                keys.append(product.keys[i].key + ' ' + name)
            for j in range(count):
                db.session.delete(product.keys[j])
                db.session.commit()
            product.stock = int(product.stock) - count
            db.session.commit()
        send_notification(email, '\n'.join(keys))
        try:
            session.pop('Shoppingcart', None)
        except Exception as e:
            print(e)
        return redirect(url_for('index'))
    return render_template('pay.html', form=form)


@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    products = Products.query
    product.searched = form.searched.data
    if form.validate_on_submit() and product.searched:
        products = products.filter(Products.name.like('%' + product.searched + '%')).all()
        return render_template('search.html', form=form, searched=product.searched, products=products)
    else:
        return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin():
    if current_user.id == 1:
        products = Products.query.all()
        return render_template('admin.html', products=products)
    else:
        flash('У вас нет прав доступа')
        return redirect(url_for('index'))


@app.route('/')
def index():
    product = Products.query.order_by(Products.stock).filter(Products.stock > 0)
    count = 4 if len(list(product)) > 4 else len(list(product))
    return render_template('index.html', product=product, count=count)


@app.route('/catalog')
def catalog():
    products = Products.query.filter(Products.stock > 0)
    return render_template('catalog.html', products=products)


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
    app.run()
