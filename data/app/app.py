from flask import Flask, request
import mysql.connector
import os
import time
import socket
import uuid
import hashlib
import cryptocode

app = Flask(__name__)

def connectToDB(db):
	env = os.environ
	dbuser = "root"
	dbpass = env.get("MYSQL_ROOT_PASSWORD")
	dbport = env.get("MYSQL_TCP_PORT")
	dbhost = socket.gethostbyname("db")
	return mysql.connector.connect(user=dbuser, password=dbpass, host=dbhost, port=dbport, database=db)

def closeConnection(cnx, cursor):
	cursor.close()
	cnx.close()

def execQuery(query, db):
	cnx = connectToDB(db)
	cursor = cnx.cursor()
	cursor.execute(query)
	output = []
	for x in cursor:
		output.append( x )
	closeConnection(cnx, cursor)
	return output

def commitQuery(query, db):
	cnx = connectToDB(db)
	cursor = cnx.cursor()
	cursor.execute(query)
	cnx.commit()
	output = []
	for x in cursor:
		output.append( x )
	closeConnection(cnx, cursor)
	return output

def createTable(tblname, uid, *args):
	columns = ""
	tbl = ''.join(tblname.split())
	query = "SHOW TABLES"
	tbls = execQuery(query, "user_{}".format(uid))
	if tbl == "":
		return False, tbl
	for i in tbls:
		if i[0] == tbl:
			return False, tbl
	for x in args:
		columns += "{} {},".format(x.get("name"), x.get("type"))
	string = "CREATE TABLE {} ({})".format(tbl, columns[:-1])
	commitQuery(string, "user_{}".format(uid))
	return True, tbl

def getTables(uid):
	output = execQuery("SHOW TABLES", "user_{}".format(uid))
	return output

def getTableContents(table, uid):
	output = execQuery("SELECT SID,Website,User,Password,Comment FROM {}".format(table), "user_{}".format(uid))
	return output

def printTableToHTML(table, authkey):
	output = ""
	uid = getUserFromAuth(authkey)
	content = getTableContents(table, uid)
	for x in content:
		sid = x[0]
		website = x[1]
		user = x[2]
		password = decryptStoredPassword(x[3], uid)
		comment = x[4]
		output = addFormHeadToHTML(output, authkey)
		output += "<input type=\"hidden\" name=\"sid\" value=\"{}\">".format(sid)
		output += "<input type=\"hidden\" name=\"table\" value=\"{}\">".format(table)
		output += "<input name=\"website\" value=\"{}\" maxlength=\"32\">".format(website)
		output += "<input name=\"user\" value=\"{}\" maxlength=\"32\">".format(user)
		output += "<input type=\"password\" name=\"password\" value=\"{}\" maxlength=\"64\">".format(password)
		output += "<input name=\"comment\" value=\"{}\" maxlength=\"128\">".format(comment)
		output += "<button type=\"button\" onclick=\"openTab('https://{0}')\">O</button>".format(website)
		output += "<button type=\"button\" onclick=\"clip('{}')\">U</button>".format(user)
		output += "<button type=\"button\" onclick=\"clip('{}')\">P</button>".format(password)
		output += "<input type=\"submit\" value=\"Update\" name=\"updateEntry\">"
		output += "<input type=\"submit\" value=\"X\" name=\"deleteEntry\">"
		output = addFormFootToHTML(output)
	output = addFormHeadToHTML(output, authkey)
	output += "<input type=\"hidden\" name=\"table\" value=\"{}\">\n".format(table)
	output += "<input name=\"website\" maxlength=\"32\">\n"
	output += "<input name=\"user\" maxlength=\"32\">\n"
	output += "<input name=\"password\" maxlength=\"64\">\n"
	output += "<input name=\"comment\" maxlength=\"128\">\n"
	output += "<input type=\"submit\" name=\"addEntry\" value=\"Add Entry\">\n"
	output = addFormFootToHTML(output)
	output = addLinebreak(output)
	output = addFormHeadToHTML(output, authkey)
	output += "<input type=\"hidden\" name=\"table\" value=\"{}\">\n".format(table)
	output += "<input type=\"submit\" name=\"dropTable\" value=\"Delete Folder\">\n"
	output += "<input id=\"confirm\" name=\"confirmation\">"
	output += "<label for=\"confirm\">Type confirm to delete folder {}!</label>\n".format(table)
	output = addFormFootToHTML(output)
	output = addLinebreak(output)
	return output

def addLinebreak(html):
	return html + "</br>\n"

def addFormHeadToHTML(html, *args):
	auth = ""
	for x in args:
		auth = "<input type=\"hidden\" name=\"authkey\" value=\"{}\">\n".format(x)
	return html + "<form method=\"post\" action=\"/\">\n" + auth

