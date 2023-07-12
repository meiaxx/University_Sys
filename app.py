# Imports #
from flask import Flask,render_template,request,redirect,url_for,session,flash,send_file,send_from_directory
import MySQLdb.cursors
from flask_mysqldb import MySQL
from flask_mail import Mail,Message
import os
import random
import string
import uuid
from datetime import datetime

# all password character's
# this is for generate key
characters = string.digits + string.ascii_letters + string.punctuation
length = 32

# start app
app = Flask(__name__)


# security anti-CSRF
app.secret_key = "".join(random.sample(characters,length))

# MYSQL DB config
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'm3y'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'uptt'

mysql = MySQL(app)

# Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'upttinfo@gmail.com' # h4A7zhhchkTCz9L
app.config['MAIL_PASSWORD'] = 'dwjedtkldbdjwkvk' # upttinfo@gmail.com
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

# Upload Folder
CARPETA = os.path.join('uploads')
app.config['CARPETA'] = CARPETA

@app.route('/uploads/<nombrefoto>')
def uploads(nombrefoto):
	return send_from_directory(app.config['CARPETA'],nombrefoto)

# send password to user-email
def send_password(email,data):
	msg = Message(f'Hola! {email} Establece tu nueva contraseña a continuacion',sender='upttinfo@gmail.com',recipients=['{}'.format(email)])
	msg.body = 'Para Cambiar Tu Contraseña porfavor ingresa en el siguiente link: {}'.format(data)
	mail.send(msg)
	return 'Mensage Enviado!!'

# home route
@app.route("/")
def home():
    return render_template('home.html')

@app.route('/download')
def download():
	return send_file('static/plantilla/form.doc',as_attachment=True)

# requisites route
@app.route("/requisitos")
def requisitos():
    return render_template('requisites.html')

# Universities
@app.route("/sedes")
def sedes():
    return render_template('sedes.html')

# Images 
@app.route("/galeria")
def galeria():
    return render_template("gallery.html")

# Contact Form 
@app.route("/contacto")
def contacto():
	return render_template("contact.html")

# Not Found 
@app.errorhandler(404)
def not_found(e):
	return render_template('404.html'),404


# Login
"""
POST
"""
@app.route("/login",methods=['GET','POST'])
def login():
	msg = ''
	if request.method == 'POST':
		usuario = request.form['usuario']
		contraseña = request.form['password']

		# execute query
		cursors = mysql.connection.cursor()
		cursors.execute('SELECT * FROM users WHERE usuario = %s AND contraseña = %s',(usuario,contraseña,))
		account = cursors.fetchone()

		if account:
			session['logeado'] = True
			session['id'] = account[0]
			session['usuario'] = account[8]

			hora_entrada = datetime.now().strftime("%H:%M:%S %p")

			session['hora_entrada'] = hora_entrada

			# Save the time of entry in the database (using MySQL)
			conn = mysql.connection.cursor()

			sql = "UPDATE users SET hora_entrada = %s WHERE id = %s"
			data=(hora_entrada,session['id'])
			conn.execute(sql,data)
			mysql.connection.commit()

			# execute this connection for load the date from user
			# query: select * from users where id = 1;
			cursors.execute('SELECT * FROM users WHERE id = %s',(session['id'],))
			users = cursors.fetchone()

			return render_template('dashboard.html',users=users)
			#flash('Logeado(a) Exitosamente!')

		else:
			flash('Usuario/Contraseña Incorrecta!')

	return render_template('login.html')

# Logout
@app.route("/logout",methods=['GET','POST'])
def logout():
	# Check if there is a login time stored in the session
	if 'hora_entrada' in session:
		hora_entrada = session['hora_entrada']

		# delete hour
		del session['hora_entrada']

		# get departure time
		hora_salida = datetime.now().strftime('%H:%M:%S %p')

		# departure time 
		cursor = mysql.connection.cursor()
		sql = "UPDATE users SET hora_salida=%s WHERE id =%s"
		data = (hora_salida,session['id'])
		cursor.execute(sql,data)
		mysql.connection.commit()


	session.pop('logeado',None)
	session.pop('id',None)
	session.pop('usuario',None)
	return redirect(url_for('login'))

