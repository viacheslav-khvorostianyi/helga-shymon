import click
from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Будь ласка, увійдіть, щоб відкрити адмін-панель."
    login_manager.login_message_category = "warning"

    from .models import Category, User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_categories():
        return {"nav_categories": Category.query.order_by(Category.name).all()}

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    from .admin.routes import bp as admin_bp
    from .public.routes import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    register_cli(app)
    return app


def register_cli(app):
    from .models import Category, Recipe, Tag, User
    from .utils import unique_slug

    @app.cli.command("init-db")
    def init_db():
        """Create database tables."""
        db.create_all()
        click.echo("Базу даних створено.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Логін")
    @click.password_option(prompt="Пароль", confirmation_prompt="Повторіть пароль")
    def create_admin(username, password):
        """Create an admin user (or reset an existing user's password)."""
        db.create_all()
        user = User.query.filter_by(username=username).first() or User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Адміністратора «{username}» збережено.")

    @app.cli.command("seed")
    def seed():
        """Add sample categories and recipes."""
        db.create_all()
        if Recipe.query.first():
            click.echo("Рецепти вже існують — пропускаю.")
            return

        def category(name):
            c = Category(name=name, slug=unique_slug(Category, name))
            db.session.add(c)
            db.session.flush()
            return c

        def tag(name):
            t = Tag(name=name, slug=unique_slug(Tag, name))
            db.session.add(t)
            db.session.flush()
            return t

        soups, mains, desserts = category("Супи"), category("Основні страви"), category("Десерти")
        traditional, quick, vegetarian = tag("традиційне"), tag("швидко"), tag("вегетаріанське")

        samples = [
            dict(
                title="Український борщ",
                category=soups,
                tags=[traditional],
                summary="Класичний червоний борщ на яловичому бульйоні.",
                ingredients="500 г яловичини\n3 картоплини\n1 буряк\n1 морква\n1 цибулина\n1/4 капусти\n2 ст. л. томатної пасти\nсіль, перець, лавровий лист",
                instructions="Зваріть бульйон з яловичини (1,5 год).\nДодайте нарізану картоплю та капусту.\nОбсмажте цибулю, моркву й буряк з томатною пастою.\nДодайте засмажку в бульйон, варіть 10 хв.\nПриправте й дайте настоятися 20 хв.",
            ),
            dict(
                title="Вареники з картоплею",
                category=mains,
                tags=[traditional, vegetarian],
                summary="Домашні вареники з картопляною начинкою та смаженою цибулею.",
                ingredients="400 г борошна\n200 мл води\n1 яйце\n600 г картоплі\n2 цибулини\nолія, сіль",
                instructions="Замісіть тісто з борошна, води, яйця та солі.\nЗваріть картоплю й зробіть пюре.\nОбсмажте цибулю, половину додайте в пюре.\nРозкачайте тісто, виріжте кружечки, ліпіть вареники.\nВаріть 3–4 хв після спливання, подавайте з цибулею.",
            ),
            dict(
                title="Сирники",
                category=desserts,
                tags=[quick, vegetarian],
                summary="Пухкі сирники на сніданок за 20 хвилин.",
                ingredients="500 г кисломолочного сиру\n1 яйце\n2 ст. л. цукру\n3 ст. л. борошна\nдрібка солі\nолія для смаження",
                instructions="Змішайте сир, яйце, цукор і сіль.\nДодайте борошно, сформуйте сирники.\nОбсмажте на середньому вогні по 3 хв з кожного боку.",
            ),
        ]
        for data in samples:
            recipe = Recipe(slug=unique_slug(Recipe, data["title"]), **data)
            db.session.add(recipe)
            db.session.flush()
        db.session.commit()
        click.echo(f"Додано {len(samples)} рецепти.")