def addFormFootToHTML(html):
	return html + "</form>\n"

def addTablesToHTML(html, authkey):
	html = addFormHeadToHTML(html, authkey)
	buttons = ""
	uid = getUserFromAuth(authkey)
	for t in getTables(uid):
		t = t[0]
		buttons += "<input type=\"submit\" value=\"{}\" name=\"openTable\"/>\n".format(t)
	html += buttons
	html = addFormFootToHTML(html)
	return html

def addCreateTableButtonToHTML(html, authkey):
	html = addFormHeadToHTML(html, authkey)
	html += "<input name=\"text\">"
	html += "<input type=\"submit\" value=\"{}\" name=\"{}\"/>\n".format("Add Folder", "addFolder")
	html = addFormFootToHTML(html)
	return html

def updateEntry(request, uid):
	sid = request["sid"]
	website = request["website"]
	user = request["user"]
	password = request["password"]
	comment = request["comment"]
	table = request["table"]
	query = "UPDATE {} SET Website = '{}', User = '{}', Password = '{}', Comment = '{}' WHERE SID = {}".format(table, website, user, encryptStoredPassword(password, uid), comment, sid)
	commitQuery(query, "user_{}".format(uid))

def addEntryToTable(request, uid):
	website = request["website"]
	user = request["user"]
	password = request["password"]
	comment = request["comment"]
	table = request["table"]
	query = "INSERT INTO {} (Website, User, Password, Comment) VALUES ('{}', '{}', '{}', '{}')".format(table, website, user, encryptStoredPassword(password, uid), comment)
	commitQuery(query, "user_{}".format(uid))

def removeEntryFromTable(request, uid):
	sid = request["sid"]
	table = request["table"]
	query = "DELETE FROM {} WHERE sid = {}".format(table, sid)
	commitQuery(query, "user_{}".format(uid))

def removeTable(request, uid):
	table = request["table"]
	confirmed = request.get("confirmation")
	query = "DROP TABLE {}".format(table)
	if confirmed == "confirm":
		commitQuery(query, "user_{}".format(uid))
		return True
	return False

def getHTMLHead():
	return "<!DOCTYPE html>\n<head>\n<title>Malns Passwordmanager</title>\n</head>\n<body>\n"

def getHTMLFoot():
	return "<script>\nfunction openTab(url) {window.open(url);}\nfunction clip(str) {var el = document.createElement('textarea'); el.value = str; el.setAttribute('readonly', ''); el.style = {position: 'absolute', left: '-9999px'}; document.body.appendChild(el); el.select(); document.execCommand('copy'); document.body.removeChild(el);}\n</script>\n</body>\n</html>\n"

def checkUser(name):
	query = "SELECT username FROM users"
	users = execQuery(query, "auth")
	for i in users:
		if i[0] == name:
			return True
	return False

def encryptPassword(pw, salt=uuid.uuid4().hex):
	return hashlib.sha256(salt.encode() + pw.encode()).hexdigest() +  salt

def checkPassword(name, pw):
	query = "SELECT password FROM users WHERE username = \"{}\"".format(name)
	data = execQuery(query, "auth")
	salt = data[0][0][-32:]
	pwenc = data[0][0]
	if encryptPassword(pw, salt) == pwenc:
		return True
	return False

def generateAuthKey(name):
	query = "SELECT uid FROM users WHERE username = \"{}\"".format(name)
	data = execQuery(query, "auth")
	oid = data[0][0]
	id = uuid.uuid4().hex
	unixtime = time.time()
	return hashlib.sha256(str(unixtime).encode() + id.encode() + str(oid).encode() + name.encode()).hexdigest(), oid

def registerAuthKey(key, oid):
	query = "INSERT INTO authkeys VALUES (\"{}\", {}, {}, {})".format(key, oid, "NOW()", "NOW()")
	commitQuery(query, "auth")

def updateAuthKey(key):
	query = "UPDATE authkeys SET timeModified = {} WHERE key = \"{}\"".format("NOW()", key)
	commitQuery(query, "auth")

def checkAuthKey(key):
	query = "SELECT uid FROM authkeys WHERE timeModified >= DATE_SUB(NOW(), INTERVAL 1 HOUR)"
	keys = execQuery(query, "auth")
	for k in keys:
		if k[0] == key:
			return True
	return False

def getUserFromAuth(authkey):
	query = "SELECT oid FROM authkeys WHERE uid = \"{}\"".format(authkey)
	user = execQuery(query, "auth")
	return user[0][0]

