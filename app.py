from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# ----------------------------------
# CONFIGURATION
# ----------------------------------

app.config['SECRET_KEY'] = 'ma_clef_secrete_flask'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/todo_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # page par défaut pour login_required


# ----------------------------------
# MODELES
# ----------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----------------------------------
# ROUTES
# ----------------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tasks")
@login_required
def tasks():
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("tasks.html", tasks=user_tasks)

@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    content = request.form["content"]
    new_task = Task(content=content, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/delete_task/<int:id>")
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("tasks"))

@app.route("/done_task/<int:id>")
@login_required
def done_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.is_done = True
        db.session.commit()
    return redirect(url_for("tasks"))


# ----------- INSCRIPTION -----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Ce nom d'utilisateur existe déjà."

        # Hash du mot de passe
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        # Création utilisateur
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# ----------- CONNEXION -----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            return "Identifiants invalides."

    return render_template("login.html")


# ----------- DECONNEXION -----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ----------------------------------
# LANCEMENT DE L'APPLICATION
# ----------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True)
