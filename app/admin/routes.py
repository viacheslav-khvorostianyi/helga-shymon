from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..forms import CategoryForm, DeleteForm, LoginForm, RecipeForm
from ..models import Category, Recipe, Tag, User
from ..utils import ImageError, delete_image, save_image, unique_slug

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_url = request.args.get("next", "")
            # Only follow relative redirects to avoid open-redirects
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("admin.dashboard")
            return redirect(next_url)
        flash("Невірний логін або пароль.", "error")
    return render_template("admin/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з адмін-панелі.", "success")
    return redirect(url_for("public.index"))


@bp.route("/")
@login_required
def dashboard():
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return render_template("admin/dashboard.html", recipes=recipes, delete_form=DeleteForm())


def category_choices():
    return [(0, "— без категорії —")] + [(c.id, c.name) for c in Category.query.order_by(Category.name)]


def parse_tags(raw):
    tags, seen = [], set()
    for name in (raw or "").split(","):
        name = name.strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, slug=unique_slug(Tag, name))
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)
    return tags


def save_recipe(form, recipe):
    """Copy form data into recipe and persist it. Returns False if the image is invalid."""
    if form.image.data:
        try:
            new_image = save_image(form.image.data)
        except ImageError as e:
            form.image.errors.append(str(e))
            return False
        delete_image(recipe.image_filename)
        recipe.image_filename = new_image
    elif form.remove_image.data:
        delete_image(recipe.image_filename)
        recipe.image_filename = None

    if recipe.title != form.title.data or not recipe.slug:
        recipe.slug = unique_slug(Recipe, form.title.data, exclude_id=recipe.id)
    recipe.title = form.title.data
    recipe.category_id = form.category_id.data or None
    recipe.summary = form.summary.data
    recipe.ingredients = form.ingredients.data
    recipe.instructions = form.instructions.data
    recipe.is_published = form.is_published.data
    recipe.tags = parse_tags(form.tags.data)

    db.session.add(recipe)
    db.session.commit()
    return True


@bp.route("/recipes/new", methods=["GET", "POST"])
@login_required
def recipe_new():
    form = RecipeForm()
    form.category_id.choices = category_choices()
    if form.validate_on_submit() and save_recipe(form, Recipe()):
        flash("Рецепт створено.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/recipe_form.html", form=form, recipe=None)


@bp.route("/recipes/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def recipe_edit(recipe_id):
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    form = RecipeForm(obj=recipe)
    form.category_id.choices = category_choices()
    if request.method == "GET":
        form.category_id.data = recipe.category_id or 0
        form.tags.data = ", ".join(t.name for t in recipe.tags)
    if form.validate_on_submit() and save_recipe(form, recipe):
        flash("Зміни збережено.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/recipe_form.html", form=form, recipe=recipe)


@bp.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
@login_required
def recipe_delete(recipe_id):
    if not DeleteForm().validate_on_submit():
        abort(400)
    recipe = db.session.get(Recipe, recipe_id) or abort(404)
    delete_image(recipe.image_filename)
    db.session.delete(recipe)
    db.session.commit()
    flash(f"Рецепт «{recipe.title}» видалено.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        if Category.query.filter_by(name=name).first():
            flash("Така категорія вже існує.", "error")
        else:
            db.session.add(Category(name=name, slug=unique_slug(Category, name)))
            db.session.commit()
            flash("Категорію додано.", "success")
        return redirect(url_for("admin.categories"))
    cats = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", form=form, categories=cats, delete_form=DeleteForm())


@bp.route("/categories/<int:category_id>/rename", methods=["POST"])
@login_required
def category_rename(category_id):
    if not DeleteForm().validate_on_submit():
        abort(400)
    category = db.session.get(Category, category_id) or abort(404)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Назва не може бути порожньою.", "error")
    elif Category.query.filter(Category.name == name, Category.id != category.id).first():
        flash("Така категорія вже існує.", "error")
    else:
        category.name = name
        category.slug = unique_slug(Category, name, exclude_id=category.id)
        db.session.commit()
        flash("Категорію перейменовано.", "success")
    return redirect(url_for("admin.categories"))


@bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def category_delete(category_id):
    if not DeleteForm().validate_on_submit():
        abort(400)
    category = db.session.get(Category, category_id) or abort(404)
    if category.recipes:
        flash("Неможливо видалити категорію, в якій є рецепти.", "error")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Категорію видалено.", "success")
    return redirect(url_for("admin.categories"))
