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
- Vagrant (version 1.7.4)
- VirtualBox (version 5)
- Python (version 2.7)
- Flask (version 0.10.1)
- Flask SeaSurf (0.2.0)
- SQL Alchemy (version 0.8.4)
- SQLLite
- Internet connection for OAuth2 authentication

##Contents
- .vagrant (folder) - containing components for running vagrant envrionment
- pg_config.sh - script for installing components in environment
- Vagrantfile - configuration file for vagrant
- Catalog (folder) - contains code files for application
    - database_setup.py - creates the sqllite database using SQL Alchemy
    - populate_database.py - populates the database with some sample projects
    - sample_data (folder) - contains csv files used by populate_database.py
    - application.py - contains flask application
    - static (folder) - contains css, javascript and fonts used by bootstrap for styling
    - templates (folder) - contains html templates which are render by flask
        - layout-sidebar.html - shared template for pages that display the sidebar
        - layout-form.html - used as shared template for pages with forms
    - uploads (folder) - folder where photos are uploaded to. Currently contains images used by sample projects


## Instructions
### Starting Virtual Machine
1. Browse to downloaded folder (folder which contains vagrantfile)
2. Run ```vagrant up``` (this will start the virtual machine)
3. To connect to the virtual machine run ```vagrant ssh```
4. Once you have connected to the terminal interface, run the following command to access the catalog project
 ``` cd /vagrant/catalog```


### Creating the database
To create the database with sqllite run:

```python database_setup.py```

### Populate Example Projects
To prepopulate the database with example projects run:

``` python populate_database.py```

### Running the application
To start the Flask application run:

 ```python application.py```

Then open the web browser and go to:
        
        http://localhost:5000
