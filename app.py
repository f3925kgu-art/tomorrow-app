from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ===== 基本設定 =====
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===== モデル（データ構造） =====

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(100), unique=True, nullable=False)
    nickname = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    memo = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== ルート =====

@app.route("/")
@login_required
def index():
    ideas = Idea.query.filter_by(user_id=current_user.id).order_by(Idea.id.desc()).all()
    return render_template("index.html", ideas=ideas)

@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title")
    memo = request.form.get("memo")

    if title:
        idea = Idea(title=title, memo=memo, user_id=current_user.id)
        db.session.add(idea)
        db.session.commit()

    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        nickname = request.form.get("nickname")
        password = request.form.get("password")

        if User.query.filter_by(login_id=login_id).first():
            flash("そのIDはすでに使われています")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)

        user = User(login_id=login_id, nickname=nickname, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash("登録成功！ログインしてください")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        user = User.query.filter_by(login_id=login_id).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("ログイン失敗")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)