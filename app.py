from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ===== 基本設定 =====
# SECRET_KEY（ログイン状態を守るカギ）：本番は環境変数、ローカルは仮の値
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# DB（データ置き場）：いまはSQLite（後でPostgresにする）
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# ✅ テーブル作成（本番でもローカルでも、起動時に必要なら作る）
with app.app_context():
    db.create_all()

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
    title = request.form.get("title", "").strip()
    memo = request.form.get("memo", "").strip()

    if title:
        idea = Idea(title=title, memo=memo, user_id=current_user.id)
        db.session.add(idea)
        db.session.commit()
    else:
        flash("タイトルは空にできません")

    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip()
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "").strip()

        if not login_id or not nickname or not password:
            flash("未入力があります（ID/ニックネーム/パスワード）")
            return redirect(url_for("register"))

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
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(login_id=login_id).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("ログイン失敗（IDかパスワードが違います）")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)