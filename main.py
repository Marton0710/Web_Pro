from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os

class RegisterForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired()])
    password = PasswordField("密码", validators=[DataRequired()])
    checkPassword = PasswordField("确认密码", validators=[DataRequired()])
    sex = SelectField("性别", choices=["男", "女", "保密"])
    submit = SubmitField("填写完毕，立即注册")

class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired()])
    password = PasswordField("密码", validators=[DataRequired()])
    submit = SubmitField("确认无误，立即登录")

class PostForm(FlaskForm):  #帖子表单
    title = StringField("主题", validators=[DataRequired()])
    content = TextAreaField("内容", validators=[DataRequired()])
    submit = SubmitField("确认无误，发布")

class CommentForm(FlaskForm):  #评论表单
    comment = TextAreaField("评论", validators=[DataRequired()])
    submit = SubmitField("发表")

class DetailForm(FlaskForm):  #个人资料表单
    sex = SelectField("性别", choices=["男", "女", "保密"])
    email = StringField("邮箱")
    address = StringField("地址")
    info = TextAreaField("个人简介")
    submit = SubmitField("确认无误，修改资料")

class AvatarForm(FlaskForm):  #头像表单
    avatarFile = FileField("个人头像", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", "jpeg"])])
    submit = SubmitField("提交上传头像")

class Photos(FlaskForm):  #图片表单
    photoFile = FileField("上传所需图片", validators=[FileRequired(), FileAllowed(["jpg", "png", "gif", "jpeg"])])
    submit = SubmitField("提交图片")


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SECRET_KEY"] = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)

class User(db.Model):  #用户模型
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(16), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True, default="无")
    address = db.Column(db.String(50), nullable=True, default="无")
    info = db.Column(db.String(100), nullable=True, default="快来介绍一下自己吧...")  #个人信息
    avatar = db.Column(db.String(100), nullable=True)  #头像
    flag_admit = db.Column(db.Boolean, default=False)  #后台管理权限
    flag_edit = db.Column(db.Boolean, default=True)  #编辑权限
    flag_kill = db.Column(db.Boolean, default=False)  #是否封禁
    posts = db.relationship("Post", backref="author")
                    #与帖子表反向建立联系，author可以代替author_id访问User
    comments = db.relationship('Comment', backref='author')
                    #与评论表反向建立联系，author可以代替author_id访问User

class Post(db.Model):  #帖子模型
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))  #与用户表建立联系
    comments = db.relationship('Comment', backref='post')
                    #与评论表反向建立联系，post可以代替post_id访问Post
 
class Comment(db.Model):  #评论模型
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Photo(db.Model):  #图片模型
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=True, unique=True)
    create_time = db.Column(db.DateTime, default=datetime.now)


@app.route("/")  #首页
def index():
    photos = Photo.query.all()
    try:
        photo = random.sample(photos, 1)[0]
        return render_template("index.html", photo_address=photo.address)
    except:
        return render_template("index.html", photo_address="../static/avatar/xiaohui.png")


@app.route("/admit")  #网站管理
def admit():
    user_id = session.get("user_id")
    if user_id:
        if User.query.filter(User.id == user_id).first().flag_admit == 1:
            users = User.query.all()
            photos = Photo.query.all()
            return render_template("admit.html", users=users, photos=photos)
        return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])  #注册
def register():
    form = RegisterForm()
    if request.method.upper() == "GET":
        return render_template("register.html", form=form)
    else:
        username = form.username.data
        password = form.password.data
        checkPassword = form.checkPassword.data
        sex = form.sex.data
        if User.query.filter(User.username == username).first():
            return "<h1>该用户已注册，请重新<a href='/register'>注册</h1>"
        else:
            if password != checkPassword:
                return "<h1>密码不一致，请重新填写</h1>"
            else:
                new_user = User(username=username, password=password, sex=sex)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])  #登录
def login():
    form = LoginForm()
    if request.method.upper() == "GET":
        return render_template("login.html", form=form)
    else:
        username = form.username.data
        password = form.password.data
        user = User.query.filter(User.username == username).first()
        if user:
            if user.flag_kill == 0:
                if password == user.password:
                    session["user_id"] = user.id  #保存到session，相当于全局容器
                    session.permanent = True  #最长保存31天
                    return redirect(url_for("index"))
                else:
                    return "<h1>密码错误，请重新<a href='/login'>登录</a></h1>"
            else:
                return "<h1>账户已封禁，请告知管理员以解封</h1>"
        else:
            return "<h1>用户名错误，请重新<a href='/login'>登录</a></h1>"


@app.route("/logout")  #退出
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/community")  #社区
def community():
    if session.get("user_id"):
        posts = Post.query.all()
        return render_template("community.html", posts=posts)
    else:
        return redirect(url_for("login"))


@app.route("/postEdit", methods=["GET", "POST"])  #发布帖子
def postEdit():
    user_id = session.get("user_id")
    if user_id:
        if User.query.filter(User.id == user_id).first().flag_edit == 1:
            form = PostForm()
            if request.method.upper() == "GET":
                return render_template("postEdit.html", form=form)
            else:
                title = form.title.data
                content = form.content.data
                post = Post(title=title, content=content)
                post.author_id = session.get("user_id")
                db.session.add(post)
                db.session.commit()
                return redirect(url_for("community"))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))
    