def encryptStoredPassword(pw, uid):
	env = os.environ
	query = "SELECT salt FROM users WHERE uid = {}".format(uid)
	salt = execQuery(query, "auth")[0][0]
	pepper = env.get("ENC_PEPPER")
	key = env.get("ENC_KEY")
	msgsalt = cryptocode.encrypt(salt + pw, key + pepper)
	msgpepper = cryptocode.encrypt(msgsalt + pepper, key + salt)
	return msgpepper

def decryptStoredPassword(crypt, uid):
	env = os.environ
	query = "SELECT salt FROM users WHERE uid = {}".format(uid)
	salt = execQuery(query, "auth")[0][0]
	key = env.get("ENC_KEY")
	pepper = env.get("ENC_PEPPER")
	decpepper = cryptocode.decrypt(crypt, key + salt)[:-32]
	dec = cryptocode.decrypt(decpepper, key + pepper)[32:]
	return dec

def registerUser(request):
	name = request["username"].lower()
	pwenc = encryptPassword(request["password"])
	if not checkUser(name):
		query = "INSERT INTO users (username, password, salt) VALUES (\"{}\", \"{}\", \"{}\")".format(name, pwenc, uuid.uuid4().hex)
		commitQuery(query, "auth")
		query = "SELECT uid FROM users WHERE username = \"{}\"".format(name)
		uid = execQuery(query, "auth")[0][0]
		query = "CREATE DATABASE user_{}".format(uid)
		commitQuery(query, None)
		return True, "Registered User {}!".format(name)
	else:
		return False, "Username {} already exists!".format(name)

def loginUser(request):
	name = request["username"]
	pw = request["password"]
	if checkPassword(name, pw):
		key, oid  = generateAuthKey(name)
		registerAuthKey(key, oid)
		return main(key)
	return drawLoginPage("Login failed!")

def registerInfo(name):
	return drawLoginPage(name)

@app.route('/', methods=['GET'])
def drawLoginPage( *args ):
        html = getHTMLHead()
        html = addFormHeadToHTML(html)
        html += "<table>\n"
        html += "<tr>\n"
        html += "<th><label for=\"user\">Username</label></th>\n"
        html += "<th><label for=\"pass\">Password</label></th>\n"
        html += "</tr>\n"
        html += "<tr>\n"
        html += "<th><input id=\"user\" name=\"username\"></th>\n"
        html += "<th><input id=\"pass\" type=\"password\" name=\"password\"></th>\n"
        html += "</tr>"
        html += "</table>"
        html = addLinebreak(html)
        html += "<input type=\"submit\" name=\"login\" value=\"Login\">\n"
        html += "or "
        html += "<input type=\"submit\" name=\"register\" value=\"Register\">\n"
        html = addFormFootToHTML(html)
        for x in args:
                html += "<p>{}</p>".format(x)
        html += getHTMLFoot()
        return html

def main(authkey, *args ):
	html = getHTMLHead()
	html = addCreateTableButtonToHTML(html, authkey)
	html = addLinebreak(html)
	html = addTablesToHTML(html, authkey)
	html = addLinebreak(html)
	for i in args:
		html += printTableToHTML(i, authkey)
	html += getHTMLFoot()
	return html

@app.route('/', methods=['POST'])
def postHandler():
	if request.form.get("login") is not None:
		return loginUser(request.form)
	elif request.form.get("register") is not None:
		success, reason = registerUser(request.form)
		return registerInfo(reason)
	if checkAuthKey(request.form.get("authkey")):
		authkey = request.form.get("authkey")
		uid = getUserFromAuth(authkey)
		if request.form.get("addFolder") is not None:
			success, tbl = createTable(request.form["text"], uid, {"name": "SID", "type": "int NOT NULL AUTO_INCREMENT"}, {"name": "Website", "type": "varchar(32)"}, {"name": "User", "type": "varchar(32)"}, {"name": "Password", "type": "varchar(448)"}, {"name": "Comment", "type": "varchar(128)"}, {"name": "PRIMARY KEY", "type": "(SID)"},)
			if success:
				return main(authkey, tbl)
			return main(authkey)
		elif request.form.get("updateEntry") is not None:
			updateEntry(request.form, uid)
			return main(authkey, request.form["table"])
		elif request.form.get("addEntry") is not None:
			addEntryToTable(request.form, uid)
			return main(authkey, request.form["table"])
		elif request.form.get("openTable") is not None:
			return main(authkey, request.form["openTable"])
		elif request.form.get("deleteEntry") is not None:
			removeEntryFromTable(request.form, uid)
			return main(authkey, request.form["table"])
		elif request.form.get("dropTable") is not None:
			if not removeTable(request.form, uid):
				return main(authkey, request.form["table"])
			return main(authkey)
	return drawLoginPage()
