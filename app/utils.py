import re
import uuid
from pathlib import Path

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "", "ю": "iu",
    "я": "ia", "ё": "e", "ы": "y", "э": "e", "ъ": "", "'": "", "’": "", "ʼ": "",
}


def slugify(text):
    text = "".join(TRANSLIT.get(ch, ch) for ch in text.lower())
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


def unique_slug(model, text, exclude_id=None):
    base = slugify(text)
    slug, n = base, 2
    while True:
        query = model.query.filter_by(slug=slug)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base}-{n}"
        n += 1


class ImageError(ValueError):
    pass


def save_image(file_storage):
    """Validate, resize and store an uploaded image. Returns the stored filename."""
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise ImageError("Дозволені формати: jpg, jpeg, png, webp.")
    try:
        img = Image.open(file_storage.stream)
        img = ImageOps.exif_transpose(img)
    except (UnidentifiedImageError, OSError):
        raise ImageError("Файл не є коректним зображенням.")

    max_width = current_app.config["MAX_IMAGE_WIDTH"]
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)

    if ext in ("jpg", "jpeg"):
        ext = "jpg"
        img = img.convert("RGB")

    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = Path(current_app.config["UPLOAD_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / filename, quality=85)
    return filename


def delete_image(filename):
    if filename:
        (Path(current_app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
