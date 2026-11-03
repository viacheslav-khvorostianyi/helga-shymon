from flask import Blueprint, current_app, render_template, request

from ..models import Category, Recipe, Tag

bp = Blueprint("public", __name__)


def published():
    return Recipe.query.filter_by(is_published=True).order_by(Recipe.created_at.desc())


def paginate(query):
    page = request.args.get("page", 1, type=int)
    return query.paginate(page=page, per_page=current_app.config["RECIPES_PER_PAGE"], error_out=False)


@bp.route("/")
def index():
    return render_template("public/index.html", pagination=paginate(published()))


@bp.route("/recipe/<slug>")
def recipe(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("public/recipe.html", recipe=recipe)


@bp.route("/category/<slug>")
def category(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    pagination = paginate(published().filter(Recipe.category_id == category.id))
    return render_template("public/category.html", category=category, pagination=pagination)


@bp.route("/tag/<slug>")
def tag(slug):
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    pagination = paginate(published().filter(Recipe.tags.any(Tag.id == tag.id)))
    return render_template("public/tag.html", tag=tag, pagination=pagination)


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    pagination = None
    if q:
        pagination = paginate(published().filter(Recipe.search_text.contains(q.lower(), autoescape=True)))
    return render_template("public/search.html", q=q, pagination=pagination)
