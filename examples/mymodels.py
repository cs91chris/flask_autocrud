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


class artists(db.Model, Model):
    __tablename__ = "Artist"
    __description__ = 'artists'
    id = db.Column('ArtistId', db.Integer, primary_key=True, comment='primarykey')
    name = db.Column('Name', db.String(80), unique=True, nullable=False)


class albums(db.Model, Model):
    __tablename__ = "Album"
    __description__ = 'my albums table'
    id = db.Column('AlbumId', db.Integer, primary_key=True)
    title = db.Column('Title', db.String(80), unique=True, nullable=False, comment="column description")
    artist_id = db.Column('ArtistId', db.Integer, ForeignKey("Artist.ArtistId"), nullable=False)
    # NOTE: it must be the same name of related class otherwise there will be unknown side effects
    # This will change in future versions
    artists = relationship(artists, backref="albums")


def main():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'more_difficult_string'
    app.config['RB_DEFAULT_ACCEPTABLE_MIMETYPES'] = ['application/json', 'application/xml']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite+pysqlite:///examples/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    admin = Admin(app)
    autocrud = AutoCrud(app, db, models=[artists, albums])

    for k, m in autocrud.models.items():
        setattr(CustomAdminView, 'column_searchable_list', m.searchable())
        admin.add_view(CustomAdminView(m, db.session))

    app.run(debug=True)


if __name__ == '__main__':
    main()
