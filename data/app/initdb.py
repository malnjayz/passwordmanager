import os
import mysql.connector
import socket

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
	#output = []
	#for x in cursor:
	#	output.append( x )
	closeConnection(cnx, cursor)
	#return output

def createDatabase(name):
	query = "CREATE DATABASE {}".format(name)
	commitQuery(query, None)

def createTable(tblname, uid, *args):
	columns = ""
	tbl = ''.join(tblname.split())
	query = "SHOW TABLES"
	tbls = execQuery(query, "user_{}".format(uid))
	if tbl == "":
		return False, tbl
	for i in tbls[0]:
		if i[0] == tbl:
			return False, tbl
	for x in args:
		columns += "{} {},".format(x["name"], x["type"])
	string = "CREATE TABLE {} ({})".format(tbl, columns[:-1])
	commitQuery(string, "user_{}".format(uid))
	return True, tbl

def main():
	createDatabase("auth")
	query = "CREATE TABLE authkeys ( uid varchar(64), oid int, timeCreated datetime, timeModified datetime, PRIMARY KEY (uid))"
	commitQuery(query, "auth")
	query = "CREATE TABLE users (uid int NOT NULL AUTO_INCREMENT, username varchar(32), password varchar(96), salt varchar(32), PRIMARY KEY (uid));"
	commitQuery(query, "auth")

if __name__ == '__main__':
	main()
