from app import application, classes, db
from flask import render_template, redirect, url_for, Response
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from utils import *
from wtforms import SubmitField
from werkzeug.utils import secure_filename
import os
import subprocess
import boto3
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from flask_login import current_user, login_user, login_required, logout_user


#docker run --rm -it -p 5000:5000 zwy8203302/app:v0 bash




@application.route('/index')
@application.route('/')
def index():
    """Index Page : Renders index.html with author name."""
    images = [{'text': 'Good Form', 'image': 'https://images.pexels.com/photos/176782/pexels-photo-176782.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500'},
              {'text': 'User Input', 'image': 'https://images.pexels.com/photos/176782/pexels-photo-176782.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500'}]
    return (render_template('index.html', images=images))


@application.route('/team')
def team():
    """Index Page : Renders index.html with author name."""
    # return ("<h1> Hello World </h1>")
    authors = ['Boliang Liu', 'Daniel Carrera', 'Elyse Cheung-Sutton',
               'Kris Johnson', 'Kexin Wang', 'Moh Kaddoura',
               'Suren Gunturu', 'Wenyao Zhang']
    return (render_template('team.html', authors=authors))


@application.route('/upload', methods=['GET', 'POST'])
def upload():
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    # s3_location = 'http://{}.s3.amazonaws.com/'.format(bucket_name)
    bucket_name = "swolemate-s3"
    s3_location = 'https://s3.console.aws.amazon.com/s3/buckets/swolemate-s3'
    # print(aws_access_key_id)
    # print(aws_secret_access_key)

    """upload a file from a client machine."""
    file = classes.UploadFileForm()  # file : UploadFileForm class instance
    if file.validate_on_submit():  # Check it's a POST request that's valid
        workout_type = dict(classes.WORKOUT_CHOICES).get(file.exercise_selection.data)
        side = dict(classes.SIDE_CHOICES).get(file.side_selection.data)
        
        f = file.file_selector.data  # f : Data of FileField
        filename = secure_filename(f.filename)
        
        f.save(os.path.join(
            'videos', filename
        ))

        items = filename.split('.')
        subprocess.run([
            'python3', 'detectron2/demo.py',
            '--config-file', 'detectron2_repo/configs/COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml',
            '--video-input', 'videos/' + filename,
            '--output', 'output/' + items[0] + '.json',
            '--opts',
            'MODEL.WEIGHTS', 'detectron2://COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x/137849621/model_final_a6e10b.pkl',
            'MODEL.DEVICE', 'cpu',
        ])
        
        json_file_name = 'output/' + items[0] + '.json'
    
        data = load_tester(json_file_name)
        
        X_train_names = files_in_order('poses_compressed/bicep')
        y_train = get_labels(X_train_names)

        X_train_1, X_train_2 = load_features(X_train_names)

        value, _, _ = kmeans_test(['demo'], X_train_1=X_train_1, X_train_2=X_train_2, y_train=y_train, data=data, side=side, bool_val=True, exercise=workout_type)
        
        
        """session = boto3.Session()

        session.resource("s3")\
            .Bucket(bucket_name)\
            .put_object(Key=filename, Body=f, ACL='public-read-write')

        uploaded_file = 'https://swolemate-s3.s3.us-west-2.amazonaws.com/' + filename
        """
        #return redirect(url_for('userpage', value=value))  # Redirect to / (/index) page.
        return userpage(value)
    return render_template('upload.html', form=file)



# update :  log in & log out

@application.route('/register',  methods=('GET', 'POST'))
def register():
    registration_form = classes.RegistrationForm()
    if registration_form.validate_on_submit():
        username = registration_form.username.data
        password = registration_form.password.data
        email = registration_form.email.data

        user_count = classes.User.query.filter_by(username=username).count() \
                     + classes.User.query.filter_by(email=email).count()
        if (user_count > 0):
            return '<h1>Error - Existing user : ' + username \
                   + ' OR ' + email + '</h1>'
        else:
            user = classes.User(username, email, password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('register.html', form=registration_form)


@application.route('/login', methods=['GET', 'POST'])
def login():
    login_form = classes.LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = classes.User.query.filter_by(username=username).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('userpage'))
            # return("<h1> Welcome {}!</h1>".format(username))

    return render_template('login.html', form=login_form)


@application.route('/logout')
@login_required
def logout():
    before_logout = '<h1> Before logout - is_autheticated : ' \
                    + str(current_user.is_authenticated) + '</h1>'

    logout_user()

    after_logout = '<h1> After logout - is_autheticated : ' \
                   + str(current_user.is_authenticated) + '</h1>'
    return before_logout + after_logout

#@application.route('/plot.png')
#def plot_png():
#    fig = classes.create_figure()
#    output = io.BytesIO()
#    FigureCanvas(fig).print_png(output)
#    return Response(output.getvalue(), mimetype='image/png')
#
    
@application.route('/userpage')
def userpage(value):
    # Show Shiqi vid
    plot_file = 'image.jpg'
    # Graph hip points
    return render_template('userpage.html', value=value)
