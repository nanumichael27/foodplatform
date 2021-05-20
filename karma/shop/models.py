from karma import db
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
# from karma.auth.models import User
from datetime import datetime
from flask_login import current_user
from datetime import datetime


class HasImage:
    def storeImage(self):
        pass

    def deleteImage(self):
        pass


class SavableMixin:
    def save(self):
        db.session.add(self)
        db.session.commit()


class Category(db.Model, HasImage):
    category_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    image = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    # products = db.relationship('Product', backref=db.backref('category', lazy=True))

    def deleteImage(self):
        from karma.admin.views import Image, CATEGORY_URL, PRODUCT_URL
        image = Image(None, CATEGORY_URL, self.image)
        image.deleteImage()

    def storeImage(self, image):
        from karma.admin.views import Image, CATEGORY_URL, PRODUCT_URL
        image = Image(image, CATEGORY_URL)
        self.image = image.create()


class Product(db.Model):
    product_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )
    title = db.Column(
        db.String(100)
    )
    description = db.Column(
        db.String(500),
        nullable=True
    )
    price = db.Column(
        db.Float,
        nullable=False,
        default=0.00
    )
    times_bought = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    views = db.Column(
        db.Integer,
        nullable= False,
        default = 0
    )
    in_stock = db.Column(
        db.Integer,
        nullable=False,
        default=3
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('category.category_id'),
        nullable=False
    )
    
    # images = db.relationship('ProductImage', backref=db.backref('product', lazy=True))
    category = db.relationship(
        'Category', backref=db.backref('product', lazy=True))

    def addImages(self, images):
        for image in images:
            image_name = self.storeImage(image)
            img = ProductImage(name=image_name)
            self.images.append(img)

    def storeImage(self, image):
        from karma.admin.views import Image, CATEGORY_URL, PRODUCT_URL
        image = Image(image, PRODUCT_URL)
        return image.create()

    def delete(self,):
        self.deleteImages()
        db.session.delete(self)
        db.session.commit()

    def deleteImages(self,):
        for image in self.images:
            image.delete()
        return True
    
    def incrementTimesViewed(self):
        self.views+=1
        db.session.add(self)
        db.session.commit()

    def incrementTimesBought(self, quantity = 1):
        self.times_bought+=quantity
        db.session.add(self)
        db.session.commit()


class ProductImage(db.Model):
    image_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.product_id'),
        nullable=False
    )

    name = db.Column(
        db.String(100)
    )

    product = db.relationship(
        'Product',
        backref=db.backref('images', lazy=True),
    )

    def delete(self):
        from karma.admin.views import Image, CATEGORY_URL, PRODUCT_URL
        image = Image(None, PRODUCT_URL, self.name)
        image.deleteImage()
        db.session.delete(self)


OrderStatus = {
    'PENDING': 'pending',
    'CLOSED': 'closed',
    'TRANSIT': 'transit',
    'DELIVERED': 'delivered'
}

class Order(db.Model):
    order_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    status = db.Column(
        db.String(15),
        nullable=False,
        default=OrderStatus['PENDING']
    )

    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id'),
        nullable=False
    )

    user = db.relationship(
        'User',
        backref=db.backref('orders', lazy=True)
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0.00
    )

    @staticmethod
    def count():
        return len(Order.query.all())

    @staticmethod
    def pendingOrders():
        return len(Order.query.filter_by(status=OrderStatus['PENDING']).all())

    @staticmethod
    def deliveredOrders():
        return len(Order.query.filter_by(status=OrderStatus['DELIVERED']).all())

    @staticmethod
    def transitOrders():
        return len(Order.query.filter_by(status=OrderStatus['TRANSIT']).all())

    def setLocation(self, location):
        self.location.append(location)

    def setUpItems(self, ):
        for item in current_user.cart[0].items:
            newItem = OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                total=item.total
            )
            item.product.incrementTimesBought(item.quantity)
            self.orderitems.append(newItem)
            self.updateTotal()

    def updateTotal(self):
        self.total = current_user.cart[0].total


class OrderItem(db.Model):
    order_item_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.order_id'),
        nullable=False
    )

    order = db.relationship(
        'Order',
        backref=db.backref('orderitems', lazy=True)
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.product_id'),
        nullable=False,
    )

    product = db.relationship(
        'Product',
        uselist=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0.00
    )

    def calculateTotal(self):
        return self.product.price*self.quantity

    def updateTotal(self):
        self.total = self.calculateTotal()
        self.save()
        return True


class Cart(db.Model, SavableMixin):

    def __init__(self, **kwargs):
        super(Cart, self).__init__(**kwargs)
        self.updateTotal()
        print('cart created')

    cart_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.user_id'),
        nullable=False,
    )

    user = db.relationship(
        'User',
        backref='cart',
        uselist=True,
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0.00
    )

    def itemExists(self, item):
        for product in self.items:
            if str(product.product_id) == str(item.product_id):
                return True
        return False

    def retrieveItem(self, item):
        for product in self.items:
            if str(product.product_id) == str(item.product_id):
                return product

    def addItem(self, item):
        if(self.itemExists(item)):
            existingItem = self.retrieveItem(item)
            existingItem.quantity = int(
                existingItem.quantity) + int(item.quantity)
            print(
                """
                This item already exists
                """
            )
        else:
            self.items.append(item)
        self.save()
        return True

    def calculateTotal(self):
        total = 0
        for item in self.items:
            total += item.total
        return total

    def updateTotal(self):
        self.total = self.calculateTotal()
        self.save()
        return True

    def clear(self):
        self.total = 0
        for item in self.items:
            item.delete()
        self.save()


class CartItem(db.Model, SavableMixin):

    def __init__(self, **kwargs):
        super(CartItem, self).__init__(**kwargs)
        # self.updateTotal()
        # print('cart item created')

    cart_item_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    cart_id = db.Column(
        db.Integer,
        db.ForeignKey('cart.cart_id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.product_id'),
        nullable=False
    )

    product = db.relationship(
        'Product',
        uselist=False
    )

    cart = db.relationship(
        'Cart',
        backref=db.backref('items', lazy=True)
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )

    def calculateTotal(self):
        return self.product.price*self.quantity

    def updateTotal(self):
        self.total = self.calculateTotal()
        self.save()
        return True

    def delete(self):
        db.session.delete(self)


class Location(db.Model):
    location_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.order_id'),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False,
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    country = db.Column(
        db.String(200),
        nullable=True
    )

    address = db.Column(
        db.String(200),
        nullable=True
    )

    order = db.relationship(
        'Order',
        backref=db.backref('location', lazy=True)
    )


PaymentStatus = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'SUCCESSFUL': 'successful'
}


class Payment(db.Model):
    payment_id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True
    )

    type = db.Column(
        db.String(30),
        nullable=True
    )

    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    paid = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    refrence = db.Column(
        db.String(150),
        nullable=True,
    )
