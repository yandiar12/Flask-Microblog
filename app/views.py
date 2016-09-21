from app import app, mongo
import os
import pymongo
from datetime import datetime, timedelta
from pytz import timezone
import pytz
from flask import Flask, render_template, flash, url_for, request, session, redirect, send_from_directory
from flask.ext.pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from math import ceil
from bson.objectid import ObjectId

class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

def timestamp():
	jakarta = timezone('Asia/Jakarta')
	fmt = '%Y-%m-%d %H:%M:%S %Z'
	timestamp = jakarta.localize(datetime.now())
	return timestamp.strftime(fmt)

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']	

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404    

@app.route('/', defaults={'page': 1}, methods=['POST', 'GET'])
@app.route('/page/<int:page>', methods=['POST', 'GET'])
def index(page):
	PER_PAGE = 5
	if 'username' in session:
		if request.method == 'POST':
			try:
				file = request.files['imgInp']
				if file.filename == '':
					filename = ''
				else:
					if file and allowed_file(file.filename):
						filename = secure_filename(file.filename)
						file.save(os.path.join(app.config['UPLOAD_FOLDER'] + 'img-post/', filename))

				post = mongo.db.posts
				post.insert({'body' : request.form['post'], \
					'timestamp' : timestamp(), \
					'author' : session['username'], \
					'image' : filename})
				flash('Your post is now live!', category='success')
				return redirect(url_for('index'))
			except Exception as e:
				return(str(e))
		else:
			count = mongo.db.posts.find().count()
			if count == 0:
				print ("count 0")
				pagination = Pagination(page, PER_PAGE, count)
				return render_template('index.html', posts="", pagination=pagination)

			post = mongo.db.posts

			count = post.find().count()
			if page != 1:
				offset = page * PER_PAGE - PER_PAGE
			else:
				offset = 0
			
			starting_post = post.find().sort('_id', pymongo.DESCENDING)
			last_post = starting_post[offset]['_id']  

			posts = post.find({'_id' : {'$lte' : last_post}}).sort('_id', pymongo.DESCENDING).limit(PER_PAGE)

			pagination = Pagination(page, PER_PAGE, count)
			return render_template('index.html', posts=posts, pagination=pagination)

	return render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
	error = None
	if request.method == 'POST':
		users = mongo.db.users
		login_user = users.find_one({'username' : request.form['username']})

		if login_user:
			# if generate_password_hash(request.form['pass']) == login_user['password']:
			if check_password_hash(login_user['password'], request.form['pass']):
				session['email'] = login_user['email']
				session['username'] = login_user['username']
				session['avatar'] = login_user['avatar']
				session['aboutme'] = login_user['aboutme']
				return redirect(url_for('index'))
			else :
				error = 'Invalid username/password combination'		
				return render_template('login.html', error=error)
	else :
		return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('email', None)
	session.pop('avatar', None)
	session.pop('aboutme', None)
	return redirect(url_for('login'))

@app.route('/register', methods=['POST', 'GET'])
def register():
	if request.method == 'POST':
		users = mongo.db.users
		existing_user = users.find_one({'email' : request.form['email']})

		if existing_user is None:
			password = generate_password_hash(request.form['pass'])
			users.insert({'username' : request.form['username'], 'password' : password, \
				'email' : request.form['email'], 'avatar' : 'default_user.jpg', 'aboutme' : ''})
			usr = users.find_one({'email' : request.form['email']})
			session['username'] = usr['username']
			session['email'] = usr['email']
			session['avatar'] = usr['avatar']
			session['aboutme'] = usr['aboutme']
			flash('Update your profile.', category='info')
			return redirect(url_for('user'))

		error =  'That username already exists!'
		return render_template('register.html', error=error)

	return render_template('register.html')

@app.route('/edit/<id>', methods=['POST','GET'])
def edit(id):
	post = mongo.db.posts
	posts = post.find({'_id' : ObjectId(id)})
	if posts:
		return render_template('post.html', posts=posts)
	flash('Failed : Get data.', category='error')
	return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update():
	if request.method == 'POST':
		post = mongo.db.posts
		data = post.find_one({'_id' : ObjectId(request.form['id'])})
		if data:
			data['body'] = request.form['post']
			data['timestamp'] = timestamp()
			post.save(data)
			flash('Your post was updated.', category='success')
			return redirect(url_for('index'))
		flash('Failed to update post.', category='error')
		return redirect(url_for('edit', id=ObjectId(request.form['id'])))
	return '<h1>404</h1>'

@app.route('/delete/<id>')
def delete(id):
	post = mongo.db.posts
	data = post.find_one({'_id' : ObjectId(id)})
	if data is None:
		flash('Post not found', category='info')
		return redirect(url_for('index'))
	if data['author'] != session['username']:
		flash('You can\'t delete this post', category='info')
		return redirect(url_for('index'))
	post.remove(data)
	flash('Your post has been deleted.', category='success')
	return redirect(url_for('index'))

@app.route('/show/<filename>')
def uploaded_image_post(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'] + 'img-post', filename)		
