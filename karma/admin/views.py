from flask import (
    Blueprint, flash, redirect, g, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from karma.auth.views import admin_required, admin_guest
from karma.auth.models import User
from karma.shop.models import Product, ProductImage, Category, Order
from karma import db
import os, json, base64, uuid
CATEGORY_URL = 'karma/static/categoryuploads/'
PRODUCT_URL = 'karma/static/productuploads/'

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard/', methods=('GET', ))
@admin_required
def dashboard():
    numberOfCustomers = User.count()
    numberOfOrders = Order.count()
    return render_template(
        'admin/dashboard.html',
        numberOfCustomers = numberOfCustomers,
        numberOfOrders = numberOfOrders,
        pendingOrders = Order.pendingOrders(),
        deliveredOrders = Order.deliveredOrders(),
        transitingOrders = Order.transitOrders(),
    )


@bp.route('/categories/')
@admin_required
def categories():
    categories = Category.query.all()
    categories.reverse()
    return render_template('admin/categories.html', categories = categories)


@bp.route('/login/', methods=('GET', 'POST'))
@admin_guest
def login():
    if (request.method == 'POST'):
        usernameoremail = request.form['username']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=usernameoremail).first()
        if user is None:
            user = User.query.filter_by(email=usernameoremail).first()

        if user is None:
            error = 'Incorrect Username or Email'
        elif not user.check_password(password):
            error = 'Incorrect Password'
        elif not user.is_admin:
            error = "You don't have the authorization to access the Admin page"

        if error is None:
            from flask_login import login_user
            login_user(user)
            return redirect(url_for('admin.dashboard'))

        flash(error)

    return render_template('admin/login.html')


@bp.route('/categories/add', methods=('POST', ))
@admin_required
def add_category():
    if request.method == 'POST':
        image = request.form['image']
        # image_name = storeImage(image, CATEGORY_URL)
        category = Category(
            name=request.form['title']
        )
        category.storeImage(image)
        db.session.add(category)
        db.session.commit()
        return 'success'


@bp.route('/categories/delete', methods=('POST', ))
@admin_required
def delete_category():
    if request.method == 'POST':
        category = Category.query.get(request.form['id'])
        if category.product: return 'Category contains products already'
        category.deleteImage()
        db.session.delete(category)
        db.session.commit()
        return 'success'


@bp.route('/products/', methods=('GET', 'POST'))
@admin_required
def add_product():
    if request.method == 'POST':
        import json
        images = json.loads(request.form['images'])
        category = Category.query.get(request.form['category'])
        product = Product(
            title = request.form['title'],
            description = request.form['description'],
            price = request.form['price'],
            category = category,
            in_stock = request.form['stock'],
        )
        product.addImages(images)
        db.session.add(product)
        db.session.commit()
        return 'success'
    products = Product.query.all()
    products.reverse()
    categories = Category.query.all()
    return render_template('admin/addproduct.html', products=products, categories=categories)


@bp.route('/product/delete', methods=('POST', ))
@admin_required
def delete_product():
    if request.method == 'POST':
        product = Product.query.get(request.form['id'])
        if not product:
            return 'Product does not exist in the database'
        else:
            product.delete()
            return 'success'

@bp.route('/product/edit', methods=('POST', )) 
@admin_required
def edit_product():
    if request.method == 'POST':
        product = Product.query.get(request.form['id'])
        if not product:
            return 'Product does not exist in the database'
        else:
            category = Category.query.get(request.form['category'])
            product.title = request.form['title']
            product.price = request.form['price']
            product.in_stock = request.form['stock']
            product.category = category
            product.description = request.form['description']

            db.session.add(product)
            result = db.session.commit()
            return 'success'


# # Store an image in the database and return the name of the image
# def storeImage(image, path, name=None):
#     image = cleanImage(image)
#     image_name = generateImageName()
#     if name is not None:
#         image_name = name
#     path = path+image_name
#     with open(path, 'wb') as f:
#                 f.write(base64.b64decode(image))
#     return image_name


# # Generate a unique name for an image
# def generateImageName():
#     return str(uuid.uuid4())+'.png'


# # Remove unnecessary string at the begining of any image
# def cleanImage(image):
#     x, image = image.split(',')
#     return image


# # Delete an image
# def deleteImage(image, path=''):
#     os.remove(path+image)

class Image:
    def __init__(self, content='', path='', name=None):
        self.name = self.generateImageName() if name is None else name
        self.content = content
        self.path=path+self.name
        self.os = os

    def parse(self):
        x, self.content = self.content.split(',')
        self.content = base64.b64decode(self.content)

    def create(self):
        self.parse()
        with open(self.path, 'wb') as f:
            f.write(self.content)
        return self.name

    def generateImageName(self):
        return str(uuid.uuid4())+'.png'

    def deleteImage(self):
        try:
            self.os.remove(self.path)
        except:
            return 'file does not exist'



    

    
