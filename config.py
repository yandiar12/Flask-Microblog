# Initialize the Database name
MONGO_DBNAME = 'microblog'
# Initialize the Database URI
MONGO_URI = 'mongodb://superadmin:1234@localhost/' + MONGO_DBNAME
# This is the path to the upload directory
UPLOAD_FOLDER = '/flask/flask-microblog/app/uploads/'
# These are the extension that we are accepting to be uploaded
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])