# P3 Item-Catalog
This project is a web based application which can be used to store information about construction projects. The application allows users to create, edit and browse construction projects based on the assigned category. The catalog can store:

- Project Title
- Category
- Client
- Project Value
- Completed Date
- Project Description
- Images / photos showcasing the project

##Requirements
- Python 2.7
- Flask
- SQL Alchemy
- SQLLite
- Internet connection for OAuth2 authentication

##Contents
- database_setup.py - creates the sqllite database using SQL Alchemy
- populate_database.py - populates the database with some sample projects
- application.py - contains flask application
- static (folder) - contains css, javascript and fonts used by bootstrap for styling
- templates (folder) - contains html templates which are render by flask
    - layout-sidebar.html - shared template for pages that display the sidebar
    - layout-form.html - used as shared template for pages with forms
- uploads (folder) - folder where photos are uploaded to. Currently contains images used by sample projects

## Instructions
### Creating the database
To create the database with sqllite run:

        python database_setup.py

### Populate Example Projects
To prepopulate the database with example projects run:

        python populate_database.py

### Running the application
To start the Flask application run:

        python application.py

Then open the web browser and go to:
        
        http://localhost:5000

##TODO
- Add OAuth authentication and only allow registered users to add, delete or edit projects
- Add endpoints such as JSON, RSS etc
- Add voting function to allow registered users to vote on projects