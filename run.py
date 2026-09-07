"""Development entrypoint: `python run.py`."""

import os

from app import create_app, db

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    from app.models.user import User
    from app.models.movie import Movie
    from app.models.review import Review
    from app.models.watch_history import WatchHistory
    from app.models.my_list import MyListEntry

    return {
        "db": db,
        "User": User,
        "Movie": Movie,
        "Review": Review,
        "WatchHistory": WatchHistory,
        "MyListEntry": MyListEntry,
    }


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", False))
