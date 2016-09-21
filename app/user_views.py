import os
from app import app, mongo
from flask import Flask, render_template, flash, url_for, request, session, redirect, send_from_directory
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from .views import allowed_file

@app.route('/user', methods=['POST', 'GET'])
def user():
	if 'username' in session:
		try:
			user = mongo.db.users
			data_user = user.find({'email' : session['email']})
			avatar = os.path.join(app.config['UPLOAD_FOLDER'])
			return render_template('user.html', user=data_user, ava=avatar)
		except Exception as e:
			return(str(e))

	return render_template('login.html')

@app.route('/edituser/<id>', methods=['POST', 'GET'])
def edituser(id):
	if request.method == 'POST':
		users = mongo.db.users
		existing_user = users.find_one({'_id' : ObjectId(id)})

		if existing_user is None:
			flash('User not found.', category='info')
			return redirect(url_for('user'))
		elif existing_user:
			existing_user['username'] = request.form['username']
			existing_user['email'] = request.form['email']
			existing_user['aboutme'] = request.form['aboutme']
			session['username'] = request.form['username']
			session['email'] = request.form['email']
			session['aboutme'] = request.form['aboutme']
			users.save(existing_user)
			flash('Your data has been updated!', category='success')
			return redirect(url_for('user'))
		flash('Something went wrong when updating data.', category='error')
		return redirect(url_for('user'))

	return render_template('register.html')

@app.route('/change-avatar/<id>', methods=['POST'])
def change_avatar(id):
	if request.method == 'POST':
		# Get the name of the uploaded file
		file = request.files['file']
		# Check if the file is not empty
		if file.filename == '':
			flash('No selected file', category='error')
			return redirect(url_for('user'))
		# Check if the file is one of the allowed types/extensions
		if file and allowed_file(file.filename):
			# Make the filename safe, remove unsupported chars
			filename = secure_filename(file.filename)
			# Move the file form the temporal folder to
			# the upload folder we setup
			file.save(os.path.join(app.config['UPLOAD_FOLDER'] + 'img-profile/', filename))
			# Redirect the user to the uploaded_file route, which
			# will basicaly show on the browser the uploaded file
			user = mongo.db.users
			usr = user.find_one({'_id' : ObjectId(id)})
			if usr:
				usr['avatar'] = filename
				session['avatar'] = filename
				user.save(usr)
				flash('Your avatar has been changed.', category='success')
				return redirect(url_for('user'))
			flash('Something went wrong !!', category='error')
			return redirect(url_for('user'))

	return render_template('post.html')

@app.route('/uploads/<filename>')
def uploaded_image_profile(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'] + 'img-profile', filename)	
    