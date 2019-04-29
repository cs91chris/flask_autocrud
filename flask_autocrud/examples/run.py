from flask import Flask

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy


class CustomAdminView(ModelView):
    column_display_pk = True
    can_export = True
    can_set_page_size = True
    can_view_details = True
    details_modal = True


def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'more_difficult_string'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///flask_autocrud/examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_ADD_STATUS'] = False

    db = SQLAlchemy(app)
    autocrud = AutoCrud(app, db)
    admin = Admin(app, template_mode='bootstrap3')

    for k, m in autocrud.models.items():
        setattr(CustomAdminView, 'column_searchable_list', m.searchable())
        view = CustomAdminView(m, db.session)
        admin.add_view(view)

    app.run(debug=True)


if __name__ == '__main__':
    main()
