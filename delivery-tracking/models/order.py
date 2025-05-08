from extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_phone = db.Column(db.String(20))
    shipping_name = db.Column(db.String(100))
    
    # Relationships
    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    delivery = db.relationship('Delivery', back_populates='order', uselist=False)
    
    def __repr__(self):
        return f'<Order {self.id}>' 