# Account/Profile
@app.route("/cuenta",methods=['GET','POST'])
def cuenta():
	if 'logeado' in session and 'hora_entrada' in session:
		# load the data from db
		hora_entrada = session['hora_entrada']
		cursor = mysql.connection.cursor()
		cursor.execute('SELECT * FROM users WHERE id = %s',(session['id'],))
		users = cursor.fetchone()

		# get d.... hour
		cursor.execute('SELECT hora_salida FROM users WHERE id = %s',(session['id'],))
		resultado = cursor.fetchone()
		
		hora_salida = resultado[0] if resultado and resultado[0] is not None else ''
		
		return render_template('dashboard.html',users=users,hora_entrada=hora_entrada, hora_salida=hora_salida)


	return redirect(url_for('login'))

# reset password
@app.route("/olvidocontraseña",methods=["GET","POST"])
def olvidocontraseña():
	msg = ''
	if 'logeado' in session:
		return redirect('/')
	elif request.method == 'POST' and 'correo' in request.form:
		correo = request.form["correo"]
		token = str(uuid.uuid4())
		cursors = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		result = cursors.execute('SELECT * FROM users WHERE correo = % s',[correo])

		if result:
			data = cursors.fetchone()
			cursors = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursors.execute('UPDATE users SET token=%s WHERE correo=%s',[token,correo])
			mysql.connection.commit()

			data = 'http://{}/cambiarcontraseña/{}'.format(host,token)
			send_password(correo,data) # send the password to the email

			msg = 'Contraseña Enviada a su Email'
		else:
			msg = '!Correo Electronico No encontrado'

	return render_template('forgot.html',msg=msg)

# reset password
@app.route("/cambiarcontraseña/<token>",methods=["GET","POST"])
def cambiarcontraseña(token):
	msg = ''
	if 'logeado' in session:
		return redirect('/')

	if request.method == 'POST':
		password = request.form["password"]
		confirmpassword = request.form["confirmpassword"]
		token1 = str(uuid.uuid4())

		if password != confirmpassword:
			flash("Las contraseñas no coinciden")
			return redirect('cambiarcontraseña')

		cursors = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursors.execute('SELECT * FROM users WHERE token = % s',[token])
		user = cursors.fetchone()

		if user:
			cursors = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursors.execute('UPDATE users SET token=%s,contraseña=%s WHERE token=%s',[token1,password,token])
			mysql.connection.commit()
			cursors.close()
			msg = 'Contraseña Actualizada Exitosamente'
			return redirect('/login')
		else:
			msg = "Token Invalido"
			return redirect('/')
	return render_template('reset.html',msg=msg)

# Register
@app.route("/registro",methods=['GET','POST'])
def registro():
	msg = ''
	if request.method == 'POST':
		nombre = request.form['nombre']
		apellido = request.form['apellido']
		edad = request.form['edad']
		fecha_nacimiento = request.form['fecha_nacimiento']
		correo = request.form['correo']
		direccion = request.form['direccion']
		numero_telefono = request.form['numero_telefono']
		usuario = request.form['usuario']
		password = request.form['contraseña']
		tipo_cargo = request.form['tipocargo']
		imagen = request.files['imagen']

		# connect to MYSQL
		cursor = mysql.connection.cursor()
		cursor.execute('SELECT * FROM users WHERE usuario = % s',(usuario,))
		account = cursor.fetchone()

		if account:
			flash('La cuenta Ya existe!')
		else:
			# execute query to insert data into DB
			now = datetime.now()
			tiempo = now.strftime("%Y%H%M%S")
			name_imagen = tiempo+imagen.filename
			imagen.save("uploads/"+name_imagen)

			sql = "INSERT INTO users(nombre,apellido,edad,fecha,correo,direccion,numero,usuario,contraseña,tipocargo,imagen) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			data = (nombre,apellido,edad,fecha_nacimiento,correo,direccion,numero_telefono,usuario,password,tipo_cargo,name_imagen)
			cursor.execute(sql,data)
			mysql.connection.commit()

			flash('Registro Exitosamente!')

	return render_template('register.html')

