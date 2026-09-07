"""
Seed the database with a demo admin account and ~20 fictional movies.

Usage:
    python scripts/seed.py

All movie metadata below is fictional. Poster/backdrop images point to
placeholder image services and video URLs point to small, freely
licensed sample clips (Google's public Big Buck Bunny/Sintel test
streams) so the app is watchable out of the box without any pirated
content.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.movie import Movie

# Freely licensed open sample videos (used only as stand-ins for demo content)
SAMPLE_VIDEO_A = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
SAMPLE_VIDEO_B = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"

MOVIES = [
    dict(title="The Last Horizon", genre="Sci-Fi,Drama", release_year=2023, duration_minutes=128,
         director="Elena Vasquez", cast="Marcus Reid, Talia Nkomo, Jonah Kirk",
         description="A deep-space crew races to reach the last habitable horizon before their ship's reactor fails.",
         age_rating="PG-13", is_trending=True, is_featured=True),
    dict(title="Neon City", genre="Action,Thriller", release_year=2022, duration_minutes=110,
         director="Kai Osei", cast="Renee Park, Adrian Boone, Miku Sato",
         description="An undercover detective infiltrates a neon-lit megacity's underworld to stop a data heist.",
         age_rating="R", is_trending=True),
    dict(title="Beyond the Stars", genre="Sci-Fi,Adventure", release_year=2021, duration_minutes=142,
         director="Priya Chandran", cast="Owen Ashford, Nadia Petrova",
         description="Humanity's first interstellar colonists discover their new home isn't as empty as it seemed.",
         age_rating="PG-13"),
    dict(title="Midnight Protocol", genre="Thriller,Sci-Fi", release_year=2024, duration_minutes=118,
         director="Marcus Lee", cast="Sofia Reyes, Damon Cole",
         description="A rogue AI analyst uncovers a conspiracy hidden inside her own company's source code.",
         age_rating="PG-13", is_trending=True),
    dict(title="Code Zero", genre="Action,Sci-Fi", release_year=2020, duration_minutes=101,
         director="Yuki Tanaka", cast="Leo Bennett, Aria Fontaine",
         description="A hacker turned soldier must shut down a rogue military program before it goes live.",
         age_rating="R"),
    dict(title="Shadow District", genre="Thriller,Drama", release_year=2019, duration_minutes=124,
         director="Isabel Duarte", cast="Noah Whitfield, Camille Laurent",
         description="A detective's investigation into a string of disappearances leads to her own family's past.",
         age_rating="R"),
    dict(title="The Final Signal", genre="Sci-Fi,Thriller", release_year=2023, duration_minutes=115,
         director="Tomas Berg", cast="Ines Alvarado, Felix Grant",
         description="When Earth receives one last transmission from a lost colony ship, a rescue team is sent to investigate.",
         age_rating="PG-13"),
    dict(title="Crimson Ledger", genre="Drama,Thriller", release_year=2022, duration_minutes=132,
         director="Grace Okafor", cast="Victor Hale, Mei Lin",
         description="A forensic accountant unravels a decade of corporate fraud that reaches the top of her firm.",
         age_rating="PG-13"),
    dict(title="Wildfire Season", genre="Drama", release_year=2021, duration_minutes=108,
         director="Hannah Reed", cast="Diego Marin, Charlotte Bishop",
         description="Two estranged siblings reunite to save their family's ranch from an encroaching wildfire.",
         age_rating="PG-13"),
    dict(title="Laugh Track", genre="Comedy", release_year=2023, duration_minutes=97,
         director="Sam Okonkwo", cast="Bella Ruiz, Trevor Nash",
         description="A washed-up sitcom writer gets one last shot when his old show is rebooted by an intern.",
         age_rating="PG-13", is_trending=True),
    dict(title="Best Man Bailout", genre="Comedy,Romance", release_year=2020, duration_minutes=102,
         director="Nina Castillo", cast="Ryan Delacroix, Priya Anand",
         description="A disaster of a bachelor party spirals into a cross-country road trip nobody signed up for.",
         age_rating="R"),
    dict(title="Office Hours", genre="Comedy", release_year=2019, duration_minutes=93,
         director="Malik Johnson", cast="Ellie Sanders, Chris Obi",
         description="A chaotic week at a failing startup forces its mismatched staff to finally work together.",
         age_rating="PG-13"),
    dict(title="Quiet Harbor", genre="Drama,Romance", release_year=2022, duration_minutes=119,
         director="Astrid Lindqvist", cast="Julian Moss, Fatima Rahman",
         description="A widowed lighthouse keeper's quiet life changes when a stranger washes ashore.",
         age_rating="PG-13"),
    dict(title="Paper Hearts", genre="Romance,Drama", release_year=2021, duration_minutes=105,
         director="Claire Dubois", cast="Amara Blake, Theo Winters",
         description="Two rival letter-writing pen pals fall for each other without realizing who's on the other end.",
         age_rating="PG"),
    dict(title="Hollow Point", genre="Action,Thriller", release_year=2024, duration_minutes=121,
         director="Derek Vance", cast="Nikolai Petrov, Sasha Rowe",
         description="A retired sniper is pulled back in for one last job that turns into a trap.",
         age_rating="R", is_trending=True),
    dict(title="The Cartographer's Wife", genre="Drama,History", release_year=2018, duration_minutes=136,
         director="Beatriz Nunes", cast="Henry Ashcombe, Lucia Ferreira",
         description="In the age of exploration, a mapmaker's wife secretly redraws the borders of her own fate.",
         age_rating="PG-13"),
    dict(title="Static", genre="Horror,Thriller", release_year=2023, duration_minutes=99,
         director="Jordan Vance", cast="Maya Ellison, Peter Kwan",
         description="A late-night radio host starts receiving calls from a station that stopped broadcasting decades ago.",
         age_rating="R", is_trending=True),
    dict(title="The Hollow House", genre="Horror", release_year=2020, duration_minutes=104,
         director="Rosa Mendez", cast="Caleb Storm, Ivy Chen",
         description="A family renovating an old farmhouse discovers renovations aren't the only thing changing the walls.",
         age_rating="R"),
    dict(title="Glass Kingdom", genre="Fantasy,Adventure", release_year=2022, duration_minutes=140,
         director="Oskar Lindberg", cast="Freya Solberg, Amir Farouk",
         description="A blacksmith's apprentice discovers she's the last heir to a shattered magical kingdom.",
         age_rating="PG-13"),
    dict(title="Nightshift Diner", genre="Drama,Comedy", release_year=2021, duration_minutes=96,
         director="Toni Alvarez", cast="Gabriel Ross, Simone Okeke",
         description="One long night at an all-night diner brings together strangers whose lives are about to collide.",
         age_rating="PG-13"),
]


def run() -> None:
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        db.create_all()

        admin_email = app.config["ADMIN_EMAIL"]
        admin_password = app.config["ADMIN_PASSWORD"]

        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(username="admin", email=admin_email, role=UserRole.ADMIN)
            admin.set_password(admin_password)
            db.session.add(admin)
            print(f"Created admin user: {admin_email}")
        else:
            print(f"Admin user already exists: {admin_email}")

        demo_user = User.query.filter_by(email="demo@example.com").first()
        if not demo_user:
            demo_user = User(username="demo", email="demo@example.com", role=UserRole.USER)
            demo_user.set_password("demopassword123")
            db.session.add(demo_user)
            print("Created demo user: demo@example.com / demopassword123")

        created_count = 0
        for index, movie_data in enumerate(MOVIES):
            existing = Movie.query.filter_by(title=movie_data["title"]).first()
            if existing:
                continue

            video_url = SAMPLE_VIDEO_A if index % 2 == 0 else SAMPLE_VIDEO_B
            seed_num = (index % 40) + 1
            movie = Movie(
                title=movie_data["title"],
                description=movie_data["description"],
                release_year=movie_data["release_year"],
                duration_minutes=movie_data["duration_minutes"],
                genre=movie_data["genre"],
                language="English",
                age_rating=movie_data.get("age_rating", "PG-13"),
                cast=movie_data["cast"],
                director=movie_data["director"],
                poster_url=f"https://picsum.photos/seed/cinevault-poster-{seed_num}/400/600",
                backdrop_url=f"https://picsum.photos/seed/cinevault-backdrop-{seed_num}/1600/700",
                video_url=video_url,
                trailer_url=video_url,
                is_trending=movie_data.get("is_trending", False),
                is_featured=movie_data.get("is_featured", False),
                view_count=(len(MOVIES) - index) * 17,
            )
            db.session.add(movie)
            created_count += 1

        db.session.commit()
        print(f"Seeded {created_count} new movies. Total movies in DB: {Movie.query.count()}")


if __name__ == "__main__":
    run()
