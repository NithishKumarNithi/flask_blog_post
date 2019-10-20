from flask import Flask , render_template , flash  ,request , redirect , url_for , g ,session
import sqlite3
app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev'
app.config['DATABASE_PATH'] = 'myfpb.db'

# db setup

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE_PATH'],
            detect_types = sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db',None)
    if 'db' is not None:
        db.close()

def init_db():
    db = get_db()
    
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    
# routing setup

@app.route('/')
def home():
    if session.get('logged-in'):
        session.clear()
        return redirect(url_for('home'))
    else:
        session.clear()
        db = get_db()
        posts = db.execute(
            'SELECT myfpbl.username, myfpbp.title, myfpbp.post'
            ' FROM myfpbp JOIN myfpbl ON myfpbl.id=myfpbp.author_id'
            ' ORDER BY myfpbl.username ASC'
        ).fetchall()
        
        return render_template('home.html',title='Home',posts=posts)

@app.route('/login', methods=('GET','POST'))
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = request.form['password']

        if not username and not password:
            error = "Please enter the username and password"
        elif not username or not password:
            error = "Enter the valid credentials"
        else:
            get_user = db.execute(
                'SELECT * FROM myfpbl WHERE username = ?',(username,)
            ).fetchone()


            db.commit()

            if get_user != None :
                session['username'] = username
                session['user-id'] = get_user['id']
                session['logged-in'] = True
                session['sign-in'] = False
                return redirect(url_for('users'))
            else:
                error = "User Not found"

    if error != None:
        flash(error)
    return render_template('login.html',title='Login')

@app.route('/sign-in',methods=('GET','POST'))
def sign():
    error = None
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = request.form['password']

        if not username and not password:
            error = "Enter the valid credentials"
        elif not username or not password:
            error = "Please enter the relative fields"
        else:
            post_exits = db.execute(
                'SELECT * FROM myfpbl WHERE username = ?',(username,)
            ).fetchone()

            if post_exits:
                error = "Username Already exists"
            else:
                db.execute('INSERT into myfpbl (username,password) VALUES(?,?)',
                    (username,password)
                )
                db.commit()
                session['sign-in'] = True
                return redirect(url_for('login'))
    if error != None:
        flash(error)
    return render_template('signin.html',title="Sign-In")

@app.route('/users-posts')
def users():
    if session.get('logged-in'):
        db = get_db()

        userId = session['user-id']

        posts = db.execute(
            'SELECT myfpbl.username, myfpbp.id, myfpbp.title, myfpbp.post '
            ' FROM myfpbp JOIN myfpbl ON myfpbl.id = myfpbp.author_id'
            ' WHERE myfpbl.id = ?',(userId,)
            
        ).fetchall()

        db.commit()

        return render_template('users.html',title='User',posts=posts,username=session['username'])
    else:
        return redirect(url_for('home'))


@app.route('/add-post', methods=('GET','POST'))
def post():
    if session.get('logged-in'):
        if request.method == 'POST':
            post_title = request.form['title']
            post_msg   = request.form['post-content']
            username = session['username']

            db = get_db()
            userId = session['user-id'] 

            db.execute(
                'INSERT INTO myfpbp (title, post, author_id) VALUES(?,?,?)',
                (post_title,post_msg,userId)
            )
            
            db.commit()
            return redirect(url_for('users'))

        return render_template('post.html',title='Post')
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# delete post
@app.route('/delete/<id>')
def delete(id):
    if session.get('logged-in'):
        db = get_db()
        db.execute(
            'DELETE FROM myfpbp WHERE id = ?',(id,)
        )
        db.commit()
        return redirect(url_for('users'))
    else:
        return redirect(url_for('home'))


#edit post
@app.route('/edit/<id>',methods=('GET','POST'))
def edit(id):
    db = get_db()
    if session.get('logged-in'):
        if request.method == 'POST':
            title = request.form['title']
            post  = request.form['post-content']
            db.execute(
                'UPDATE myfpbp SET title = ? ,post = ? WHERE id = ? ',(title,post,id,)
            )
            db.commit()

            return redirect(url_for('users'))

        
        posts = db.execute(
            'SELECT * FROM myfpbp WHERE id = ?',(id,)
        ).fetchone()

        return render_template('edit.html',title='Edit',posts=posts)
    else:
        return redirect(url_for('home'))