# Update
@app.route("/actualizar_contraseña",methods=['GET','POST'])
def actualizar_contraseña():
	pass
	return render_template('update.html')


# show the profile dates in the following order:
#  1) User Image
#  2) Name
#  3) CD ( Cedula of Entity )
@app.route('/perfil')
def perfil():
	if 'logeado' in session:
		cur = mysql.connection.cursor()
		cur.execute('SELECT * FROM users WHERE id = %s',(session['id'],))
		account = cur.fetchone()

		return render_template('profile.html',account=account)
	
	return redirect(url_for('login'))

# Update dates from perfil if the user is logged in
# for update this dates need to access first
@app.route('/actualizar_datos', methods=['GET', 'POST'])
def actualizar_datos():
	if 'logeado' in session:
		if request.method == 'POST':
			# Obtener los datos proporcionados por el usuario
			nombre = request.form.get('nombre')
			apellido = request.form.get('apellido')
			edad = request.form.get('edad')
			fecha_nac = request.form.get('fecha')
			correo = request.form.get('correo')
			direccion = request.form.get('direccion')
			numero_tel = request.form.get('numero')
			usuario = request.form.get('usuario')
			password = request.form.get('contraseña')
			tipo_cargo = request.form.get('tipocargo')
			imagen = request.files.get('imagen')
			
			# Conectar a la base de datos
			cur = mysql.connection.cursor()
			
			# Construir la consulta de actualización dinámicamente
			sql = "UPDATE users SET"

            # Crear una lista de valores a actualizar
			valores = []
			if nombre:
				sql += " nombre=%s,"
				valores.append(nombre)
			if apellido:
				sql += " apellido=%s,"
				valores.append(apellido)
			if edad:
				sql += " edad=%s,"
				valores.append(edad)
			if fecha_nac:
				sql += " fecha=%s,"
				valores.append(fecha_nac)
			if correo:
				sql += " correo=%s,"
				valores.append(correo)
			if direccion:
				sql += " direccion=%s,"
				valores.append(direccion)
			if numero_tel:
				sql += " numero=%s,"
				valores.append(numero_tel)
			if usuario:
				sql += " usuario=%s,"
				valores.append(usuario)
			if password:
				sql += " contraseña=%s,"
				valores.append(password)
			if tipo_cargo:
				sql += " tipocargo=%s,"
				valores.append(tipo_cargo)
			if imagen:
				now = datetime.now()
				tiempo = now.strftime("%Y%H%M%S")
				new_image = tiempo + imagen.filename
				imagen.save("uploads/" + new_image)
				sql += " imagen=%s,"
				valores.append(new_image)

            # Eliminar la última coma de la consulta
			sql = sql.rstrip(',')

            # Agregar la condición para actualizar un usuario específico
			sql += " WHERE id=%s"
			valores.append(session['id'])

            # Ejecutar la consulta de actualización
			cur.execute(sql, tuple(valores))
			mysql.connection.commit()
			
			flash('¡Actualización exitosa!')
		
		return render_template('actualizar_datos.html')


# update password from profile if the user is logged in
@app.route('/actualizar_contraseña_perfil',methods=['GET','POST'])
def actualizar_contraseña_perfil():
	if 'logeado' in session:
		if request.method == 'POST':
			new_password = request.form['new_password']
			cur = mysql.connection.cursor()
			cur.execute('UPDATE users SET contraseña=%s WHERE usuario=%s',(new_password,session['usuario'],))
			mysql.connection.commit()
			
			return render_template('actualizar_contraseña.html',msg='Contraseña actualizada exitosamente!')
		
		return render_template('actualizar_contraseña.html')

	else:
		return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
