import random
import string
import os
import datetime
from flask import Flask, render_template, request, flash, redirect, url_for
from flask import session as login_session, send_from_directory, make_response
from werkzeug import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Project, User

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests


app = Flask(__name__)


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

app.config['CLIENT_ID'] = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = session.query(Category).order_by(Category.name)


@app.route('/')
@app.route('/catalog/')
def home():
    """Route for home page / default view.

    Renders the template for the home page, displaying the categories and
    the last 5 projects.

    """
    items = session.query(Project).order_by(Project.id.desc()).limit(5)
    return render_template(
        "home.html",
        categories=categories,
        latest_projects=items)


def createUser(login_session):
    """Creates a new user based on details retrieved during login.
    """
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Gets user based on user_id
    args:
        user_id: integer containing user_id
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Gets user_id based on email address
    args:
        email: string containing email address
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/login')
def showLogin():
    """Route for rendering the login screen and passing the state token
    """
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Connection and validation method for logging in using Google+
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets(
            'client_secrets_google.json', 
            scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the \
            authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']
    # Verify user id's match
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user_id doesn't match \
            given user ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # verify that the access token is valid for this app
    if result['issued_to'] != app.config['CLIENT_ID']:
        response = make_response(json.dumps("Token's client id doesn't \
            match apps"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # store the access token in the session for later use
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = "google"

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    flash("you are now logged in as %s" % login_session['username'])
    return "success"


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Connection and validation method for logging in using Facebook+
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    app_id = json.loads(open('client_secrets_facebook.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('client_secrets_facebook.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (  # noqa
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    """ The token must be stored in the login_session in order to properly
    logout, let's strip out the information before the equals sign in our
    token
    """
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("Now logged in as %s" % login_session['username'])
    return "success"


def gdisconnect():
    """Disconnect method for logging out of Google+
    """
    # Only disconnect a connected user.
    credentials = login_session['credentials']
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def fbdisconnect():
    """Disconnect method for logging out of Facebook
    """
    fbid = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        fbid,
        access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    """Logout method for destroying session based on the provider used"""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
    else:
        flash("You were not logged in")
    return redirect(url_for('home'))


@app.route('/catalog/category/<int:category_id>/')
def catalogCategory(category_id):
    """Route for category page / category view.

    Renders the template for the category and lists the items within the
    category.

    Args:
        category_id: integer for the selected category
    """
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Project).filter_by(category_id=category_id)
    return render_template(
        "category.html",
        category=category,
        projects=items,
        categories=categories)


@app.route('/catalog/item/<int:item_id>/')
def catalogItem(item_id):
    """Route for item page / item view.

    Renders the template for the item / project. includes the list of images
    for the carousel

    Args:
        item_id: integer for the selected item
    """
    item = session.query(Project).filter_by(id=item_id).one()
    images = getImages(item_id)
    category = session.query(Category).filter_by(id=item.category_id).one()
    return render_template(
        "item.html",
        item=item,
        categories=categories,
        category=category,
        images=images)


@app.route('/catalog/showImage/<int:item_id>/<string:filename>')
def showImage(item_id, filename):
    """Route to display the selected image and return to the browser

    Args:
        item_id: integer used for selecting the correct sub folder
        filename: string for the name of the image file
    """
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    return send_from_directory(
        folderPath,
        filename)


@app.route('/catalog/showthumbnail/<int:item_id>')
def showThumbnail(item_id):
    """Route to display the thumbnail for the selected item

    Args:
        item_id: integer used for selecting the correct sub folder
    """
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    filename = getThumbnail(item_id)
    return send_from_directory(
        folderPath,
        filename)


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def addCatalogItem():
    """Route to either render the create a new item page or POST method
    for saving the new item
    """
    if 'user_id' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # POST method for saving new item
        # Converts date from EN-AU to Python date
        completed_date = datetime.datetime.strptime(
            request.form['completed_date'], "%d/%m/%Y").date()
        # details of new item
        newItem = Project(
            project_title=request.form['project_title'],
            client=request.form['client'],
            project_value=request.form['project_value'],
            completed_date=completed_date,
            description=request.form['description'],
            category_id=request.form['category'],
            user_id=login_session['user_id']
        )
        session.add(newItem)
        session.commit()

        # call to upload function
        uploadImages(newItem.id, request.files.getlist("files[]"))
        # store flash message and redirect to home page
        flash("Project '%s' added" % newItem.project_title)
        return redirect(url_for('home'))
    else:
        # GET method which renders the new item page
        return render_template('newItem.html', categories=categories)


@app.route('/catalog/item/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteCatalogItem(item_id):
    """Route to GET delete page or POST method

    Args:
        item_id: integer for id of item to delete
    """
    if 'user_id' not in login_session:
        return redirect('/login')
    # get item here so that code to find item only needs to be called once
    item = session.query(Project).filter_by(id=item_id).one()
    if (item.user_id != login_session["user_id"]):
        flash("You can only delete projects that you created")
        return redirect(url_for('home'))
    if request.method == 'POST':
        # POST method to delete item
        session.delete(item)
        session.commit()
        # call to function to remove the images from the item upload folder
        removeImages(item_id)
        # store flash message and redirect to home page
        flash("Project '%s' has been deleted" % item.project_title)
        return redirect(url_for('home'))
    else:
        # GET method which renders the delete item confirmation page
        return render_template('deleteItem.html', item=item)


@app.route('/catalog/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editCatalogItem(item_id):
    """Route to GET edit page or POST method

    Args:
        item_id: integer for id of item to update
    """
    if 'user_id' not in login_session:
        return redirect('/login')

    item = session.query(Project).filter_by(id=item_id).one()
    if item.user_id != login_session["user_id"]:
        flash("You can only edit projects that you created")
        return redirect(url_for('home'))
    if request.method == 'POST':
        # POST method for saving changes to item
        item.project_title = request.form['project_title']
        item.client = request.form['client']
        item.project_value = request.form['project_value']
        item.completed_date = datetime.datetime.strptime(
            request.form['completed_date'], "%d/%m/%Y").date()
        item.description = request.form['description']
        item.category_id = request.form['category']
        session.add(item)
        session.commit()

        if (request.form['photooption'] == "replace"):
            """If the option to replace the photos is selected then the
            previous photos will be deleted and the new ones uploaded
            """
            # if the option to replace the images is selected then
            removeImages(item_id)
            uploadImages(item_id, request.files.getlist("files[]"))
        flash("Project '%s' has been updated" % item.project_title)
        return redirect(url_for('home'))
    else:
        return render_template(
            'editItem.html',
            item=item,
            categories=categories)


def removeImages(item_id):
    """Deletes images from sub folder in the UPLOADS directory

    Args:
        item_id: integer for id of item to delete
    """
    imagePath = app.config['UPLOAD_FOLDER'] + str(item_id)
    if os.path.exists(imagePath):
        for file in os.listdir(imagePath):
            file_path = os.path.join(imagePath, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception, e:
                print e


def uploadImages(item_id, files):
    """Uploads files to sub folder on server

    Args:
        item_id: id / name of subfolder for uploads
        files: list of files to upload to server
    """
    uploadPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    # checks if folder exists if not create the sub folder
    if not os.path.exists(uploadPath):
        os.makedirs(uploadPath)
    """Loop through files and check if they are an allowed file type
    TODO: see if validation of file type can be done on client side rather
    than on the server side
    """
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(uploadPath, filename))


def allowed_file(filename):
    # For a given file, return whether it's an allowed type or not
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def getImages(item_id):
    """Return a list of files in the folder linked to the item_id

    Args:
        item_id: id / name of subfolder for uploads
    """
    files = []
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    if os.path.exists(folderPath):
        images = os.listdir(folderPath)
        for image in images:
            if "thumbnail" not in image and allowed_file(image):
                files.append(image)
    return files


def getThumbnail(item_id):
    """Returns the name of the file to be displayed as the thumbnail

    If a file does not contain the text 'thumbnail' the first file in the
    directory will be used

    Args:
        item_id: id / name of subfolder for uploads
    """
    files = []
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    images = os.listdir(folderPath)
    filename = ""
    for image in images:
        if "thumbnail" in image and allowed_file(image):
            filename = image
    if filename == "":
        filename = getImages(item_id)[0]
    return filename


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)
