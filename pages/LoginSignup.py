from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
app = Flask(__name__)
uri='postgresql://wf2322:St278-Ahobo$#cGHh@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/w4111'
engine=create_engine(uri)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        Post_Username = str(request.form['username'])
        
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=f"SELECT * FROM users WHERE username = '{Post_Username}'"
        result = conn.execute(text(query)).fetchone()
        conn.close()
        
        if result:
            session['logged_in'] = True
            return redirect('/')  
        else:
            flash('Invalid username. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('Login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        Post_Username = str(request.form['username'])
        Post_Email = str(request.form['email'])
        Post_Interests = str(request.form['interests'])
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        if "@" in Post_Email: #check valid email
            query=f"SELECT max(USERID) FROM users"
            max_userid = conn.execute(text(query)).fetchone()
            new_userid = max_userid[0] + 1
            print(new_userid)
            print(Post_Username)
            print(Post_Email)
            print(Post_Interests)
            try:
                query=f"INSERT INTO users (USERID, username, projectScore, email, interests) VALUES ({new_userid}, '{Post_Username}', 0, '{Post_Email}', '{Post_Interests}')"
                conn.execute(text(query))
                conn.commit()
                return redirect('/login')
            except IntegrityError as e:
                flash('Error signing up. Please try again.', 'error')
            conn.close()
    return render_template('SignUp.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
