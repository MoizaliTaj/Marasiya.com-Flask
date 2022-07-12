import os
from flask import Flask, send_from_directory
from flask import render_template
from flask_sqlalchemy import SQLAlchemy

current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "database.sqlite3")
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()


class File_Info(db.Model):
    __tablename__ = 'file_info'
    title = db.Column(db.String, nullable=False)
    file_name = db.Column(db.String, nullable=False)
    file_id = db.Column(db.String, primary_key=True)
    category = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)


class Page_Info(db.Model):
    __tablename__ = 'page_info'
    page_number = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String, nullable=False)
    page_path = db.Column(db.String, primary_key=True, nullable=False)
    page_name = db.Column(db.String, nullable=False)
    nav_name = db.Column(db.String, nullable=False)
    page_info = db.Column(db.String)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/ads.txt")
def ads_txt():
    return 'google.com, pub-6804075268466793, DIRECT, f08c47fec0942fa0'


@app.route("/app-ads.txt")
def app_ads_txt():
    return 'google.com, pub-6804075268466793, DIRECT, f08c47fec0942fa0'


@app.route("/robots.txt")
def robots_txt():
    return 'Sitemap: https://www.marasiya.com/sitemap.xml'

@app.route("/sitemap.xml")
def sitemap_xml():
    urls = ['https://marasiya.com']
    page_data = Page_Info.query.order_by(Page_Info.page_number).all()
    page_list = []
    for i in page_data:
        page_list.append((i.category,i.page_path))
        urls.append('https://marasiya.com/'+str(i.page_path))
    for a in page_list:
        title_data = File_Info.query.filter_by(category=a[0]).with_entities(File_Info.title).distinct().order_by(File_Info.title).all()
        for i in title_data:
            urls.append('https://marasiya.com/'+str(a[1])+'/'+i[0].replace(' ','%20'))
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset 
      xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:xhtml="http://www.w3.org/1999/xhtml"
      xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd
http://www.w3.org/1999/xhtml
http://www.w3.org/2002/08/xhtml/xhtml1-strict.xsd">

'''
    from datetime import datetime

    for i in urls:
        priority_count = i.count('/')
        if priority_count == 2:
            priority = 1.00
        elif priority_count == 3:
            priority = 0.80
        elif priority_count == 4:
            priority = 0.64
        date_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
        Out_inst = '<url>\n  <loc>' + i + '</loc>\n  <lastmod>' + str(date_time) + '</lastmod>\n  <priority>' + str(
            priority) + '</priority>\n</url>\n'
        xml_content = xml_content + Out_inst
    xml_content = xml_content + '\n</urlset>'
    temp = open("sitemapdetails.xml","w")
    temp.write(xml_content)
    temp.close
    return xml_content


@app.route("/")
def home():

    # path data is used for navigation menu and current content link displayed in the main content.
    path_data = Page_Info.query.order_by(Page_Info.page_number).all()
    return render_template("index.html", path_data=path_data)


@app.route("/<page_path>")
def page(page_path):

    # path data is used for navigation menu.
    path_data = Page_Info.query.order_by(Page_Info.page_number).all()

    # This will get all the info for a page as per the page_path in the url.
    page_info = Page_Info.query.filter_by(page_path=page_path.lower()).first()
    if not page_info:
        return render_template("error.html", path_data=path_data), 404
    category = page_info.category
    page_title = page_info.page_name

    # retrieves all the unique title info for a particular category.
    dump_title = File_Info.query.filter_by(category=category).with_entities(File_Info.title).distinct().order_by(File_Info.title).all()
    return render_template("page.html", path_data=path_data, data=dump_title, page_title=page_title, parent=page_path.lower(), title=category)

@app.route("/<page_path>/<title>")
def title(page_path, title):

    # path data is used for navigation menu.
    path_data = Page_Info.query.order_by(Page_Info.page_number).all()

    # This will get all the info for a page as per the page_path in the url.
    page_info = Page_Info.query.filter_by(page_path=page_path.lower()).first()
    if not page_info:
        return render_template("error.html", path_data=path_data), 404
    category = page_info.category

    # audio file(s) dump
    dump_audio = File_Info.query.filter_by(category=category, title=title, type='Audio').with_entities(File_Info.file_name, File_Info.file_id, File_Info.type).order_by(File_Info.file_name).all()

    # PDF file(s) dump
    dump_pdf = File_Info.query.filter_by(category=category, title=title, type='PDF').with_entities(File_Info.file_name, File_Info.file_id,File_Info.type).order_by(File_Info.file_name).all()

    if (not dump_audio) and (not dump_pdf):
        return render_template("error.html", path_data=path_data), 404

    return render_template("kalam.html", path_data=path_data, category=category, parent_path=page_path, page_title=title, data_audio=dump_audio, data_pdf=dump_pdf,)


if __name__ == '__main__':
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080
    app.run(host='127.0.0.1', port=PORT, debug=False)
