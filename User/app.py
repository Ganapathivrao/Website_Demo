#All these libraries need to be installed on the system using the package manager, PIP on CMD. 
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#This is imported from the data.py in the same folder where firstpro.py exists.
#from data import Articles
#MYSQL packages that operate with MySQL Database
from flask_mysqldb import MySQL, MySQLdb
#wtforms are built in forms that need to be installed on our system using pip and fileds need to included
from wtforms import Form, StringField, TextAreaField,PasswordField, validators, HiddenField
#passlib.hash is used for encrypting our password we want to use. 
from passlib.hash import sha256_crypt
import mysql.connector
#used for styling
from functools import wraps
import os

from wtforms.fields.html5 import EmailField

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Config MySQL
mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'finalpro'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize the app for use with this MySQL class
mysql.init_app(app)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            flash('Unauthorized, You logged in', 'danger')
            return redirect(url_for('register'))
        else:
            return f(*args, *kwargs)
    return wrap

#Home PAge
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/second')
def second():
    return render_template('second.html')

@app.route('/sendEssay')
def send():
    return render_template('sendEssay.html')


#Articles
@app.route('/articles', methods=['GET', 'POST'])
@is_logged_in
def articles():
    if request.method == 'POST':

        searchtext = request.form['searchtext']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM articles WHERE `title` LIKE %s ",['%'+searchtext+'%'])

        articles = cur.fetchall()

        if result >0:
            return render_template('articles.html', articles=articles)
        else:
            msg = 'No articles found'+searchtext
            return render_template('articles.html', msg=msg)

        cur.close()
    else:
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM articles")

        articles = cur.fetchall()

        if result >0:
            return render_template('articles.html', articles=articles)
        else:
            msg = 'No articles found'
            return render_template('articles.html', msg=msg)

        cur.close()



#This route will takes us a single artilce to be dispalyed on the screen. When a user clicks on any of the the link,
#a new page will be displayed. 
""" The article id will be passed here from the data.py file"""
@app.route('/article/<string:id>/')#for single article
def article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template("article.html", article=article)

#A class for registration form 
class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=3, max=50)], render_kw={'autofocus': True})
    username = StringField('Username', [validators.length(min=3, max=25)])
    email = EmailField('Email', [validators.DataRequired(), validators.Email(), validators.length(min=4, max=25)])
    password = PasswordField('Password', [validators.length(min=3)])

"""
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Password do not match")
    ])
    confirm = PasswordField('Confirm Password')
"""
class LoginForm(Form):    # Create Message Form
    username = StringField('Username', [validators.length(min=1)], render_kw={'autofocus': True})


# User Login
@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        # GEt user form
        username = form.username.data
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

        if result > 0:
            # Get stored value
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['name']

            # Compare password
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['uid'] = uid
                session['s_name'] = username
                x = '1'
                cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))
                flash('You are now logged in', 'success')

                return redirect(url_for('home'))

            else:
                flash('Incorrect password', 'danger')
                return render_template('login.html', form=form)

        else:
            flash('Username not found', 'danger')
            # Close connection
            cur.close()
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if 'uid' in session:

        # Create cursor
        cur = mysql.connection.cursor()
        uid = session['uid']
        x = '0'
        cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))
        session.clear()
        flash('You are logged out', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
@not_logged_in
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit cursor
        mysql.connection.commit()

        # Close Connection
        cur.close()

        flash('You are now registered and can login', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


class MessageForm(Form):    # Create Message Form
    body = StringField('', [validators.length(min=1)], render_kw={'autofocus': True})

#Dashboard

@app.route('/dashboard')
@is_logged_in
def dashboard():

    cur = mysql.connection.cursor()
    uid = session['uid']
    result = cur.execute("SELECT * FROM articles  WHERE authorid = %s",[uid])

    articles = cur.fetchall()

    if result >0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)

        cur.close()

#The list of the essays sent for editing will appear here.

@app.route('/sendEssayDashboard')
@is_logged_in
def sendEssayDashboard():

    cur = mysql.connection.cursor()
    uid = session['uid']
    result = cur.execute("SELECT * FROM sendessay  WHERE senderid = %s",[uid])

    articles = cur.fetchall()

    if result >0:
        return render_template('sendEssayDashboard.html', articles=articles)
    else:
        msg = 'No essays found'
        return render_template('sendEssayDashboard.html', msg=msg)

        cur.clos()


#Essay form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=50)])
    summary = StringField('Summary',[validators.Length(min=10, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Essay forms for validating the form for the sake of updating the essays by the users.
class editArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=50)])
    id = HiddenField('id', [validators.Length(min=1, max=50)])
    summary = StringField('Summary',[validators.Length(min=10, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)]) 

#Adding essays done by users here
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        summary = form.summary.data
        body = form.body.data
        uid = session['uid']
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO `articles`(`authorid`,`title`, `summary`, `body`, `author`)  values (%s,%s,%s,%s,%s)", (uid,title,summary, body, session['s_name']))
        
        mysql.connection.commit()

        cur.close()

        flash('Article created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

#UserSendsTheEssays

#The page where the users will add their essays for editing. 
@app.route('/UserSendEssay', methods=['GET', 'POST'])
@is_logged_in
def send_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        summary = form.summary.data
        body = form.body.data
        uid = session['uid']

        cur = mysql.connection.cursor()


        cur.execute("INSERT INTO `sendessay`(`senderid`, `title`, `summary`, `body`,`issent`)  values (%s,%s,%s,%s,%s)", (uid,title,summary, body, 0))
        
        mysql.connection.commit()

        cur.close()

        flash('Essay Sent', 'success')
        return redirect(url_for('sendEssayDashboard'))
    return render_template('UserSendEssay.html', form=form)

#edit Essays by the users themselves 
@app.route('/edit_article', methods=['GET', 'POST'])
@is_logged_in
def edit_article():
    if request.method == 'POST':
        id = request.form['eid']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
        article = cur.fetchone()
        #Get Form
        form = editArticleForm(request.form)
        #populate article form field 
        form.id.data = article['id']
        form.title.data = article['title']
        form.summary.data = article['summary']
        form.body.data = article['body']
        """if request.method == 'POST' and form.validate():
        title = request.form['title']
        summary = request.form['summary']
        body = request.form['body']
    
        cur = mysql.connection.cursor()

        cur.execute("UPDATE edrecievedessay SET `title`=%s, `summary`=%s, `body`=%s WHERE articleid=%s"), (title,summary,body,id)
        
        mysql.connection.commit()

        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('editorRecieveDashboard'))"""
        return render_template('edit_article.html', form=form)
    else:
        return redirect(url_for('dashboard'))

#Updating the articles after the users themselves edit their essays.
@app.route('/update_article', methods=['GET', 'POST'])
@is_logged_in
def update_article():
    if request.method == 'POST':
        #Get Form
        #populate article form field 
        id = request.form['id']
        title = request.form['title']
        summary = request.form['summary']
        body = request.form['body']
        cur = mysql.connection.cursor()

        cur.execute("UPDATE articles SET `title`=%s , `summary`=%s , `body`=%s WHERE id=%s", (title,summary,body,id))
        
        mysql.connection.commit()

        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))

