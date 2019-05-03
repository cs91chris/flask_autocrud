from flask import Flask

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import relationship

from flask_autocrud import Model
from flask_autocrud import AutoCrud
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import ForeignKey

db = SQLAlchemy()


class CustomAdminView(ModelView):
    column_display_pk = True
    can_set_page_size = True
    can_view_details = True
    details_modal = True
    can_export = True


class artists(db.Model, Model):
    __tablename__ = "Artist"
    ArtistId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), unique=True, nullable=False)


class albums(db.Model, Model):
    __tablename__ = "Album"
    __description__ = 'my albums table'
    id = db.Column('AlbumId', db.Integer, primary_key=True)
    title = db.Column('Title', db.String(80), unique=True, nullable=False)
    ArtistId = db.Column(db.Integer, ForeignKey("Artist.ArtistId"), nullable=False, comment="column description")
    artist = relationship(artists, backref="albums")


def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'more_difficult_string'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///flask_autocrud/examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_ADD_STATUS'] = False

    db.init_app(app)
    autocrud = AutoCrud(app, db, models=[artists, albums])
    admin = Admin(app)

    for k, m in autocrud.models.items():
        setattr(CustomAdminView, 'column_searchable_list', m.searchable())
        admin.add_view(CustomAdminView(m, db.session))

    app.run(debug=True)


if __name__ == '__main__':
    main()
