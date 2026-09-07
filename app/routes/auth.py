"""Authentication routes: register, login, logout, profile management."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not email or "@" not in email:
            errors.append("Please provide a valid email address.")
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to CineVault! Your account has been created.", "success")
        return redirect(url_for("main.index"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been disabled. Contact support.", "danger")
                return render_template("login.html")
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("main.index"))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip().lower()

            existing = User.query.filter(
                User.username == new_username, User.id != current_user.id
            ).first()
            if existing:
                flash("That username is already taken.", "danger")
            else:
                current_user.username = new_username
                current_user.email = new_email
                db.session.commit()
                flash("Profile updated successfully.", "success")

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_new_password = request.form.get("confirm_new_password", "")

            if not current_user.check_password(current_password):
                flash("Current password is incorrect.", "danger")
            elif len(new_password) < 8:
                flash("New password must be at least 8 characters long.", "danger")
            elif new_password != confirm_new_password:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash("Password changed successfully.", "success")

        elif action == "delete_account":
            user = User.query.get(current_user.id)
            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash("Your account has been deleted.", "info")
            return redirect(url_for("main.index"))

        return redirect(url_for("auth.profile"))

    return render_template("profile.html")
