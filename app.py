from flask import Flask, request, redirect
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__) # creates a new Flask app
app.debug = True # turns on debugger mode

# link the database to the Flask app's config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# creates a new database for the app
db = SQLAlchemy(app)

# sets up migration (transfers data from one database to another)
migrate = Migrate(app, db)

# displayed on the home page
@app.route('/')
def index():
    return "Hello, world!"

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
