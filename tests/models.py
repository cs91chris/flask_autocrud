from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from flask_autocrud import Model
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class artists(db.Model, Model):
    __tablename__ = "Artist"
    __description__ = "artists"
    id = db.Column('ArtistId', db.Integer, primary_key=True, comment='primarykey')
    name = db.Column('Name', db.String(80), unique=True, nullable=False)


class albums(db.Model, Model):
    __tablename__ = "Album"
    __hidden__ = "title"
    __url__ = '/myalbum'
    id = db.Column('AlbumId', db.Integer, primary_key=True)
    title = db.Column('Title', db.String(80), unique=True, nullable=False)
    artist_id = db.Column('ArtistId', db.Integer, ForeignKey("Artist.ArtistId"), nullable=False)
    artists = relationship(artists, backref="albums")
