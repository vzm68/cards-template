# Import libraries
from flask import Flask, request, send_file, render_template, make_response
from PIL import Image, ImageDraw, ImageFont, ImageOps
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, BooleanField
from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['UPLOAD_FOLDER'] = './uploads'


# Create a form
class ImageForm(FlaskForm):
    first_name = StringField('First Name:', validators=[InputRequired()])
    last_name = StringField('Last Name:', validators=[InputRequired()])
    image = FileField('Upload Image:', validators=[InputRequired()])
    studio = BooleanField('Studio')  # Studio checkbox
    phone = BooleanField('Phone')  # Phone checkbox
    submit = SubmitField('Download')


# Function to round corners of an image
def round_corners(image, radius):
    image = image.convert('RGBA')
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

    alpha = Image.new('L', image.size, 255)
    w, h = image.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0)) # top left
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius)) # bottom left
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0)) # top right
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius)) # bottom right

    image.putalpha(alpha)
    return image


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ImageForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        image = form.image.data
        studio = form.studio.data  # Get the value of the studio checkbox
        phone = form.phone.data  # Get the value of the phone checkbox
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Open the image file
        with Image.open(filepath) as img:
            # Round corners of the image
            radius = 20  # radius of rounded corners
            rounded_img = round_corners(img, radius)

            # Add a white border for the frame
            border = (20, 40, 20, 250)  # 10 pixels on each side, 70 pixels at the bottom for text
            framed_img = Image.new('RGBA', (
            rounded_img.width + border[0] + border[2], rounded_img.height + border[1] + border[3]), 'white')
            framed_img.paste(rounded_img, (border[0], border[1]), rounded_img)

            # Draw text
            draw = ImageDraw.Draw(framed_img)
            # Specify the font-family and the font-size
            font = ImageFont.truetype("GTAmericaLCG-ExtMd.ttf", 80)

            # Draw first name
            text_width, text_height = draw.textsize(first_name, font=font)
            position = ((framed_img.width - text_width) // 2, framed_img.height - 2*text_height - border[3] // 4)
            draw.text(position, first_name, fill='black', font=font)

            # Draw last name
            text_width, text_height = draw.textsize(last_name, font=font)
            position = ((framed_img.width - text_width) // 2, framed_img.height - text_height - border[3] // 4)
            draw.text(position, last_name, fill='black', font=font)

            # If the studio checkbox is checked, paste the studio image
            overlay_images = []
            if studio:
                studio_img = Image.open('studio.png')
                overlay_images.append(studio_img)
            if phone:
                phone_img = Image.open('phone.png')
                overlay_images.append(phone_img)

            overlay_widths = [i.width for i in overlay_images]
            total_overlay_width = sum(overlay_widths) + 20 * (len(overlay_images) - 1)  # Add 10px gap between images

            start_x = (framed_img.width - total_overlay_width) // 2  # This will center the overlays

            for overlay in overlay_images:
                position = (start_x, framed_img.height - overlay.height - 270)  # 150px from the bottom
                framed_img.paste(overlay, position, overlay)
                start_x += overlay.width + 20  # Move the start_x to the right for the next image

            # Save the image in memory
            byte_io = io.BytesIO()
            framed_img.convert('RGB').save(byte_io, 'JPEG')
            # framed_img.save(byte_io, 'JPEG')
            byte_io.seek(0)
            response = make_response(send_file(byte_io, mimetype='image/jpeg'))
            # filename by Name on card
            filename = f"{first_name} {last_name}"
            response.headers.set('Content-Disposition', 'attachment', filename=f'{filename}.jpg')
            return response

    return render_template('index.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)

# Create a form GTAmericaLCG-ExtMd.ttf