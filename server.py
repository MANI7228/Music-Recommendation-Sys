from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import cv2, base64, random, sqlite3, os
import numpy as np
from fer import FER

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Ensure database folder exists
if not os.path.exists("database"):
    os.makedirs("database")

# Init database
def init_db():
    conn = sqlite3.connect("database/users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT,
                    age INTEGER,
                    gender TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# FER Detector
detector = FER(mtcnn=True)

# ================= INTRO =================
@app.route("/")
def intro():
    return render_template("intro.html")

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        age = request.form.get("age")
        gender = request.form.get("gender")

        conn = sqlite3.connect("database/users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email, password, age, gender) VALUES (?, ?, ?, ?)",
                      (email, password, age, gender))
            conn.commit()
            flash("✅ Signup successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("⚠️ Email already registered!", "error")
        conn.close()
    return render_template("signup.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database/users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email
            flash("✅ Login successful!", "success")
            return redirect(url_for("recommend"))
        else:
            flash("❌ Invalid email or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ================= RECOMMEND PAGE =================
@app.route("/recommend")
def recommend():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("recommend.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("login"))

# ================= SONGS =================
mood_to_songs = {
    "happy": [
        {"name": "Happy", "singer": "Pharrell Williams", "spotify_url": "https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH"},
        {"name": "Uptown Funk", "singer": "Bruno Mars", "spotify_url": "https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS"},
        {"name": "Can’t Stop the Feeling", "singer": "Justin Timberlake", "spotify_url": "https://open.spotify.com/track/6JV2JOEocMgcZxYSZelKcc"},
        {"name": "Good Life", "singer": "OneRepublic", "spotify_url": "https://open.spotify.com/track/6OtCIsQZ64Vs1EbzztvAv4"},
        {"name": "Shake It Off", "singer": "Taylor Swift", "spotify_url": "https://open.spotify.com/track/5xTtaWoae3wi06K5WfVUUH"},
        {"name": "I Gotta Feeling", "singer": "Black Eyed Peas", "spotify_url": "https://open.spotify.com/track/4bHsxqR3GMrXTxEPLuK5ue"},
        {"name": "On Top of the World", "singer": "Imagine Dragons", "spotify_url": "https://open.spotify.com/track/6KuHjfXHkfnIjdmcIvt9r0"},
        {"name": "Best Day of My Life", "singer": "American Authors", "spotify_url": "https://open.spotify.com/track/5Hroj5K7vLpIG4FNCRIjbP"},
        {"name": "Sugar", "singer": "Maroon 5", "spotify_url": "https://open.spotify.com/track/494OU6M7NOf4ICYb4zWCf5"},
        {"name": "Firework", "singer": "Katy Perry", "spotify_url": "https://open.spotify.com/track/4jCj0C5eaM3yTQpYJ1dHzT"},
    ],
    "sad": [
        {"name": "Someone Like You", "singer": "Adele", "spotify_url": "https://open.spotify.com/track/4kflIGfjdZJW4ot2ioixTB"},
        {"name": "Let Her Go", "singer": "Passenger", "spotify_url": "https://open.spotify.com/track/2jyjhRf6DVbMPU5zxagN2h"},
        {"name": "Fix You", "singer": "Coldplay", "spotify_url": "https://open.spotify.com/track/7LVHVU3tWfcxj5aiPFEW4Q"},
        {"name": "Stay With Me", "singer": "Sam Smith", "spotify_url": "https://open.spotify.com/track/3jjujdWJ72nww5eGnfs2E7"},
        {"name": "When I Was Your Man", "singer": "Bruno Mars", "spotify_url": "https://open.spotify.com/track/0nJW01T7XtvILxQgC5J7Wh"},
        {"name": "All I Want", "singer": "Kodaline", "spotify_url": "https://open.spotify.com/track/0MlTOiC5ZYKFGeZ8h3D4rd"},
        {"name": "Say Something", "singer": "A Great Big World", "spotify_url": "https://open.spotify.com/track/2aBxt229cbLDOvtL7Xbb9x"},
        {"name": "The Night We Met", "singer": "Lord Huron", "spotify_url": "https://open.spotify.com/track/0sQLhU6sAuQG2iJQyF4kOx"},
        {"name": "Jealous", "singer": "Labrinth", "spotify_url": "https://open.spotify.com/track/3dT4hzxwPjKYQxDq2AvivO"},
        {"name": "With or Without You", "singer": "U2", "spotify_url": "https://open.spotify.com/track/5J4PZby3pi0wfQWmVHg6Y7"},
    ],
    "angry": [
        {"name": "In The End", "singer": "Linkin Park", "spotify_url": "https://open.spotify.com/track/60a0Rd6pjrkxjPbaKzXjfq"},
        {"name": "Break Stuff", "singer": "Limp Bizkit", "spotify_url": "https://open.spotify.com/track/5UoFrZbjWKQUn0KPLWgwhT"},
        {"name": "Killing In The Name", "singer": "RATM", "spotify_url": "https://open.spotify.com/track/4u7EnebtmKWzUH433cf5Qv"},
        {"name": "Smells Like Teen Spirit", "singer": "Nirvana", "spotify_url": "https://open.spotify.com/track/5ghIJDpPoe3CfHMGu71E6T"},
        {"name": "Duality", "singer": "Slipknot", "spotify_url": "https://open.spotify.com/track/6QgjcU0zLnzq5OrUoSZ3OK"},
        {"name": "Down With The Sickness", "singer": "Disturbed", "spotify_url": "https://open.spotify.com/track/2DlHlPMa4M17kufBvI2lEN"},
        {"name": "Enter Sandman", "singer": "Metallica", "spotify_url": "https://open.spotify.com/track/5sICkBXVmaCQk5aISGR3x1"},
        {"name": "Bulls on Parade", "singer": "RATM", "spotify_url": "https://open.spotify.com/track/4oN6KR2hAm5JTYo5kxv8aD"},
        {"name": "Bodies", "singer": "Drowning Pool", "spotify_url": "https://open.spotify.com/track/5r6Vi8ghsl7W95Y0UHMgCy"},
        {"name": "Faint", "singer": "Linkin Park", "spotify_url": "https://open.spotify.com/track/5w3slHyJp3ihX5mymXy4pM"},
    ],
    "neutral": [
        {"name": "Shape of You", "singer": "Ed Sheeran", "spotify_url": "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"},
        {"name": "Counting Stars", "singer": "OneRepublic", "spotify_url": "https://open.spotify.com/track/2tpWsVSb9UEmDRxAl1zhX1"},
        {"name": "Rolling in the Deep", "singer": "Adele", "spotify_url": "https://open.spotify.com/track/4OSBTYWVwsQhGLF9NHvIbR"},
        {"name": "Perfect", "singer": "Ed Sheeran", "spotify_url": "https://open.spotify.com/track/0tgVpDi06FyKpA1z0VMD4v"},
        {"name": "Photograph", "singer": "Ed Sheeran", "spotify_url": "https://open.spotify.com/track/1HNkqx9Ahdgi1Ixy2xkKkL"},
        {"name": "Hall of Fame", "singer": "The Script", "spotify_url": "https://open.spotify.com/track/0jQpzzUwC8FrQ1Z21aWztN"},
        {"name": "Cheap Thrills", "singer": "Sia", "spotify_url": "https://open.spotify.com/track/4pNApnaUWAL2J4KO2eqokq"},
        {"name": "Stay", "singer": "Rihanna", "spotify_url": "https://open.spotify.com/track/2gZUPNdnz5Y45eiGxpHGSc"},
        {"name": "A Sky Full of Stars", "singer": "Coldplay", "spotify_url": "https://open.spotify.com/track/2sSyjEshk5U1S4nTbB4ShJ"},
        {"name": "Memories", "singer": "Maroon 5", "spotify_url": "https://open.spotify.com/track/2NmsngXHeC1GQ9wWrzhOMf"},
    ],
    "surprise": [
        {"name": "Believer", "singer": "Imagine Dragons", "spotify_url": "https://open.spotify.com/track/0pqnGHJpmpxLKifKRmU6WP"},
        {"name": "Thunder", "singer": "Imagine Dragons", "spotify_url": "https://open.spotify.com/track/1zB4vmk8tFRmM9UULNzbLB"},
        {"name": "Stronger", "singer": "Kanye West", "spotify_url": "https://open.spotify.com/track/5D4cdSZ6f3j2cGl9LJZNlU"},
        {"name": "Titanium", "singer": "David Guetta", "spotify_url": "https://open.spotify.com/track/45wXjjX9g4BTQoyKp7jGxm"},
        {"name": "Wake Me Up", "singer": "Avicii", "spotify_url": "https://open.spotify.com/track/0nrRP2bk19rLc0orkWPQk2"},
        {"name": "Fireflies", "singer": "Owl City", "spotify_url": "https://open.spotify.com/track/2VxeLyX666F8uXCJ0dZF8B"},
        {"name": "Radioactive", "singer": "Imagine Dragons", "spotify_url": "https://open.spotify.com/track/4G8gkOterJn0Ywt6uhqbhp"},
        {"name": "We Found Love", "singer": "Rihanna", "spotify_url": "https://open.spotify.com/track/4KBeYlgkHhGXlDUl9RrY5e"},
        {"name": "On The Floor", "singer": "Jennifer Lopez", "spotify_url": "https://open.spotify.com/track/2KsP6tYLJlTBvSUxnwlVWa"},
        {"name": "Stronger (What Doesn’t Kill You)", "singer": "Kelly Clarkson", "spotify_url": "https://open.spotify.com/track/7o7E1r7hMaS8mx3v0xkhOm"},
    ]
}

# ================= APIs =================
@app.route("/detect_mood", methods=["POST"])
def detect_mood():
    try:
        data = request.json['image']
        img_data = base64.b64decode(data.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        results = detector.detect_emotions(frame)
        mood = "neutral"
        if results:
            emotions = results[0]["emotions"]
            mood = max(emotions, key=emotions.get)

        songs = random.sample(mood_to_songs[mood], k=4)
        return jsonify({"mood": mood, "songs": songs})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/emoji_recommend", methods=["POST"])
def emoji_recommend():
    try:
        data = request.json
        emoji = data.get("emoji")

        emoji_to_mood = {
            "😊": "happy",
            "😢": "sad",
            "😡": "angry",
            "😲": "surprise",
            "🙂": "neutral"
        }

        mood = emoji_to_mood.get(emoji, "neutral")
        songs = random.sample(mood_to_songs[mood], k=4)
        return jsonify({"mood": mood, "songs": songs})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
