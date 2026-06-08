import os
from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from flask import send_from_directory
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
app = Flask(__name__)

app.secret_key = "musicify123"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'musicify_db'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(username) < 5:
            return render_template(
                'register.html',
                error="Username must be at least 5 characters"
            )

        if len(password) < 6:
            return render_template(
                'register.html',
                error="Password must be at least 6 characters"
            )

        if not any(char.isdigit() for char in password):
            return render_template(
                'register.html',
                error="Password must contain at least one number"
            )

        if not any(char.isalpha() for char in password):
            return render_template(
                'register.html',
                error="Password must contain at least one letter"
            )

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        if user:

            cur.close()

            return render_template(
                'register.html',
                error="Email already registered"
            )

        hashed_password = generate_password_hash(password)
       
        cur.execute(
         "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        existing_username = cur.fetchone()

        if existing_username:

         cur.close()

         return render_template(
        'register.html',
        error="Username already exists"
      )
        cur.execute(
            """
            INSERT INTO users
            (username,email,password)
            VALUES(%s,%s,%s)
            """,
            (username, email, hashed_password)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template('register.html')

from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # Admin Login
        if email == "sumitpatelofficial05@gmail.com" and password == "sumit05":
            session['user'] = 'admin'
            return redirect('/admin')

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()

        if user and check_password_hash(user[3], password):

            session['user_id'] = user[0]      # id
            session['user'] = user[1]         # username

            print("LOGIN USER =", session['user'])

            return redirect('/songs')

        return render_template(
            'login.html',
            error="Invalid Email or Password"
        )

    return render_template('login.html')

@app.route('/admin')
def admin():

    if session.get('user') != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Total Users
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
     
    cur.execute("SELECT COUNT(*) FROM downloads")
    total_downloads = cur.fetchone()[0]
    # Total Songs
    cur.execute("SELECT COUNT(*) FROM songs")
    total_songs = cur.fetchone()[0]
     
    cur.execute("SELECT COUNT(*) FROM playlists")
    total_playlists = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cur.fetchone()[0]
    cur.execute("""
    SELECT song_name, play_count
    FROM songs
    ORDER BY play_count DESC
    LIMIT 1
    """)

    most_played_song = cur.fetchone()
    # Total Favorites

    cur.execute("SELECT COUNT(*) FROM favorites")
    total_favorites = cur.fetchone()[0]

    # Total Likes
    cur.execute("SELECT SUM(likes) FROM songs")
    total_likes = cur.fetchone()[0] or 0

    # Most Liked Song
    cur.execute("""
        SELECT song_name, likes
        FROM songs
        ORDER BY likes DESC
        LIMIT 1
    """)
    most_liked_song = cur.fetchone()

    # Most Favorite Song
    cur.execute("""
        SELECT songs.song_name,
        COUNT(favorites.song_id) AS total
        FROM songs
        LEFT JOIN favorites
        ON songs.id = favorites.song_id
        GROUP BY songs.id
        ORDER BY total DESC
        LIMIT 1
    """)
    most_song = cur.fetchone()

    # Top Rated Song
    cur.execute("""
        SELECT songs.song_name,
        AVG(reviews.rating) AS avg_rating
        FROM songs
        JOIN reviews
        ON songs.id = reviews.song_id
        GROUP BY songs.id
        ORDER BY avg_rating DESC
        LIMIT 1
    """)
    top_rated_song = cur.fetchone()

    # All Songs
    cur.execute("SELECT * FROM songs")
    songs = cur.fetchall()
       
    cur.execute("""
    SELECT songs.song_name,
    AVG(reviews.rating) AS avg_rating
    FROM songs
    JOIN reviews
    ON songs.id = reviews.song_id
    GROUP BY songs.id
    ORDER BY avg_rating DESC
    LIMIT 1
  """)

    top_rated_song = cur.fetchone()
    cur.close()

    return render_template(
        'dashboard.html',
        total_users=total_users,
        total_songs=total_songs,
        total_playlists=total_playlists,
        total_reviews=total_reviews,
        total_downloads=total_downloads,
        total_favorites=total_favorites,
        total_likes=total_likes,
        most_played_song=most_played_song,
        most_liked_song=most_liked_song,
        most_song=most_song,
        top_rated_song=top_rated_song,
        songs=songs
    )

@app.route('/songs')
def songs():

    if 'user' not in session:
        return redirect('/login')

    search = request.args.get('search')
    category = request.args.get('category')

    cur = mysql.connection.cursor()

    if category:

        cur.execute(
            "SELECT * FROM songs WHERE category=%s",
            (category,)
        )

    elif search:

        cur.execute(
            "SELECT * FROM songs WHERE song_name LIKE %s",
            ('%' + search + '%',)
        )

    else:

        cur.execute(
            "SELECT * FROM songs"
        )

    songs = cur.fetchall()

    cur.execute("SELECT * FROM reviews")
    reviews = cur.fetchall()

    cur.execute("""
     SELECT song_id,
     AVG(rating)
     FROM reviews
     GROUP BY song_id
     """)

    ratings = cur.fetchall()

    cur.close()

    return render_template(
    "songs.html",
    songs=songs,
    reviews=reviews,
    ratings=ratings
)
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

@app.route('/delete_song/<int:id>', methods=['POST'])
def delete_song(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT file_name, image FROM songs WHERE id=%s",
        (id,)
    )

    song = cur.fetchone()

    if song:

        if song[0]:
            audio_path = os.path.join('static/songs', song[0])

            if os.path.exists(audio_path):
                os.remove(audio_path)

        if song[1]:
            image_path = os.path.join('static/images', song[1])

            if os.path.exists(image_path):
                os.remove(image_path)

    cur.execute(
        "DELETE FROM songs WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/admin')

@app.route('/edit_song/<int:id>', methods=['GET', 'POST'])
def edit_song(id):

    cur = mysql.connection.cursor()

    # Song Fetch
    cur.execute("SELECT * FROM songs WHERE id=%s", (id,))
    song = cur.fetchone()

    if not song:
        cur.close()
        return "Song Not Found"

    if request.method == 'POST':

        song_name = request.form.get('song_name')
        singer = request.form.get('singer')

        cur.execute(
            "UPDATE songs SET song_name=%s, singer=%s WHERE id=%s",
            (song_name, singer, id)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/admin')

    cur.close()

    return render_template(
        'edit_song.html',
        song=song
    )

@app.route('/favorite/<int:id>')
def favorite(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM favorites WHERE username=%s AND song_id=%s",
        (session['user'], id)
    )

    already = cur.fetchone()

    if not already:

        cur.execute(
            "UPDATE songs SET likes = likes + 1 WHERE id=%s",
            (id,)
        )

        cur.execute(
            "INSERT INTO favorites(username,song_id) VALUES(%s,%s)",
            (session['user'], id)
        )

        mysql.connection.commit()

    cur.close()

    return redirect('/songs')


@app.route('/favorites')
def favorites():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT songs.*
        FROM songs
        JOIN favorites
        ON songs.id = favorites.song_id
        WHERE favorites.username = %s
    """, (session['user'],))

    songs = cur.fetchall()

    cur.close()

    return render_template('favorites.html', songs=songs)
     
     
@app.route('/remove_favorite/<int:id>')
def remove_favorite(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM favorites WHERE username=%s AND song_id=%s",
        (session['user'], id)
    )

    cur.execute(
        "UPDATE songs SET likes = likes - 1 WHERE id=%s AND likes > 0",
        (id,)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/favorites')

@app.route('/add_song', methods=['GET', 'POST'])
def add_song():

    if request.method == 'POST':

        song_name = request.form['song_name']
        singer = request.form['singer']
        category = request.form['category']
        audio = request.files['audio']
        image = request.files['image']

        if audio and image:

            cur = mysql.connection.cursor()

            cur.execute(
                """
                SELECT *
                FROM songs
                WHERE song_name=%s
                AND singer=%s
                """,
                (song_name, singer)
            )

            already = cur.fetchone()

            if already:

                cur.close()

                return render_template(
                    'add_song.html',
                    error="This song already exists!"
                )

            audio.save(
                os.path.join(
                    'static/songs',
                    audio.filename
                )
            )

            image.save(
                os.path.join(
                    'static/images',
                    image.filename
                )
            )

            cur.execute(
                """
                INSERT INTO songs
                (song_name, singer, file_name, image, category)
                VALUES(%s,%s,%s,%s,%s)
                """,
                (
                    song_name,
                    singer,
                    audio.filename,
                    image.filename,
                    category
                )
            )

            mysql.connection.commit()
            cur.close()

            return redirect('/admin')

    return render_template('add_song.html')

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # User Data
    cur.execute(
        "SELECT * FROM users WHERE id=%s",
        (session['user_id'],)
    )

    user = cur.fetchone()

    print("SESSION USER =", session['user'])
    print("USER DATA =", user)

    # Total Favorites
    cur.execute(
        "SELECT COUNT(*) FROM favorites WHERE username=%s",
        (session['user'],)
    )

    total_favorites = cur.fetchone()[0]

    # Total Downloads
    cur.execute(
        "SELECT COUNT(*) FROM downloads WHERE username=%s",
        (session['user'],)
    )

    total_downloads = cur.fetchone()[0]

    # Total Playlists
    cur.execute(
        "SELECT COUNT(*) FROM playlists WHERE username=%s",
        (session['user'],)
    )

    total_playlists = cur.fetchone()[0]

    # Recently Played Songs
    cur.execute("""
        SELECT songs.song_name, songs.singer
        FROM recent_songs
        JOIN songs
        ON recent_songs.song_id = songs.id
        WHERE recent_songs.username=%s
        ORDER BY recent_songs.id DESC
        LIMIT 5
    """,
    (session['user'],))

    recent_songs = cur.fetchall()

    cur.close()

    return render_template(
        'profile.html',
        user=user,
        total_favorites=total_favorites,
        total_downloads=total_downloads,
        total_playlists=total_playlists,
        recent_songs=recent_songs
    )
   
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']

        cur.execute(
            "UPDATE users SET username=%s, email=%s WHERE username=%s",
            (username, email, session['user'])
        )

        mysql.connection.commit()

        session['user'] = username

        cur.close()

        return redirect('/profile')

    cur.execute(
        "SELECT * FROM users WHERE username=%s",
        (session['user'],)
    )

    user = cur.fetchone()

    cur.close()

    return render_template('edit_profile.html', user=user)
     
@app.route('/delete_account')
def delete_account():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM favorites WHERE username=%s",
        (session['user'],)
    )

    cur.execute(
        "DELETE FROM users WHERE username=%s",
        (session['user'],)
    )

    mysql.connection.commit()

    cur.close()

    session.clear()

    return redirect('/register')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template(
                'change_password.html',
                error="Passwords do not match"
            )

        cur = mysql.connection.cursor()

        cur.execute(
        "SELECT * FROM users WHERE id=%s",
        (session['user'],)
       )

        user = cur.fetchone()

        if not user:
            cur.close()
            return redirect('/login')

        if not check_password_hash(user[3], current_password):

            cur.close()

            return render_template(
                'change_password.html',
                error="Current Password Incorrect"
            )

        hashed_password = generate_password_hash(new_password)

        cur.execute(
          "UPDATE users SET password=%s WHERE id=%s",
          (hashed_password, session['user_id'])
        )

        mysql.connection.commit()
        cur.close()

        return render_template(
        'change_password.html',
         success="Password Changed Successfully"
        )

        return render_template('change_password.html')

@app.route('/manage_users')
def manage_users():

    if session.get('user') != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, email FROM users")

    users = cur.fetchall()

    cur.close()

    return render_template(
        'manage_users.html',
        users=users
    )

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):

    if session.get('user') != 'admin':
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM users WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/manage_users')

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():

    if 'user' not in session:
        return redirect('/login')

    image = request.files['profile_pic']

    print("FILE =", image.filename)

    if image and image.filename != '':

        cur = mysql.connection.cursor()

        cur.execute(
            """
            UPDATE users
            SET profile_image=%s
            WHERE username=%s
            """,
            (image.filename, session['user'])
        )

        mysql.connection.commit()

        cur.execute(
            "SELECT profile_image FROM users WHERE username=%s",
            (session['user'],)
        )

        print("DB =", cur.fetchone())

        cur.close()

    return redirect('/profile')

@app.route('/play_song/<int:id>')
def play_song(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Recent Songs Save
    cur.execute(
        "INSERT INTO recent_songs(username, song_id) VALUES(%s,%s)",
        (session['user'], id)
    )

    # Play Count Increase
    cur.execute(
        "UPDATE songs SET play_count = play_count + 1 WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return "Played"

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        playlist_name = request.form['playlist_name']

        cover_image = request.files.get('cover_image')

        filename = None

        if cover_image and cover_image.filename != "":

            filename = cover_image.filename

            cover_image.save(
                os.path.join(
                    'static/playlists',
                    filename
                )
            )

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO playlists
            (username, playlist_name, cover_image)
            VALUES(%s,%s,%s)
            """,
            (session['user'], playlist_name, filename)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/my_playlists')

    return render_template('create_playlist.html')

@app.route('/my_playlists')
def my_playlists():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM playlists WHERE username=%s",
        (session['user'],)
    )

    playlists = cur.fetchall()

    cur.close()

    return render_template(
        'my_playlists.html',
        playlists=playlists
    )
    
@app.route('/delete_playlist/<int:id>')
def delete_playlist(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM playlists WHERE id=%s AND username=%s",
        (id, session['user'])
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/my_playlists')

@app.route('/playlist/<int:id>')
def playlist(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT songs.*
        FROM playlist_songs
        JOIN songs
        ON playlist_songs.song_id = songs.id
        WHERE playlist_songs.playlist_id=%s
    """, (id,))

    songs = cur.fetchall()

    cur.execute(
        "SELECT * FROM playlists WHERE id=%s",
        (id,)
    )

    playlist = cur.fetchone()

    cur.close()

    return render_template(
        'playlist.html',
        songs=songs,
        playlist=playlist
    )

@app.route('/select_playlist/<int:song_id>')
def select_playlist(song_id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM playlists WHERE username=%s",
        (session['user'],)
    )

    playlists = cur.fetchall()

    cur.close()

    return render_template(
        'select_playlist.html',
        playlists=playlists,
        song_id=song_id
    )

@app.route('/add_to_playlist/<int:song_id>/<int:playlist_id>')
def add_to_playlist(song_id, playlist_id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Check if song already exists
    cur.execute(
        """
        SELECT *
        FROM playlist_songs
        WHERE playlist_id=%s
        AND song_id=%s
        """,
        (playlist_id, song_id)
    )

    already = cur.fetchone()

    if not already:

        cur.execute(
            """
            INSERT INTO playlist_songs
            (playlist_id, song_id)
            VALUES(%s,%s)
            """,
            (playlist_id, song_id)
        )

        mysql.connection.commit()

    cur.close()

    return redirect('/playlist/' + str(playlist_id))

@app.route('/remove_from_playlist/<int:playlist_id>/<int:song_id>')
def remove_from_playlist(playlist_id, song_id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        DELETE FROM playlist_songs
        WHERE playlist_id=%s
        AND song_id=%s
        """,
        (playlist_id, song_id)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/playlist/' + str(playlist_id))

@app.route('/rename_playlist/<int:id>', methods=['GET', 'POST'])
def rename_playlist(id):

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM playlists WHERE id=%s AND username=%s",
        (id, session['user'])
    )

    playlist = cur.fetchone()

    if not playlist:
        cur.close()
        return redirect('/my_playlists')

    if request.method == 'POST':

        playlist_name = request.form['playlist_name']

        cur.execute(
            """
            UPDATE playlists
            SET playlist_name=%s
            WHERE id=%s
            """,
            (playlist_name, id)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/my_playlists')

    cur.close()

    return render_template(
        'rename_playlist.html',
        playlist=playlist
    )

@app.route('/recent_songs')
def recent_songs():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT songs.*
        FROM recent_songs
        JOIN songs
        ON recent_songs.song_id = songs.id
        WHERE recent_songs.username=%s
        ORDER BY recent_songs.id DESC
        LIMIT 20
    """, (session['user'],))

    songs = cur.fetchall()

    cur.close()

    return render_template(
        'recent_songs.html',
        songs=songs
    )

@app.route('/add_review/<int:song_id>', methods=['POST'])
def add_review(song_id):

    if 'user' not in session:
        return redirect('/login')

    rating = request.form['rating']
    comment = request.form['comment']

    cur = mysql.connection.cursor()

    # Check Existing Review

    cur.execute(
        """
        SELECT *
        FROM reviews
        WHERE username=%s
        AND song_id=%s
        """,
        (session['user'], song_id)
    )

    review = cur.fetchone()

    if review:

     cur.close()

    return redirect('/songs')

    # Insert Review

    cur.execute(
        """
        INSERT INTO reviews
        (username, song_id, rating, comment)
        VALUES(%s,%s,%s,%s)
        """,
        (session['user'], song_id, rating, comment)
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/songs')

@app.route('/download/<filename>')
def download_song(filename):

    if 'user' in session:

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO downloads
            (username, song_name)
            VALUES(%s,%s)
            """,
            (session['user'], filename)
        )

        mysql.connection.commit()
        cur.close()

    return send_from_directory(
        'static/songs',
        filename,
        as_attachment=True
    )

@app.route('/upload_profile', methods=['POST'])
def upload_profile():

    if 'user' not in session:
        return redirect('/login')

    image = request.files.get('profile_image')

    if image and image.filename != "":

        print("Uploaded File =", image.filename)
        print("Session User =", session['user'])

        image.save(
            os.path.join(
                'static/profile',
                image.filename
            )
        )

        cur = mysql.connection.cursor()

        cur.execute(
            """
            UPDATE users
            SET profile_image=%s
            WHERE username=%s
            """,
            (image.filename, session['user'])
        )

        mysql.connection.commit()

        print("Rows Updated =", cur.rowcount)

        cur.close()

    return redirect('/profile')

@app.route('/download_history')
def download_history():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT song_name
        FROM downloads
        WHERE username=%s
        ORDER BY id DESC
        """,
        (session['user'],)
    )

    downloads = cur.fetchall()

    cur.close()

    return render_template(
        'download_history.html',
        downloads=downloads
    )
    
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)