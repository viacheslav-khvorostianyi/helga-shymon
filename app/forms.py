from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Логін", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Увійти")


class RecipeForm(FlaskForm):
    title = StringField("Назва", validators=[DataRequired(), Length(max=200)])
    category_id = SelectField("Категорія", coerce=int)
    tags = StringField("Теги (через кому)", validators=[Length(max=500)])
    summary = TextAreaField("Короткий опис")
    ingredients = TextAreaField("Інгредієнти (кожен з нового рядка)")
    instructions = TextAreaField("Приготування (кожен крок з нового рядка)")
    image = FileField("Фото", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Лише зображення!")])
    remove_image = BooleanField("Видалити поточне фото")
    is_published = BooleanField("Опубліковано", default=True)
    submit = SubmitField("Зберегти")


class CategoryForm(FlaskForm):
    name = StringField("Назва категорії", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Додати")


class DeleteForm(FlaskForm):
    """Empty form used only for its CSRF token on delete buttons."""
