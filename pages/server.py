from flask import Flask, render_template
from Packages import *
from LoginSignup import LoginSignup
from UserProfile import UserProfile
from ProjectPage import project
from projectcalendar import projectcalendar
from Search import Search
app = Flask(__name__)
app.register_blueprint(LoginSignup)
app.register_blueprint(UserProfile)
app.register_blueprint(project)
app.register_blueprint(projectcalendar) 
app.register_blueprint(Search) 
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=8111)