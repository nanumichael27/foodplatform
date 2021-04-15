from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from karma import db
from datetime import datetime
from flask_login import UserMixin
from karma.shop.models import Cart, Order, OrderItem


class User(db.Model, UserMixin):
    id = db.Column('user_id', db.Integer, primary_key=True,
                   unique=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    fullname = db.Column(db.String(50), nullable=False)
    _password = db.Column('password', db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False,)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.now
    )
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    email_is_verified = db.Column(db.Boolean, nullable=False, default=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        """Store the password as a hash for security"""
        self._password = generate_password_hash(value)

    def check_password(self, value):
        return check_password_hash(self._password, value)

    def addToCart(self, CartItem):
        if not self.cart:
            self.createCart()

        return self.cart[0].addItem(CartItem)

    def createCart(self):
        cart = Cart(user_id = self.id)
        self.cart.append(cart)
        print(self.cart)
        # db.session.add(self)
        # db.session.commit()

    def placeOrder(self, location):
        order = Order()
        order.setLocation(location)
        order.setUpItems()
        self.orders.append(order)
        self.cart[0].clear()
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def count():
        return len(User.query.all())