#EssaysRecievedFromAdminAfterEditing

@app.route('/EditedEssayDashboard')
@is_logged_in
def EditedEssayDashboard():

    cur = mysql.connection.cursor()

    result = cur.execute("SELECT finalizedessay.articleid , finalizedessay.title, finalizedessay.recievedate FROM finalizedessay  INNER JOIN edrecievedessay ON edrecievedessay.articleid = finalizedessay.sentarticleid WHERE issent = 1 AND edrecievedessay.senderid = 15")

    articles = cur.fetchall()

    if result >0:
        return render_template('EditedEssayDashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('EditedEssayDashboard.html', msg=msg)

        cur.clos()
@app.route('/OpenEdited', methods=['GET', 'POST'])
def OpenEdited():
    if request.method == 'POST':
        eid = request.form['eid']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM finalizedessay WHERE `articleid` = %s ",[eid])
        articles = cur.fetchone()
        return render_template('OpenEdited.html', articles=articles)
    else:
        return 'hi'

#The users can delete their essays using this route
@app.route('/delete_article/<string:id>', methods=['POST'])
def delete_article(id): 

    cur = mysql.connection.cursor()

    cur.execute("DELETE from articles where id=%s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Article deleted', 'success')
    return redirect(url_for('dashboard'))



#The Chatting environemnt
@app.route('/chatting/<string:id>', methods=['GET', 'POST'])
def chatting(id):
    if 'uid' in session:
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.connection.cursor()
        # lid name
        get_result = cur.execute("SELECT * FROM users  WHERE users.id=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data['name']
            uid = session['uid']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, id, uid))
                # Commit cursor
                mysql.connection.commit()

            # Get users
            cur.execute("SELECT * FROM users WHERE users.user_type = %s", ['editor'])
            users = cur.fetchall()

            # Close Connection
            cur.close()
            return render_template('chat_room.html', users=users, form=form)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

#Chatting Area
@app.route('/chats', methods=['GET', 'POST'])
def chats():
    if 'lid' in session:
        id = session['lid']
        uid = session['uid']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get message
        cur.execute("SELECT * FROM messages WHERE (msg_by=%s AND msg_to=%s) OR (msg_by=%s AND msg_to=%s) "
                    "ORDER BY id ASC", (id, uid, uid, id))
        chats = cur.fetchall()
        # Close Connection
        cur.close()
        return render_template('chats.html', chats=chats,)
    return redirect(url_for('login'))

#pAYMENT
@app.route('/payment')
def pay():
    return render_template('index.html')

if __name__ == '__main__':
    app.secret_key="HeyIam"
    app.run(debug=True)
