from flask import Flask

from flask_admin import Admin
from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView


class CustomAdminView(ModelView):
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'
    column_display_pk = True


def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'more_difficult_string'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///flask_autocrud/examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_ADD_STATUS'] = False

    autocrud = AutoCrud()
    db = SQLAlchemy(app)
    autocrud.init_app(app, db)

    admin = Admin(app, base_template='layout.html', template_mode='bootstrap3')

    for k, m in autocrud.models.items():
        admin.add_view(CustomAdminView(m, db.session))

    app.run(debug=True)


if __name__ == '__main__':
    main()
