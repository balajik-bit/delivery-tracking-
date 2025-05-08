from flask import Blueprint, request, jsonify
from db import mysql

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/add-delivery', methods=['POST'])
def add_delivery():
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO deliveries (customer_id, item_name, status, location) VALUES (%s, %s, %s, %s)",
                   (data['customer_id'], data['item_name'], "Pending", "Warehouse"))
    mysql.connection.commit()
    return jsonify({"message": "Delivery created"})

@delivery_bp.route('/update-status/<int:id>', methods=['PUT'])
def update_status(id):
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE deliveries SET status = %s, location = %s WHERE id = %s",
                   (data['status'], data['location'], id))
    mysql.connection.commit()
    return jsonify({"message": "Status updated"})

@delivery_bp.route('/track/<int:id>', methods=['GET'])
def track_delivery(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT status, location FROM deliveries WHERE id = %s", (id,))
    result = cursor.fetchone()
    if result:
        return jsonify({"status": result[0], "location": result[1]})
    return jsonify({"message": "Delivery not found"}), 404
