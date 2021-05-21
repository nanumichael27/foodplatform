from flask import (
    Blueprint, flash, redirect, g, render_template, request, url_for
)
from werkzeug.exceptions import abort

# from karma.auth.views import login_required
from flask_login import login_required, current_user
from karma import db
from .models import Category, Product, ProductImage, CartItem, Order, Location
import json
from sqlalchemy import desc
bp = Blueprint('shop', __name__)


@bp.route('/')
@login_required
def index():
    products = Product.query.all()
    products.reverse()
    recommended = Product.query.order_by(desc(Product.views)).limit(2)
    return render_template('shop/index.html', products=products, recommended=recommended)

@bp.route('/product/<int:product_id>/')
@login_required
def single_product(product_id):
    product = Product.query.get(product_id)
    product.incrementTimesViewed()
    return render_template('shop/product_single.html', product=product)

@bp.route('/add-to-cart/', methods=('POST',))
@login_required
def addToCart():
    if request.method == 'POST':
        productId = request.form['id']
        quantity = request.form['quantity'] or 1
        item = CartItem(
            product_id = productId,
            quantity = quantity
        )
        result = current_user.addToCart(item)
        if result is True:
            return 'success'
        else: 
            return 'This item is already in the cart. go to cart and increase the quantity'

@bp.route('/cart/', methods=('GET', 'POST'))
@login_required
def cart():
    if request.method == 'GET':
        if not current_user.cart[0].items:
            pass
        else:
            for item in current_user.cart[0].items:
                item.updateTotal()
            current_user.cart[0].updateTotal()
        return render_template('shop/shopping_cart.html', cart_items=current_user.cart[0].items, cart=current_user.cart[0])


@bp.route('/cart/update', methods=('GET', 'POST'))
@login_required
def updateCart():
    if request.method == 'POST':
        id = request.form['id']
        quantity = request.form['quantity']

        item = CartItem.query.get(id)
        item.quantity=quantity
        item.save()
        return 'success'

@bp.route('/checkout/', methods=('GET', 'POST'))
@login_required
def checkout():
    return render_template('shop/checkout.html', order_items=current_user.cart[0].items, cart=current_user.cart[0])

@bp.route('/cart/deleteitem/', methods=('POST', 'GET'))
@login_required
def deleteItemFromCart():
    if request.method == "POST":
        id = request.form['id']
        item = CartItem.query.get(id)
        db.session.delete(item)
        db.session.commit()
        return 'success'

@bp.route('/cart/placeorder/', methods=('POST', ))
@login_required
def placeOrder():
    coords = json.loads(request.form['coords'])
    print(coords)
    location = Location(
        longitude=coords['lng'],
        latitude=coords['lat'],
        country=coords['country'],
        address=coords['address']
    )
    current_user.placeOrder(location)
    return 'success'

@bp.route('/confirmation/', methods=('GET', ))
@login_required
def confirmation():
    return render_template('shop/confirmation.html', order=current_user.orders[-1])

@bp.route('/orders/', methods=('GET',))
@login_required
def viewOrders():
    return render_template('shop/orders.html', orders=current_user.orders)