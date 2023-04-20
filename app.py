from flask import Flask, request, redirect, url_for, render_template, flash
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime
from webforms import *


# App
app = Flask(__name__)

# database
app.config['SECRET_KEY'] = 'ABCDabcd123'
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
migrate = Migrate(app, db)
# flask db init
# flask db migrate -m "Initial"
# flask db upgrade

# Custom Secusity
csrf = CSRFProtect(app)
     

# Model

class Users(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), nullable=False, unique=True)
	name = db.Column(db.String(200), nullable=True)
	email = db.Column(db.String(120), nullable=False, unique=True)
	about_author = db.Column(db.Text(), nullable=True)
	date_added = db.Column(db.DateTime, default=datetime.utcnow)
	profile_pic = db.Column(db.String(), nullable=True)
	password_hash = db.Column(db.String(128))
	# posts = db.relationship('Posts', backref='poster')

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute!')
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return self.username

class Blog_Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(50))
    content = db.Column(db.String(200))
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, slug, content):
        self.title =title
        self.slug = slug
        self.content = content

    def __str__(self):
        return self.name

with app.app_context():
    db.create_all()




@app.route('/')
def home():
    return render_template('base.html')


# User Management

@app.route('/user_register', methods=['GET', 'POST'])
def register():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        pass1 = form.password_hash.data
        pass2 = form.password_hash2.data
        model_user = Users.query.filter_by(username=form.username.data).first()
        model_email = Users.query.filter_by(email=email).first()
        if pass1 == pass2:
            hashed_pw = generate_password_hash(pass1, "sha256")
            if model_user is None and model_email is None:
                user = Users(username=username, email=email, password_hash=hashed_pw)
                db.session.add(user)
                db.session.commit()
                return redirect('/user_list')
            else:
                flash('Username or Email is already exist')
                return render_template("register.html", form=form)
        else:
            flash('Password must be same')
            return render_template("register.html", form=form)
    else:
        return render_template("register.html", form=form)


@app.route('/user_list')
def all_users():
    users_list = Users.query.order_by(Users.id)
    return render_template('user_list.html', users_list=users_list)
    
@app.route('/user_details/<int:id>')
def user_details(id):
    users_details = Users.query.get_or_404(id)
    return render_template('users_details.html', users_details=users_details)

@app.route('/user_delete/<int:id>')
def user_delete(id):
    user_to_delete = Users.query.get_or_404(id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('User Deleted')
    return redirect('/user_list')



# Post Management

@app.route('/post_create', methods=['GET', 'POST'])
def post_create():
    form = PostForm()
    if  form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        slug = form.slug.data
        if title != None and content != None and slug != None:
            obj = Blog_Post(title=title, content=content, slug=slug)
            db.session.add(obj)
            db.session.commit()
            return redirect('/post_list')
        else:
            return render_template('post_create.html', form=form)

    else:
        return render_template('post_create.html', form=form)



@app.route('/post_list')
def post_list():
    post_data = Blog_Post.query.order_by(Blog_Post.id)
    return render_template('post_list.html', post_data=post_data)


@app.route('/post_edit/<int:id>', methods=['GET', 'POST'])
def post_edit(id):
    post_to_edit = Blog_Post.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        if form.title.data != None and form.slug.data != None and form.content.data != None:
            post_to_edit.title = form.title.data
            post_to_edit.slug = form.slug.data
            post_to_edit.content = form.content.data
            db.session.add(post_to_edit)
            db.session.commit()
            return redirect(url_for('post_details', id=post_to_edit.id))
        else:
            flash('Please Input all data')
            return render_template('post_edit.html', form=form)
    else:
        form.title.data = post_to_edit.title
        form.slug.data = post_to_edit.slug
        form.content.data = post_to_edit.content
        return render_template('post_edit.html', form=form, post_to_edit=post_to_edit)



@app.route('/post_details/<int:id>')
def post_details(id):
    posts_details = Blog_Post.query.get_or_404(id)
    return render_template('post_details.html', posts_details=posts_details)


@app.route('/post_delete/<int:id>')
def post_delete(id):
    post_to_delete = Blog_Post.query.get_or_404(id)
    db.session.delete(post_to_delete)
    db.session.commit()
    flash('Post Deleted')
    return redirect('/post_list')




@app.route('/post_api')
def api():
     post_data = Blog_Post.query.order_by(Blog_Post.id)
     post_list = []
     for post in post_data:
          post_dict = {}
          post_dict['id'] = post.id
          post_dict['title'] = post.title
          post_dict['content'] = post.content
          post_list.append(post_dict)
     return {'post_data':post_list}



@app.route('/search', methods = ['POST', 'GET'])
def search():
    search_text = ''
    if request.method == 'POST' and request.form['search_input'] != '':
        search_text = request.form['search_input']
        Post_query = Blog_Post.query.filter(Blog_Post.name.like('%'+ search_text + '%'))
        Post_query = Blog_Post.order_by(Blog_Post.name).all()
        return render_template('search.html', search_text = search_text, Post_query = Post_query)
    else:
        return redirect(request)
    






@app.route("/example/<example_data>")
def example(example_data):
    return render_template('example.html', example_data=example_data)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
else:
    app.config.update(
        SERVER_NAME='snip.snip.com:80',
        APPLICATION_ROOT='/',
    )



# @app.route('/post_create', methods=['GET', 'POST'])
# def post_create():
#     name = ''
#     roll = ''
#     address = ''
#     if request.method == 'POST':
#         name = request.form['name']
#         roll = request.form['roll']
#         address = request.form['address']
#         if request.form['name'] != '' and request.form['roll'] != '' and request.form['address'] !='':
#             obj = Blog_Post(name=name, roll=roll, address=address)
#             db.session.add(obj)
#             db.session.commit()
#             return redirect('/post_list')
#         else:
#             return render_template('post_create.html', name=name, roll=roll, address=address)

#     else:
#         return render_template('post_create.html')