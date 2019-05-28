from flask import Flask

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy


class CustomAdminView(ModelView):
    can_export = True
    details_modal = True
    column_display_pk = True
    can_set_page_size = True
    can_view_details = True


def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'more_difficult_string'
    app.config['FLASK_ADMIN_SWATCH'] = 'cosmo'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    admin = Admin(app)
    db = SQLAlchemy(app)
    autocrud = AutoCrud(app, db)

    for k, m in autocrud.models.items():
        setattr(CustomAdminView, 'column_searchable_list', m.searchable())
        admin.add_view(CustomAdminView(m, db.session))

    app.run(debug=True)


if __name__ == '__main__':
    main()
