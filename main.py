import numpy as np
from PIL import Image
from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, IntegerField, RadioField
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import os
import shutil
from collections import Counter
from sklearn.cluster import KMeans


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jhsbdKJ34unkj9238nfqel'
Bootstrap(app)


# Image form
class ImageForm(FlaskForm):
    image = FileField("Image to Upload", validators=[FileRequired(), FileAllowed({"jpeg", "png", "jpg"})])
    num_color = IntegerField("Number of colors", default=10)
    pal = RadioField(choices=["True Colors", "Palette"], default="True Colors")
    submit = SubmitField("Generate")


def clear_directories():
    for filename in os.listdir("static/image/"):
        file_path = os.path.join("static/image/", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"File cannot be deleted: {e}")


def save_file(form):
    f = form.image.data
    filename = secure_filename(f.filename)
    input_file = "static/image/" + filename
    f.save(input_file)
    return input_file, filename


def rgb_to_hex(color):
    return "#%02x%02x%02x" % (int(color[0]), int(color[1]), int(color[2]))


# Home page
@app.route("/", methods=["GET", "POST"])
def home():
    form = ImageForm()
    if form.validate_on_submit():
        clear_directories()
        input_file, filename = save_file(form)

        image_file = form.image.data
        image = Image.open(image_file)

        size = image.size[0] * image.size[1]
        if size > 89478485:
            flash("Photo pixel amount is too large to process.")
            return redirect(url_for("home"))

        img_array_3d = np.array(image)
        img_array_2d = img_array_3d.reshape(-1, img_array_3d.shape[-1])

        results = {}
        if form.pal.data == "True Colors":
            counter_dict = Counter([tuple(arr) for arr in img_array_2d])
            sort_list = sorted(counter_dict, key=counter_dict.get, reverse=True)
            try:
                top_10_colors = sort_list[:form.num_color.data]
            except IndexError:
                top_10_colors = sort_list

            for color in top_10_colors:
                hex = rgb_to_hex(color)
                count = counter_dict.get(color)
                p = round((count / size) * 100, 2)
                results[hex] = p
        else:
            model = KMeans(n_clusters=form.num_color.data, n_init="auto").fit(img_array_2d)
            top_10_colors = model.cluster_centers_
            for color in top_10_colors:
                hex = rgb_to_hex(color.tolist())
                results[hex] = 0

        image_path = f"static/image/{filename}"
        return render_template("index.html", form=form, image=image_path, results=results)
    return render_template("index.html", form=form)


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
