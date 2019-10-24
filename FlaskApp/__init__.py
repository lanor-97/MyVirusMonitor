from flask import Flask, render_template, request, url_for, redirect, session, flash
from werkzeug import secure_filename
import mysql.connector, json, os

#FLASK HANDLERS
app = Flask(__name__)
app.secret_key = "3CDDB48BDD8D59EEB44FDFAA99B5"

#WEB LOGIN INFO
conf_file = open("/var/www/FlaskApp/Config.json")
conf = json.loads(conf_file.read())

true_user = conf['site_user']
true_pass = conf['site_psw']

#DATABASE HANDLERS
db_connection = mysql.connector.connect(
	user=conf['db_user'],
	password=conf['db_psw'],
	host=conf['db_host'],
	database=conf['db_name'])

cursor = db_connection.cursor(buffered=True)

conf_file.close()
#FUNZIONI UTILIY
supported_filetypes = [
	"exe", "eml", "xls", "img", "virus", "zip", "rar", "ace", "doc", "msi"
]

def manage_new_file(file):
	#non tiene conto del caso in cui si carica un file con lo stesso nome
	#di uno già presente in directory

	name = file.filename
	filetype_idx = name.rfind('.') + 1
	filetype = name[filetype_idx :]
	if filetype not in supported_filetypes:
		return "not_supported_format"

	path, dirs, files = next(os.walk("tmp_files"))
	file_count = len(files)
	if file_count > 20:
		return "too_many_files"

	file_size = os.path.getsize('tmp_files/' + file.filename)
	if file_size > 100000000:
		return "too_big"

	cursor.execute("SELECT * FROM File")
	num_files_in_db = cursor.rowcount
	if num_files_in_db > 2000:
		return  "too_many_files_db"

	file.save('tmp_files/' + secure_filename(file.filename))
	return "success"



#WEB FUNCTIONS
@app.route('/')
def index():
	if session.get('logged_in'):
		return home()

	return render_template('index.html')

@app.route('/login', methods = ['POST'])
def login():
	if session.get('logged_in'):
		return home()

	tried_user = request.form['user']
	tried_pass = request.form['pass']

	if tried_user == true_user and tried_pass == true_pass:
		session['logged_in'] = True
		return redirect(url_for('home'))

	return redirect(url_for('index'))

@app.route('/home', methods = ['GET'])
def home():
	if not session.get('logged_in'):
		return index()

	try:
		cursor.execute("SELECT * FROM File")
		rows = cursor.fetchall()

		#Taking info about each file: num av that detected it vs num av that processed it
		data = []
		for row in rows:
			id = row[0]
			cursor.execute("SELECT count(*) FROM VirusDetected WHERE file_id = %s", (id,))
			num_detected = cursor.fetchone()
			cursor.execute("SELECT count(*) FROM AvProcessedFile WHERE file_id = %s", (id,))
			num_processed = cursor.fetchone()

			#file_info is a tuple
			file_info = row + num_detected + num_processed
			data.append(file_info)
		return render_template("home.html", files = data)
	except:
		return render_template("error.html")

@app.route('/antivirus', methods = ['GET'])
def antivirus():
	if not session.get('logged_in'):
		return index()

	try:
		cursor.execute("SELECT * FROM AntiVirus WHERE num_files_processed > 0 ORDER BY num_files_detected / num_files_processed")
		rows = cursor.fetchall()

		percs = []
		for row in rows:
			num_files_detected = row[1]
			num_files_processed = row[3]
			perc = 0
			if num_files_processed > 0:
				perc = (num_files_detected / num_files_processed) * 100
				perc = float('%.2f'%(perc))
			percs.append(perc)

		#idx 0: nome antivirus
		#idx 1: num file rilevati
		#idx 2: num falsi pos
		#idx 3: num file processati
		return render_template("antivirus.html", av_list = rows, perc_list = percs, length = len(rows))
	except:
		return render_template("error.html")

@app.route('/file', methods = ['GET'])
def file_info():
	if not session.get('logged_in'):
		return index()

	try:
		id = request.args['id']
		detailed_info = []

		cursor.execute("SELECT distinct(detect_date) FROM VirusDetected WHERE file_id = " + id + " ORDER BY detect_date")
		dates = cursor.fetchall()

		count = 0
		if len(dates) == 0:
			return home()

		for date_ in dates:
			cursor.execute("SELECT av_name FROM VirusDetected WHERE file_id = %s AND detect_date = %s", (id, date_[0]))
			count += cursor.rowcount

			detailed_info.append((date_[0], cursor.rowcount, cursor.fetchall(), count))

		cursor.execute("SELECT name FROM File WHERE id = " + id)
		file_name = cursor.fetchone()

		#formato di info: (detect_date, num_av_per_date, av_list, num_av_detect_total)
		return render_template("file_info.html", info = detailed_info, name = file_name, length = len(dates))
	except:
		return render_template("error.html")

@app.route('/add', methods = ['POST'])
def add_file():
	if not session.get('logged_in'):
		return index()

	try:
		f = request.files['file']
		return manage_new_file(f)
	except:
		return "error"


@app.route('/add-api', methods = ['POST'])
def add_file_api():
	try:
		f = request.files['file']
		return manage_new_file(f)
	except:
		return "error"



@app.route('/rmv', methods = ['POST'])
def rmv_file():
	if not session.get('logged_in'):
		return index()

	try:
		id = request.data
		#commented for now for avoiding damage
		#cursor.execute("DELETE FROM File WHERE id = " + id)
		#db_connection.commit()
		return "success"
	except:
		return "error"

@app.route('/logout')
def logout():
	if session.get('logged_in'):
		session['logged_in'] = False

	return index()


#MAIN
if __name__ == '__main__':#avvio il sito web
	app.run()