import time
import datetime
import os
import PyPDF2
from flask import Flask, request, render_template, send_from_directory
import platform
from PyPDF2 import PdfFileReader
from PIL import Image
from statistics import mean
from crontab import CronTab

app = Flask(__name__)
my_url = "http://ec2-18-216-49-139.us-east-2.compute.amazonaws.com:5005/"

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

def timer_five():
    cron = CronTab(user='ubuntu')
    job = cron.new(command='python t_5.py')
    print("cron started")
    job.minute.every(5)
    cron.write()


def pdf_word_(filename):
	pdfFile = os.path.join(APP_ROOT, 'images/' + filename)
	# check if the specified file exists or not
	try:
		if os.path.exists(pdfFile):
			print("file found!")
	except OSError as err:
		print(err.reason)
		exit(1)


	# get the word count in the pdf file
	totalWords = 0
	num_lines = 0
	d=[]
        numPages = getPageCount(pdfFile)
        for i in range(numPages):
            text = extractData(pdfFile, i)
            print(text)
            totalWords += getWordCount(text)
            num_lines += text.count("\n")
	    time.sleep(1)
	    d.append(numPages)
	    d.append(totalWords)
	    d.append(num_lines)
	    return d

def getPageCount(pdf_file):
	pdfFileObj = open(pdf_file, 'rb')
	pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
	pages = pdfReader.numPages
	return pages


def extractData(pdf_file, page):
	pdfFileObj = open(pdf_file, 'rb')
	pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
	pageObj = pdfReader.getPage(page)
	data = pageObj.extractText()
	return data


def getWordCount(data):
	data = data.split()
	return len(data)




def timer_five_mins(filename):
    time.sleep(60*5)
    os.remove(os.path.join(APP_ROOT, 'images/'+filename))



def jpeg_res(filename):
   with open(filename,'rb') as img_file:
       img_file.seek(163)
       a = img_file.read(2)
       height = (a[0] << 8) + a[1]
       a = img_file.read(2)
       width = (a[0] << 8) + a[1]
   return "The resolution of the image is" + str(width) + "x" + str(height)


def creation_date(path_to_file):
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            print(stat.st_birthtime)
            return datetime.datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            return datetime.datetime.fromtimestamp(stat.st_mtime)


def modification_date(path_to_file):
    if platform.system() == 'Windows':
        return datetime.datetime.fromtimestamp(os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            return datetime.datetime.fromtimestamp(stat.st_mtime)
        except AttributeError:
            return datetime.datetime.fromtimestamp(stat.st_birthtime)


@app.route("/")
def index():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    if not os.path.isdir(target):
        os.mkdir(target)
    timer_five()
    print(request.files.getlist("file"))
    for upload in request.files.getlist("file"):
        print(upload)
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        # This is to verify files are supported
        ext = os.path.splitext(filename)[1]
        if (ext == ".jpg") or (ext == ".png") or (ext == ".jpeg") or (ext == ".pdf"):
            print("File supported moving on...")
        else:
            render_template("Error.html", message="Files uploaded are not supported...")
        destination = "/".join([target, filename])
        print("Accept incoming file:", filename)
        print("Save it to:", destination)
        upload.save(destination)
    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("upload.html", image_url=my_url+"upload/"+filename, img_txt="click to view uploaded file",
                           del_txt="click to delete file", del_url=my_url+"delete/"+filename,
                           details_url=my_url+"details/"+filename, details_txt="click for details",
                           gallery_txt="click to view gallery", gallery_url=my_url+"gallery")


@app.route('/upload/<filename>')
def send_image(filename):
    print("fffffff")
    return send_from_directory("images", filename)


@app.route('/delete/<filename>')
def delete_file(filename):
    os.remove(os.path.join(APP_ROOT, 'images/' + filename))
    return render_template("deleted.html")


@app.route('/details/<filename>', methods=["POST", "GET"])
def details_file(filename):
    details = []
    print("detailssssss")
    details.append(creation_date(os.path.join(APP_ROOT, 'images/' + filename)))
    details.append(modification_date(os.path.join(APP_ROOT, 'images/' + filename)))
    details.append(os.path.getsize(os.path.join(APP_ROOT, 'images/' + filename)))
    ext = os.path.splitext(filename)[1]
    if ext == ".pdf":
        input1 = PdfFileReader(open(os.path.join(APP_ROOT, 'images/' + filename), 'rb'))
        details.append(input1.getPage(0).mediaBox)
        temp=(pdf_word_(filename))
        details.append(temp[1])
        details.append(temp[2])
        details.append(temp[3])
        return render_template("details.html", detailyys=details,n_w_txt="no of words :",n_l_txt="no on lines :")
    else:
        im= Image.open(os.path.join(APP_ROOT, 'images/' + filename))
        details.append(im.size)
        npixels = im.size[0]*im.size[1]
	cols = im.getcolors(npixels)
	sumRGB = [(x[0]*x[1][0], x[0]*x[1][1], x[0]*x[1][2]) for x in cols]
	avg = tuple([sum(x)/npixels for x in zip(*sumRGB)])
	details.append(avg)
        return render_template("details.html", detailyys=details,t="average rgb")



@app.route('/gallery')
def get_gallery():
    image_names = os.listdir('./images')
    print("gallery")
    print(image_names)
    return render_template("gallery.html", image_names=image_names)


if __name__ == "__main__":
    app.run( host='0.0.0.0',port=5005, debug=True)