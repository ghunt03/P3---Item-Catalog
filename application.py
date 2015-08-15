import random, string
import os
import datetime
from flask import Flask, render_template, request, flash, redirect, url_for
from flask import session as login_session, send_from_directory
from werkzeug import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Project

app = Flask(__name__)


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

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
    return render_template("home.html", 
        categories = categories, 
        latest_projects = items)


@app.route('/catalog/category/<int:category_id>/')
def catalogCategory(category_id):
    """Route for category page / category view.

    Renders the template for the category and lists the items within the 
    category.
    
    Args:
        category_id: integer for the selected category
    """
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Project).filter_by(category_id = category_id)
    return render_template(
        "category.html", 
        category=category, 
        projects = items,
        categories=categories)


@app.route('/catalog/item/<int:item_id>/')
def catalogItem(item_id):
    """Route for item page / item view.

    Renders the template for the item / project. includes the list of images 
    for the carousel
    
    Args:
        item_id: integer for the selected item
    """
    item = session.query(Project).filter_by(id = item_id).one()
    images = getImages(item_id)
    category = session.query(Category).filter_by(id = item.category_id).one()
    return render_template("item.html", 
        item = item, 
        categories = categories,
        category = category,
        images = images)

    


@app.route('/catalog/showImage/<int:item_id>/<string:filename>')
def showImage(item_id, filename):
    """Route to display the selected image and return to the browser
    
    Args:
        item_id: integer used for selecting the correct sub folder
        filename: string for the name of the image file
    """
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    return send_from_directory(folderPath,
                               filename)

@app.route('/catalog/showthumbnail/<int:item_id>')
def showThumbnail(item_id):
    """Route to display the thumbnail for the selected item
    
    Args:
        item_id: integer used for selecting the correct sub folder
    """
    folderPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    filename = getThumbnail(item_id)
    return send_from_directory(folderPath,
                               filename)

 
@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def addCatalogItem():
    """Route to either render the create a new item page or POST method 
    for saving the new item
    """
    if request.method == 'POST':
        # POST method for saving new item
        # Converts date from EN-AU to Python date
        completed_date = datetime.datetime.strptime(
            request.form['completed_date'],"%d/%m/%Y").date()
        # details of new item
        newItem = Project(
            project_title = request.form['project_title'],
            client = request.form['client'],
            project_value = request.form['project_value'],
            completed_date = completed_date,
            description = request.form['description'],
            category_id = request.form['category']
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
    
    # get item here so that code to find item only needs to be called once
    item = session.query(Project).filter_by(id=item_id).one()
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
        return render_template('deleteItem.html',item=item)
    
@app.route('/catalog/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editCatalogItem(item_id):
    """Route to GET edit page or POST method
    
    Args:
        item_id: integer for id of item to update
    """
    item = session.query(Project).filter_by(id=item_id).one()
    if request.method == 'POST':
        # POST method for saving changes to item
        item.project_title = request.form['project_title']
        item.client = request.form['client']
        item.project_value = request.form['project_value']
        item.completed_date = datetime.datetime.strptime(
            request.form['completed_date'],"%d/%m/%Y").date()
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
        return render_template('editItem.html', 
            item = item, 
            categories = categories)
    
  
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
                #elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception, e:
                print e

def uploadImages(item_id, files):
    """Uploads files to sub folder on server
    
    Args:
        item_id: id / name of subfolder for uploads
        files: list of files to upload to server
    """
    uploadPath = app.config['UPLOAD_FOLDER'] + str(item_id)
    #checks if folder exists if not create the sub folder
    if not os.path.exists(uploadPath):
        os.makedirs(uploadPath)
    """Loop through files and check if they are an allowed file type
    TODO: see if validation of file type can be done on client side rather than
    on the server side
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
    app.run(host = '0.0.0.0', port = 5000)
