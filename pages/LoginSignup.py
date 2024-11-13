from Packages import *

LoginSignup = Blueprint('LoginSignup', __name__, template_folder='templates')


@LoginSignup.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        Post_Username = str(request.form['username'])
        
        conn = engine.connect()
        conn.execute(text("SET SCHEMA 'wf2322'"))
        query=text(f"SELECT * FROM users WHERE username = :username")
        result = conn.execute(query,{'username':Post_Username}).fetchone()
        conn.close()
        
        if result:
            session['logged_in'] = True
            session['user_id'] = result[0]
            return redirect(f'/userprofile/{Post_Username}')  
        else:
            flash('Invalid username. Please try again.', 'error')
            return render_template('Login.html')
    
    return render_template('Login.html')

@LoginSignup.route('/signup', methods=['GET','POST'])
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
            try:
                query=f"INSERT INTO users (USERID, username, projectScore, email, interests) VALUES ({new_userid}, '{Post_Username}', 0, '{Post_Email}', '{Post_Interests}')"
                conn.execute(text(query))
                conn.commit()
                return redirect(url_for('LoginSignup.login'))
            except IntegrityError as e:
                flash('Error signing up. Please try again.', 'error')
            conn.close()
        else:
            flash('Use a proper email address', 'error')
    return render_template('SignUp.html')
