# ---IMPORTS SECTION---
from flask import Flask,render_template,request,url_for
import requests
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField  
from wtforms.validators import DataRequired,Length,Regexp,Email  
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column 
from sqlalchemy import Integer, String
import os
import mailtrap as mt

#---CONSTANTS SECTION---
SENDER=os.environ.get("SENDER")
PW=os.environ.get("PW")

smtp_server = 'smtp.gmail.com'
smtp_port = 465
sender_email = SENDER
sender_password = PW 
context = ssl.create_default_context()

email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

#Contact form
class ContactForm(FlaskForm):
    fullname = StringField(label="Full Name",
                           name="fullname",
                           render_kw={'placeholder': 'Full Name'},
                           validators=[DataRequired()])
    email = StringField(label="Email",
                        name="email",
                        render_kw={'placeholder': 'Email'},
                        validators=[DataRequired(),Regexp(regex=email_pattern, message="Not a valid email")])
    phone = StringField(label="Phone number",
                        name="phone",
                        render_kw={'placeholder': 'Phone number'},
                        validators=[DataRequired(),Length(min=10,max=10,message="Phone number should be 10 digits")])
    subject =StringField(label="Subject",
                         name="subject",
                         render_kw={'placeholder': 'Subject'},
                         validators=[DataRequired()])
    message = TextAreaField(label="message",
                            render_kw={'rows': 10, 'cols': 30,'placeholder': 'Your Message'})
    submit = SubmitField(label="Send Message",
                         render_kw={'class':'btn'})
    
#--- DB DECLARATION ---
class Base(DeclarativeBase):
    pass

db=SQLAlchemy(model_class=Base)
        
app = Flask(__name__)
app.secret_key = os.environ.get("sec")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI","sqlite:///portfolio-database.db")

db.init_app(app)

class ContactDetails(db.Model):
    Id : Mapped[int] = mapped_column(Integer, primary_key=True)
    Name : Mapped[str] = mapped_column(String(250), nullable=False)
    Email : Mapped[str] = mapped_column(String(250),nullable=False)
    Phone : Mapped[str] = mapped_column(String(11), nullable=False)
    Subject : Mapped[str] = mapped_column(String(250), nullable=False)
    Message : Mapped[str] = mapped_column(String(400))
    
    def __repr__(self):
        return f'<id. {self.Name}>'
    
with app.app_context():
    db.create_all()

# CREATE ROW
def create_row(fullname,email,phone,subject,message):
    with app.app_context():
        new_user = ContactDetails(Name=fullname,
                                  Email=email,
                                  Phone=phone,
                                  Subject=subject,
                                  Message=message)
        db.session.add(new_user)
        db.session.commit()
    
# SEND MAIL
# def send_mail(name, email, phone, subject, message):
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = sender_email
#     msg['Subject'] = subject
#     body = f"Subject: {subject}\n\n Name: {name}\n Email: {email}\n Phone: {phone}\n Message: {message}"
#     msg.attach(MIMEText(body, 'plain'))
    
#     with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
#         server.login(os.environ.get("SENDER"),os.environ.get("PW"))
#         server.sendmail(sender_email, sender_email, msg.as_string())

def send_mail(name,email,phone,subject,message):
    mail = mt.Mail(
    sender=mt.Address(email=os.environ.get("frommail"), name="From Portfolio"),
    to=[mt.Address(email=os.environ.get("tomail"))],
    subject=f"{subject}",
    text=f"Name: {name}\n Email: {email}\n Phone: {phone}\n Message: {message}",)
    client = mt.MailtrapClient(token=os.environ.get("apimail"))
    client.send(mail)
    
  
# HOME PAGE
@app.route("/")
def home():
    previous_section = request.args.get('prev_section','home')
    curr_year=datetime.now().year
    return render_template("index.html",
                           previous_section=previous_section,
                           year=curr_year,
                           form=ContactForm())

# BLOGS PAGE
@app.route("/blogs")
def blog():
    curr_year=datetime.now().year
    blog_posts = requests.get( os.environ.get("npoint")).json()
    return render_template("blogs.html",posts=blog_posts,year=curr_year)

# SEND MAIL WHEN SUBMIT
@app.route("/",methods=["GET","POST"])
def acknowledge():
    curr_year=datetime.now().year
    contact_form = ContactForm()
    data_c=contact_form
    if contact_form.validate_on_submit():
        send_mail(data_c.fullname.data,
                  data_c.email.data,
                  data_c.phone.data,
                  data_c.subject.data,
                  data_c.message.data)
        create_row(data_c.fullname.data,
                   data_c.email.data,
                   data_c.phone.data,
                   data_c.subject.data,
                   data_c.message.data)
        data_c.fullname.data,data_c.email.data,data_c.phone.data,data_c.subject.data,data_c.message.data="","","","",""
        return render_template("index.html",
                               msg_sent=True,
                               form=data_c,
                               year=curr_year)
    data_c.fullname.data,data_c.email.data,data_c.phone.data,data_c.subject.data,data_c.message.data="","","","",""
    return render_template("index.html",
                           msg_sent=False,
                           form=data_c,
                           year=curr_year)
        

#INDIVIDUAL BLOG RENDERING
@app.route("/blogs/<int:id>")
def show_blog(id):
    blog_posts = requests.get(os.environ.get("npoint")).json()
    curr_year=datetime.now().year
    title,blog_text="",""
    for i in blog_posts:
        if i["id"]==id:
            title,blog_text=i["title"],i["blog"]
            break
    return render_template("blog_post.html",
                           title=title,
                           blog_text=blog_text,
                           year=curr_year)


if __name__ == "__main__":
    app.run(debug=True)