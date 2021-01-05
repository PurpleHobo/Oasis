#############imports, if you remove any of these it will break OwO
import threading #WillowBot
from flask import Flask, render_template, url_for, request, redirect, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from random import randint
from hashlib import sha256, pbkdf2_hmac
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField
from wtforms.validators import InputRequired, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from extra import Salty, Timer    #this shit started getting too long so there is now a submodule, enjoy!
import os
###########

###########initialisers 
app = Flask(__name__) 
Bootstrap(app)                 #initialieses bootstrap
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'        #initialises and points to database
app.config['SQLALCHEMY_BINDS'] = {'two' : 'sqlite:///hash.db'}
app.config['SECRET_KEY'] = 'stoplookingcuntthisissecret'
db = SQLAlchemy(app)
login_manager.login_view = 'login'
##########

#############classes
class LoginForm(FlaskForm): #for login fields 
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('Remember Me')

class RegisterForm(FlaskForm): #for signup page
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4, max=80)])
    checkpassword = PasswordField('Check Password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('Remember Me')
    
class WillowControl(FlaskForm):
    killWillow = BooleanField('Kill Willow')
    startWillow = BooleanField('Spawn Willow')

class Todo(db.Model): #for task page
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    dueDate = db.Column(db.DateTime, default=datetime.utcnow)
    date_created = db.Column(db.DateTime, default=datetime.utcnow) #takes current time from datetime module

    def __repr__(self):
        return f'Task: {self.id}'

class Storage(UserMixin, db.Model): #for storing passwords, i named it terribly but can't be bothered to rewrite
    __bind_key__ = 'two'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    Hash = db.Column(db.String(200), nullable=False)
#################

##########functions
@login_manager.user_loader
def load_user(user_id):   #i actually dont know what this does jej, but it crashes if i delete kek
    return Storage.query.get(int(user_id))

    def __repr__(self):
        return f'Task: {self.id}'

@app.route('/') #Defines index route
@login_required
def index():
    return render_template('index.html', name=current_user.username) #displays index.html

@app.route('/api/', methods=['POST', 'GET']) #Defines api route if i am ever feeling frisky
@Timer
def api(): #for future use if i am bored
    if request.method == "POST":
        someJSON = request.get_json()
        return jsonify({"you sent" : someJSON}), 201
    else:return jsonify({"about" : "Hello World!"})

@app.route('/login/', methods=['POST', 'GET']) #defines login route
def login():
    form = LoginForm() 

    if form.validate_on_submit(): #checks if class information has been filled 
        user = Storage.query.filter_by(username=form.username.data).first() #takes first username that matches as they should be unique
        password = Salty(form.username.data, form.password.data) #a shitty hashing system, still doubt you can crack it doe

        if user: #if user exists it will check password and login the user

            if user.Hash == password:
                login_user(user, remember=form.remember.data)
                return redirect('/')

            else:return redirect('/login/')

    return render_template('login.html', form=form)

@app.route('/signup/', methods=['POST', 'GET']) #defines signup route
def signup():
    form = RegisterForm()
    if form.password.data != form.checkpassword.data: #makes sure both password and checkpassword fields are correct to avoid errors
        return redirect('/signup/')

    password = Salty(form.username.data, form.password.data) #a shitty hashing system, still doubt you can crack it doe
    if form.validate_on_submit():
        newUser = Storage(username=form.username.data, Hash=password) #makes a new user in the class and makes it a variable

        try:
            db.session.add(newUser)
            db.session.commit() #add and commit to db
            user = Storage.query.filter_by(username=form.username.data).first()
            login_user(user, remember=form.remember.data)
            return redirect('/')

        except Exception as e: return ('There was an error in signup(): ' + str(e))

    return render_template('signup.html', form=form)

@app.route('/portfolio/') #for logging endevours
def portfolio():
    return render_template('portfolio.html')

@app.route('/about/') #for about page
@login_required
def about():
    return render_template('about.html')

@app.route('/goals/') #for about page
@login_required
def goals():
    if current_user.username != 'purple':
        return redirect('/')
    else:return render_template('goals.html')

@app.route('/task/', methods=['POST', 'GET']) #this is just a basic decorater
@login_required
@Timer
def task():
    if current_user.username != 'purple':
        return redirect('/')

    if request.method == 'POST':
        task_content = request.form['content'] #pulls content from the add text feild
        task_content_date_HTML = request.form['dateTask']
        task_content_date_HTML = task_content_date_HTML[2:16] + ":00"

        if len(task_content_date_HTML) != 17:
            return redirect('/task/') #redirects back to task page

        else:
            task_content_date_Python = datetime.strptime(task_content_date_HTML, '%y-%m-%dT%H:%M:%S') #html and python datetime are incompatable so this is a conversion
            new_task = Todo(content=task_content, dueDate=task_content_date_Python) 

            try: #to add a task
                db.session.add(new_task)
                db.session.commit()
                return redirect('/task/')
        
            except Exception as e: return ('There was an error in task(): ' + str(e))
            
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('tasks.html', tasks=tasks)

@app.route('/task/delete/<int:id>') #route for deleting tasks
@login_required
@Timer
def delete(id):
    task_to_delete = Todo.query.get_or_404(id) #finds task to del
    
    try:
        db.session.delete(task_to_delete) #attempts to del task
        db.session.commit() #pushs if task is successfully del
        return redirect('/task/') #redirects back to task page

    except:
        return 'issue with Delete()'

@app.route('/task/update/<int:id>', methods=['GET', 'POST'])
@login_required
@Timer
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']     #finds info method 'post' at index 'content'
        task_content_date_HTML = request.form['dateTask']
        task_content_date_HTML = task_content_date_HTML[2:16] + ":00"

        if len(task_content_date_HTML) != 17:
            return redirect('/task/') #redirects back to task page

        else:
            task_content_date_Python = datetime.strptime(task_content_date_HTML, '%y-%m-%dT%H:%M:%S')
            task.dueDate = task_content_date_Python

            try:
                db.session.commit() #commits to db
                return redirect('/task/') #now that it is updated it redirects back to task page

            except Exception as e: return ('There was an error in update(): ' + str(e))

    else:
        return render_template('update.html', task=task)

@app.route('/logout/') #logs out, no page or anything as i cant be bothered 
@login_required
def logout():
    logout_user()
    return redirect('/')

#def botThread():
#    WillowBot.client.run('NzAyNDA4Nzg5NDAzNjMxNjQ3.Xp_nuQ.R1snkn0y0D7_x9tHnweKHmAOdGI')
####################

#############executable code
print("Beep boop, we are online!") #played at startup

if __name__ == "__main__": #checks that the module is not being imported and then starts the webserver
    #threadOne = threading.Thread(target=botThread) #hash out when working on webserver
    #threadOne.start() #also hash this
    #app.run(debug=False) #it runs twice if true and opens my bot twice which is obnoxious
    app.run(host='0.0.0.0', debug=False) #it runs twice if true and opens my bot twice which is obnoxious

print("Beeb boop, see you later lads!") #plays at shutdown
###############

