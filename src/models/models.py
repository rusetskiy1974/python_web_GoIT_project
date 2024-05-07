import enum
import uuid
from datetime import datetime

from sqlalchemy import Float, String, Integer, ForeignKey, DateTime, func, Column, Boolean, Enum, CheckConstraint, UUID, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(length=320), unique=True, index=True, nullable=False)
    password = Column(String(length=1024), nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    confirmed = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False)
    images = relationship("Image", back_populates="owner")
    comments = relationship("Comment", back_populates="user")

    @hybrid_property
    def fullname(self):
        return self.first_name + " " + self.last_name


class ImageToTag(Base):
    __tablename__ = "image_to_tag"
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE", onupdate="CASCADE"))
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE", onupdate="CASCADE"))


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    size = Column(Integer, nullable=False, index=True)
    path = Column(String(length=255),  index=True)
    created_at = Column(DateTime, default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    count_tags = Column(Integer, default=0, nullable=False)
    owner = relationship("User", back_populates="images", lazy="joined")
    tags = relationship("Tag", secondary="image_to_tag", back_populates="images", lazy="joined")
    comments = relationship("Comment", back_populates="image")
    average_rating = Column(Float, default=0.0)


class Tag(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    images = relationship("Image", secondary="image_to_tag", back_populates="tags", lazy="joined")


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    image_id = Column(Integer, ForeignKey('images.id'))

    user = relationship("User", back_populates="comments")
    image = relationship("Image", back_populates="comments")


class BlackList(Base):
    __tablename__ = 'black_list'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)


class ImageRating(Base):
    __tablename__ = "image_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_id = Column(Integer, ForeignKey("images.id"))
    rating = Column(Integer)

    user = relationship("User", back_populates="ratings")
    image = relationship("Image", back_populates="ratings")