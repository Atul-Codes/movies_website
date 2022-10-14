from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

# ----------------------------------------- declarations --------------------------------------------------- #
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)

API_KEY = '58918ee4d20f3e611697aa2ffc3fd752'
API_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODkxOGVlNGQyMGYzZTYxMTY5N2FhMmZmYzNmZDc1MiIsInN1YiI6IjYzMzg3MjU3ODdmM2Yy' \
            'MDA3YTJmNGU4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.3LkBR9_j8wNN_IPNI3Rk86SiFepjKY6SB0rkeEszrGY'

# -------------------------------------------- Forms ----------------------------------------------------- #
class RateMovieForm(FlaskForm):
    rating = StringField(label="Rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Review", validators=[DataRequired()])
    submit = SubmitField(label="Update Movie")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

# ---------------------------------------- Database creation ----------------------------------------------- #
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(150), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(120), nullable=False)
    img_url = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return '<Post %r>' % self.title


if not os.path.isfile('sqlite:///movie-collection.db'):
    db.create_all()

# ----------------------------------------- Website Setup  ----------------------------------------------------- #
@app.route("/")
def home():
    movies_db = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies_db)):
        movies_db[i].ranking = len(movies_db) - i
    db.session.commit()
    return render_template("index.html", movies_data=movies_db)

# add page to search for movie name and get list of movies with same name. Redirects to select page
@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        query = form.title.data
        response = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={query}')
        movie_list = response.json()
        return render_template("select.html", movies=movie_list['results'])
    return render_template("add.html", form=form)


# function to add selected movie into database. Once a movie is selected, this gets triggered and, it adds the
# movie in database. It is not a page and, it just redirects user to add review and rating page
@app.route("/add-movie/movie?id=<int:movie_id>")
def add_movie(movie_id):
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US)")
    movie_data = response.json()
    new_movie = Movie(
        title=movie_data['title'],
        year=movie_data['release_date'],
        description=movie_data['overview'],
        rating=7.3,
        ranking=10,
        review="My favourite character was the caller.",
        img_url=f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    new_movie_db_obj = Movie.query.filter_by(title=movie_data['title']).first()
    return redirect(url_for("edit", id=new_movie_db_obj.id))

# page to edit movie rating and review. user can come here either after clicking on edit button on movie card or
# while adding a movie in DB. once form submitted, user gets redirected to home page
@app.route("/edit/id?<int:id>", methods=["GET", "POST"])
def edit(id):
    form = RateMovieForm()
    movie_id = id
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_to_update)


# function to delete any movie entry from record. It is only a button so, returns to home page
@app.route('/delete/id?<int:id>')
def delete(id):
    movie_id = id
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
