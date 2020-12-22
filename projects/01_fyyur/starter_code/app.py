#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from model import app, db, Venue, Artist, Show 
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app.config.from_object('config')
moment = Moment(app)
db.init_app(app)


# TODO: connect to a local postgresql database
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    cityState = db.session.query(Venue).filter_by(
        city=Venue.city, state=Venue.state).distinct(Venue.city, Venue.state)  # Gets Cities and States distinctively from the DB
    venues = []
    finalData = []
    for CS in cityState:

        venuesInCS = db.session.query(
            Venue).filter_by(city=CS.city, state=CS.state).all()
        for v in venuesInCS:
            venues.append({
                "id": v.id,
                "name": v.name,
            })

        finalData.append({
            "city": CS.city,
            'state': CS.state,
            'venues': venuesInCS
        })
    return render_template('pages/venues.html', areas=finalData)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    searchTerm = request.form.get('search_term', '')
    results = db.session.query(Venue).filter(
      Venue.name.ilike("%" + searchTerm + "%")).all()
    venues = []
    for result in results:
        shows = db.session.query(
            Show.start_time).filter_by(artist_id=result.id)
        upcomingShows = []
        for show in shows:
            if show.start_time > datetime.now():
                upcomingShows.append(show)
        venues.append({
            'id': result.id,
            'name': result.name,
            'num_upcoming_shows': len(upcomingShows)
        })

    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    v = db.session.query(Venue).get(venue_id)

    shows = db.session.query(Show).join(
        Venue).filter(venue_id == Show.venue_id)

    pastShows = []

    upcomingShows = []

    for show in shows:  # Cycles through shows and determines if a show is upcoming or past
        showDate = show.start_time
        if showDate > datetime.now():
            upcomingShows.append({
                'artist_id': show.artist_id,
                'artist_name': db.session.query(Artist).get(show.artist_id).name,
                'artist_image_link': db.session.query(Artist).get(show.artist_id).image_link,
                'start_time': str(show.start_time)
            })
        else:
            pastShows.append({
                'artist_id': show.artist_id,
                'artist_name': db.session.query(Artist).get(show.artist_id).name,
                'artist_image_link': db.session.query(Artist).get(show.artist_id).image_link,
                'start_time': str(show.start_time)
            })

    venueData = {
        'id': v.id,
        'name': v.name,
        'genres': v.genres,
        'address': v.address,
        'city': v.city,
        'state': v.state,
        'phone': v.phone,
        'facebook_link': v.facebook_link,
        'seeking_talent': v.seeking_talent,
        'seeking_description': v.seeking_description,
        'image_link': v.image_link,
        'past_shows': pastShows,
        'upcoming_shows': upcomingShows,
        'past_shows_count': len(pastShows),
        'upcoming_shows_count': len(upcomingShows)
    }

    return render_template('pages/show_venue.html', venue=venueData)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    """
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    """
    form = VenueForm(request.form)
    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' +request.form['name'] + ' has been successfully added.')
    # on successful db insert, flash success
    except:
        flash('There was an error inserting ' + request.form['name'] + ' as an artist.')
        db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Show.query.filter_by(venue_id=venue_id).delete()
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash("Venue successfully deleted!")
    except:
        db.session.rollback()
        flash("Venue unsuccessfully deleted.")
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    Artists = db.session.query(Artist).all()
    data = []
    for artist in Artists:
        data.append({
            'id': artist.id,
            'name': artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    searchTerm = request.form.get('search_term', '')  
    results = db.session.query(Artist).filter(  
        Artist.name.ilike("%" + searchTerm + "%")).all()
    artists = []

    for result in results:
        shows = db.session.query(
            Show.start_time).filter_by(artist_id=result.id)
        upcomingShows = []
        for show in shows:
            if show.start_time > datetime.now():
                upcomingShows.append(show)
        artists.append({
            'id': result.id,
            'name': result.name,
            'num_upcoming_shows': len(upcomingShows)
        })

    response = {
        "count": len(results),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = db.session.query(Artist).get(artist_id)
    shows = db.session.query(Show).join(
        Artist).filter(artist_id == Show.artist_id)
    pastShows = []
    upcomingShows = []
    for show in shows:
        if show.start_time > datetime.now():
            upcomingShows.append({
                'venue_id': show.venue_id,
                'venue_name': db.session.query(Venue).get(show.venue_id).name,
                'venue_image_link': db.session.query(Venue).get(show.venue_id).image_link,
                'start_time': str(show.start_time)
            })
        else:
            pastShows.append({
                'venue_id': show.venue_id,
                'venue_name': db.session.query(Venue).get(show.venue_id).name,
                'venue_image_link': db.session.query(Venue).get(show.venue_id).image_link,
                'start_time': str(show.start_time)
            })
    resposnse = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        'past_shows': pastShows,
        'upcoming_shows': upcomingShows,
        'past_shows_count': len(pastShows),
        'upcoming_shows_count': len(upcomingShows)
    }
    return render_template('pages/show_artist.html', artist=resposnse)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    name = form.name.data = db.session.query(
        Artist.name).filter_by(id=artist_id).scalar()  # Scalar gets string value
    city = form.city.data = db.session.query(
        Artist.city).filter_by(id=artist_id).scalar()
    state = form.state.data = db.session.query(
        Artist.state).filter_by(id=artist_id).scalar()
    genres = form.genres.data = db.session.query(
        Artist.genres).filter_by(id=artist_id).all()
    facebook_link = form.facebook_link.data = db.session.query(
        Artist.facebook_link).filter_by(id=artist_id).scalar()
    image_link = form.image_link.data = db.session.query(
        Artist.image_link).filter_by(id=artist_id).scalar()
    phone = form.phone.data = db.session.query(
        Artist.phone).filter_by(id=artist_id).scalar()
    artist = {
        "id": artist_id,
        "name": name,
        "genres": genres,
        "city": city,
        "state": state,
        "phone": phone,
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": facebook_link,
        "seeking_venue": False,
        "seeking_description": "",
        "image_link": image_link
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']

    try:
        Artist1 = db.session.query(Artist).get(artist_id)
        Artist1.name = name
        Artist1.city = city
        Artist1.state = state
        Artist1.phone = phone
        Artist1.genres = genres
        Artist1.facebook_link = facebook_link
        Artist1.image_link = image_link
        db.session.commit()
        flash("Artist successfully edited!")
    except:
        flash("Artist unsuccessfully edited.")
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    name = form.name.data = db.session.query(
        Venue.name).filter_by(id=venue_id).scalar()
    city = form.city.data = db.session.query(
        Venue.city).filter_by(id=venue_id).scalar()
    state = form.state.data = db.session.query(
        Venue.state).filter_by(id=venue_id).scalar()
    genres = form.genres.data = db.session.query(
        Venue.genres).filter_by(id=venue_id).all()
    facebook_link = form.facebook_link.data = db.session.query(
        Venue.facebook_link).filter_by(id=venue_id).scalar()
    image_link = form.image_link.data = db.session.query(
        Venue.image_link).filter_by(id=venue_id).scalar()
    phone = form.phone.data = db.session.query(
        Venue.phone).filter_by(id=venue_id).scalar()
    address = form.address.data = db.session.query(
        Venue.address).filter_by(id=venue_id).scalar()

    venue = {
        "id": venue_id,
        "name": name,
        "genres": genres,
        "address": address,
        "city": city,
        "state": state,
        "phone": phone,
        "website": "",
        "facebook_link": facebook_link,
        "seeking_talent": False,
        "seeking_description": "",
        "image_link": image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    name = request.form['name']
    city = request.form['city']
    address = request.form['address']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']

    try:
        Venue1 = db.session.query(Venue).get(venue_id)
        Venue1.name = name
        Venue1.city = city
        Venue1.state = state
        Venue1.phone = phone
        Venue1.genres = genres
        Venue1.facebook_link = facebook_link
        Venue1.image_link = image_link
        Venue1.address = address
        db.session.commit()
        flash("Artist successfully edited!")
    except:
        flash("Artist unsuccessfully edited.")
    
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    """
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    """
    form = ArtistForm(request.form)
    try:
        artist = Artist()
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        flash('Artist ' + request.form['name'] + ' was unsuccessfully listed.')
        db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows = db.session.query(Show).join(Artist).filter(
        Artist.id == Show.artist_id).all()
    showsAndData = []
    for show in shows:  # Cycles through all shows in DB
        artist = db.session.query(Artist).get(show.artist_id)
        venue = db.session.query(Venue).get(show.venue_id)
        showsAndData.append({
            'venue_id': venue.id,
            'venue_name': venue.name,
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start_time)
        })
    return render_template('pages/shows.html', shows=showsAndData)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    
    artistID = request.form['artist_id']
    venueID = request.form['venue_id']
    startTime = request.form['start_time']
    
    form = ShowForm(request.form)
    # on successful db insert, flash success
    if (len(db.session.query(Artist).filter_by(id=artistID).all()) or len(db.session.query(Venue).filter_by(id=venueID).all())) == 0:
          flash('Error: Either Artist or Venue don\'t exist!')
    else:
        try:
            show = Show()
            form.populate_obj(show)
            db.session.add(show)
            db.session.commit()
            flash('Show successfully added!')
        except:
            db.session.rollback()
            flash(
                'Uh oh! an Error happened when connecting to the Database. Don\'t worry, not your fault!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
