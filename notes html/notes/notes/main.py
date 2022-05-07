import requests
from flask import Flask, render_template, redirect
from flask_restful import reqparse, abort, Api, Resource
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.notes import Note
from data.users import User
from forms.note import NoteForm
from forms.user import RegisterForm, LoginForm
from resources import user_res, note_res

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'kotiki_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

# для одного объекта
api.add_resource(note_res.NoteResource, '/api/notes/<int:note_id>')

# для списка объектов
api.add_resource(note_res.NoteListResource, '/api/notes')

# для одного объекта
api.add_resource(user_res.UserResource, '/api/users/<int:user_id>')

# для списка объектов
api.add_resource(user_res.UserListResource, '/api/users')


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        notes = db_sess.query(Note).filter(
            (Note.user == current_user) | (Note.is_private != True))
    else:
        notes = db_sess.query(Note).filter(Note.is_private != True)
    return render_template("index.html", notes=notes)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не одинаковые")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже зарегистрирован")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Зарегистрироваться', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/note/add', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NoteForm()
    if form.validate_on_submit():
        requests.post('http://127.0.0.1:5000/api/notes', {
            'title': form.title.data,
            'content': form.content.data,
            'is_private': form.is_private.data,
            'user_id': current_user.id
        })
        return redirect('/')
    return render_template('news.html', title='Написать о чем-то новом',
                           form=form)


@app.route('/note/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_news(id):
    requests.delete('http://127.0.0.1:5000/api/notes/' + str(id))
    return redirect('/')


@app.route('/note/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_news(note_id):
    form = NoteForm()
    if form.validate_on_submit():
        requests.put('http://127.0.0.1:5000/api/notes/' + str(note_id),
                     {
                         'title': form.title.data,
                         'content': form.content.data,
                         'is_private': form.is_private.data,
                         'user_id': current_user.id
                     }
                     )
        return redirect('/')
    return render_template('news.html', title='Редактирование заметки',
                           form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    db_sess.commit()
    app.run()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


if __name__ == '__main__':
    main()