@app.route("/comment/<post_id>", methods=["GET", "POST"])  #评论，comment.html为详情+评论
def comment(post_id):
    if session.get("user_id"):
        form = CommentForm()
        if request.method.upper() == "GET":
            post = Post.query.filter(Post.id == post_id).first()
            return render_template("comment.html", form=form, post=post)
        else:
            comment = Comment(content=form.comment.data)
            comment.post_id = post_id
            comment.author_id = session.get("user_id")
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("comment", post_id=post_id))
    else:
        return redirect(url_for("login"))
    

@app.route("/delete_post/<post_id>")  #删除帖子及其附属评论
def delete_post(post_id):
    if session.get("user_id"):
        post = Post.query.filter(Post.id == post_id).first()
        if session.get("user_id") == int(post.author.id):
            comments = Comment.query.filter(Comment.post_id == post_id).all()
            for comment in comments:
                db.session.delete(comment)
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for("community"))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))
    

@app.route("/delete_comment/<comment_id>")  #删除评论
def delete_comment(comment_id):
    if session.get("user_id"):
        comment = Comment.query.filter(Comment.id == comment_id).first()
        if session.get("user_id") == int(comment.author_id):
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for("comment", post_id=comment.post_id))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/delete_photo/<photo_id>")  #删除图片
def delete_photo(photo_id):
    user_id = session.get("user_id")
    if user_id:
        if User.query.filter(User.id == user_id).first().flag_admit == 1:
            try:
                photo = Photo.query.filter(Photo.id == photo_id).first()
                db.session.delete(photo)
                db.session.commit()
                os.remove(photo.address)
                return redirect(url_for("admit"))
            except:
                return redirect(url_for("admit"))
        return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/user_detail/<user_id>")  #个人中心
def user_detail(user_id):
    if session.get("user_id"):
        user = User.query.filter(User.id == user_id).first()
        return render_template("user_detail.html", user=user)
    else:
        return redirect(url_for("login"))
    

@app.route("/edit_detail/<user_id>", methods=["GET", "POST"])  #编辑个人资料
def edit_detail(user_id):
    if session.get("user_id"):
        if session.get("user_id") == int(user_id):  #user_id原本为str
            form = DetailForm()
            if request.method.upper() == "GET":
                return render_template("edit_detail.html", form=form)
            else:
                user = User.query.filter(User.id == user_id).first()
                user.sex = form.sex.data
                user.email = form.email.data
                user.address = form.address.data
                user.info = form.info.data
                db.session.commit()
                return redirect(url_for("user_detail", user_id=user_id))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/edit_avatar/<user_id>", methods=["GET", "POST"])  #编辑头像
def edit_avatar(user_id):
    if session.get("user_id"):
        if session.get("user_id") == int(user_id):
            form = AvatarForm()
            if request.method.upper() == "GET":
                return render_template("edit_avatar.html", form=form)
            else:
                file = request.files["avatarFile"]  #获取文件
                file.save(f"E:\\VsCode_Project\\Python\\Web_Pro\\static\\avatar\\{file.filename}")
                user = User.query.filter(User.id == user_id).first()
                user.avatar = file.filename
                db.session.commit()
                return redirect(url_for("user_detail", user_id=user.id))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))
    

@app.route("/uploads_photo", methods=["GET", "POST"])  #上传图片
def uploads_photo():
    user_id = session.get("user_id")
    if user_id:
        if User.query.filter(User.id == user_id).first().flag_admit == 1:
            if request.method.upper() == "GET":
                form = Photos()
                return render_template("uploads_photo.html", form=form)
            else:
                file = request.files["photoFile"]  #获取文件
                file.save(f"E:\\Vscode_Project\\Python\\Web_Pro\\static\\photo\\{file.filename}")
                photo  = Photo(address=(f"../static/photo/{file.filename}"))
                try:
                    db.session.add(photo)
                    db.session.commit()
                except:
                    return redirect(url_for("uploads_photo"))
                return redirect(url_for("uploads_photo"))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("login"))


@app.route("/flag_kill/<wheater>/<user_id>")  #封禁用户
def flag_kill(wheater, user_id):
    user_id_s = session.get("user_id")
    if user_id_s:
        user_f = User.query.filter(User.id == user_id_s).first() #验证admit
        if user_f.flag_admit == 1:
            user = User.query.filter(User.id == user_id).first()
            if int(wheater) == 0:
                user.flag_kill = 1
            elif int(wheater) == 1:
                user.flag_kill = 0
            db.session.commit()
            return redirect(url_for("admit"))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/flag_edit/<wheater>/<user_id>")  #编辑权限
def flag_edit(wheater, user_id):
    user_id_s = session.get("user_id")
    if user_id_s:
        user_f = User.query.filter(User.id == user_id_s).first() #验证admit
        if user_f.flag_admit == 1:
            user = User.query.filter(User.id == user_id).first()
            if int(wheater) == 0:
                user.flag_edit = 1
            elif int(wheater) == 1:
                user.flag_edit = 0
            db.session.commit()
            return redirect(url_for("admit"))
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/about")  #关于
def about():
    return render_template("about.html")


@app.errorhandler(404)  #错误处理
def not_found_template(text):
    return render_template("404.html", text=text)


@app.context_processor  #上下文处理器，任何页面都可使用其中的变量
def context():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.filter(User.id == user_id).first()  #找到哪个用户登录
        if user:
            return {"um": user}
    return {}


if __name__ == "__main__":
    # with app.app_context():
    #     db.drop_all()
    #     db.create_all()
    app.run(debug=True)
