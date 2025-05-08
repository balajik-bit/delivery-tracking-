from extensions import db
from datetime import datetime

class DeliveryStatusUpdate(db.Model):
    __tablename__ = 'delivery_status_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey('deliveries.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    delivery = db.relationship('Delivery', back_populates='status_updates')
    
    def __repr__(self):
        return f'<DeliveryStatusUpdate {self.id}>'

class Delivery(db.Model):
    __tablename__ = 'deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, in_transit, delivered
    current_location = db.Column(db.String(100))
    estimated_delivery = db.Column(db.DateTime)
    actual_delivery = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', back_populates='delivery')
    status_updates = db.relationship('DeliveryStatusUpdate', back_populates='delivery', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Delivery {self.tracking_number}>' 