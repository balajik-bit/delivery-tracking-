from flask import Blueprint, request, jsonify, session
from db import mysql
from flask_bcrypt import Bcrypt
import MySQLdb

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (data['username'], data['email'], hashed_pw))
        mysql.connection.commit()
        return jsonify({'message': 'Signup successful!'})
    except MySQLdb.IntegrityError as e:
        return jsonify({'message': 'Email already registered!'}), 400
    finally:
        cursor.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
    user = cursor.fetchone()
    if user and bcrypt.check_password_hash(user[3], data['password']):
        session['user_id'] = user[0]
        session['username'] = user[1]
        return {'redirect': '/dashboard'}  # Let frontend handle redirect
    return {'message': 'Invalid credentials'}, 401
