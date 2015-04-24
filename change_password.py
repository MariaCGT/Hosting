#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import MySQLdb
import os

tipo = sys.argv[1]
usuario = sys.argv[2]
contra = sys.argv[3]

if sys.argv[1] == "-ftp":
	conn = MySQLdb.connect(host="localhost",user="root",passwd="root",db="ftpd")
	cursor = conn.cursor()
	query = "update usuarios SET password = password('%s') where username = '%s'" % (contra,usuario)
	cursor.execute(query)
	conn.commit()
	cursor.close()
	conn.close()
	print "La contraseña del usuario ftp ha sido modificada correctamente"
elif sys.argv[1] == "-sql":
	conn = MySQLdb.connect(host="localhost",user="root",passwd="root")
	cursor = conn.cursor()
	query = "set password for my%s@localhost = password('%s')" % (usuario,contra)
	cursor.execute(query)
	conn.commit()
	cursor.close()
	conn.close()
	print "La contraseña del usuario mysql ha sido modificada correctamente"
else:
	print "Opción incorrecta"
