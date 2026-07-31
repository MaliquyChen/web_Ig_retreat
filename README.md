# 📸 Interactive Instagram Event Web Application

An interactive simulated Instagram web application for offline events, mystery games, and character-based audience engagement.

## 🚀 Features

1. **Mobile Post Scanning Page (`/post?character_id=<ID>`)**
   - Simulated Instagram New Post modal UI.
   - Pre-configured character header & avatar (`Detective Sherlock`, `Phantom Thief`, `Cyber Hacker V`).
   - Image upload supporting direct camera capture or mobile photo gallery.
   - Caption input with instant hashtag quick-pills (`#Event2026`, `#MysteryClue`, etc.).
   - Asynchronous AJAX upload with loading feedback & success toasts.

2. **Big Screen Instagram Profile Page (`/screen?character_id=<ID>`)**
   - Simulated Instagram official profile page with character avatar, handle, bio, follower count, and post stats.
   - **Responsive 3-Column 1:1 Square Grid** layout displaying all submitted posts.
   - **Auto-Refresh Engine**: Polling mechanism every 10 seconds without full-page refresh.
   - **Interactive Lightbox Modal**: Click any post thumbnail to inspect full-res photo, full caption text, timestamps, and click the heart icon to like posts in real-time!

3. **Event Host Control Center (`/`)**
   - Quick launch buttons for all character post creation pages & screen views.
   - Simple testing directory for event staff.

---

## 🛠️ Technical Stack

- **Backend:** Python (Flask)
- **Database:** SQLite (`database.db`, auto-initialized with sample data)
- **Frontend:** HTML5, CSS3 (Custom Instagram design system with Light/Dark mode), Vanilla JavaScript
- **Deployment:** Render-ready with `Procfile` & `gunicorn`

---

## 📂 Project Structure

```
IG/
├── app.py                      # Flask backend API & SQLite setup
├── database.db                 # SQLite database (auto created)
├── requirements.txt            # Python dependencies
├── Procfile                    # Render/Gunicorn deployment entry
├── README.md                   # Documentation
├── static/
│   ├── css/
│   │   └── style.css           # Instagram UI design system & modal styling
│   ├── js/
│   │   └── app.js              # DOM, AJAX post submit, polling & lightbox logic
│   ├── avatars/                # Character avatars (detective, thief, hacker SVGs)
│   └── uploads/                # Directory for user-submitted post images
└── templates/
    ├── index.html              # Host Control Hub & QR links
    ├── post.html               # Mobile Post Creation (/post?character_id=...)
    └── screen.html             # Big Screen Profile (/screen?character_id=...)
```

---

## 🏃 Running Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python app.py
   ```

3. **Open in browser:**
   - **Host Hub:** `http://127.0.0.1:5000/`
   - **Mobile Post (Sherlock):** `http://127.0.0.1:5000/post?character_id=char_1`
   - **Mobile Post (Phantom Thief):** `http://127.0.0.1:5000/post?character_id=char_2`
   - **Big Screen Profile (Sherlock):** `http://127.0.0.1:5000/screen?character_id=char_1`
   - **Big Screen Profile (All Feeds):** `http://127.0.0.1:5000/screen?character_id=all`

---

## 🌐 Deploying to Render

1. Push your repository to GitHub / GitLab.
2. Log into [Render](https://render.com) and click **New + -> Web Service**.
3. Connect your repository.
4. Set the build parameters:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Create Web Service**. Your app will be live with HTTPS!

---

## 📱 Generating QR Codes for the Event

For your offline event, generate QR codes pointing to:
- QR Code A: `https://<your-render-domain>/post?character_id=char_1`
- QR Code B: `https://<your-render-domain>/post?character_id=char_2`
- QR Code C: `https://<your-render-domain>/post?character_id=char_3`
