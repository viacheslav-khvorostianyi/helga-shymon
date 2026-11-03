from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import event
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def utcnow():
    return datetime.now(timezone.utc)


recipe_tags = db.Table(
    "recipe_tags",
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipe.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    recipes = db.relationship("Recipe", back_populates="category")


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    summary = db.Column(db.Text, default="")
    ingredients = db.Column(db.Text, default="")
    instructions = db.Column(db.Text, default="")
    image_filename = db.Column(db.String(100))
    # Lowercased copy of searchable text: SQLite's LIKE is only case-insensitive for ASCII
    search_text = db.Column(db.Text, default="")
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", back_populates="recipes")
    tags = db.relationship("Tag", secondary=recipe_tags, backref="recipes", order_by="Tag.name")

    @property
    def ingredient_list(self):
        return [line.strip() for line in (self.ingredients or "").splitlines() if line.strip()]

    @property
    def step_list(self):
        return [line.strip() for line in (self.instructions or "").splitlines() if line.strip()]


@event.listens_for(Recipe, "before_insert")
@event.listens_for(Recipe, "before_update")
def update_search_text(mapper, connection, recipe):
    parts = (recipe.title, recipe.summary, recipe.ingredients)
    recipe.search_text = " ".join(p or "" for p in parts).lower()
