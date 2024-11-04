from sqlalchemy import *
from sqlalchemy import create_engine, text # Import text
engine = create_engine()
conn = engine.connect()
def setSchema():
    cursor = conn.execute(text("SET search_path TO wf2322;")) 

def selectUsers():
    cursor = conn.execute(text("select * from users"))
    return cursor.fetchall()
from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

app = Flask(__name__)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "Hello Boss!"

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password!')
        return home()


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
