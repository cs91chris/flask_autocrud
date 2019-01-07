from flask import Flask

from flask_admin import Admin
from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///flask_autocrud/examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_ADD_STATUS'] = False

    db = SQLAlchemy(app)
    admin = Admin(app, base_template='layout.html', template_mode='bootstrap3')
    AutoCrud(db, app, admin)

    app.run(debug=True)


if __name__ == '__main__':
    main()
