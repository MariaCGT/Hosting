#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import MySQLdb
import os
import string
from random import choice

#Creamos función para crear contraseñas aleatorias
def GenPasswd(n):
	return ''.join([choice(string.letters + string.digits) for i in range(n)])


#Guardamos en variables los parámetros introducidos por el usuario
usuario = sys.argv[1]
dominio = sys.argv[2]+".com"

#Nos conectamos a la base de datos
conn = MySQLdb.connect(host="localhost",user="proftpd",passwd="proftpd",db="ftpd")

#Creamos un cursor
cursor = conn.cursor()

#Ejecutamos la consulta
query = 'select username from usuarios where username = "%s";' % usuario

resultado = cursor.execute(query)

#Cerramos el cursor
cursor.close()

#Resultado devuelve 1 ó 0 dependiendo de si hay coincidencia
if resultado != 0:
	print "El usuario %s ya existe" % usuario
else:
	#comprobamos si existe el dominio
	#abrimos el cursor de nuevo
	cursor = conn.cursor()
	query = 'select dominio from usuarios where dominio = "%s";' % dominio
	resultado = cursor.execute(query)
	cursor.close()
	if resultado != 0:
		print "El dominio %s ya existe" % dominio
	else:

		#VIRTUALHOST
		#Creamos la carpeta del DocumentRoot y el index.html para el usuario
		os.system('mkdir /srv/www/%s' % usuario)
		os.system('cp /var/www/index.html /srv/www/%s' % usuario)

		#Creamos el virtualhost en apache2
		#Abrimos la plantilla en modo lectura
		plantilla = open('/srv/plantillas/vhost','r')

		#Leemos las líneas y las guardamos en una variable
		contenido = plantilla.read()
		plantilla.close()

		#Creamos y abrimos el virtualhost en modo escritura
		os.system('touch /etc/apache2/sites-available/%s' % dominio)
		nuevo_vhost = open('/etc/apache2/sites-available/'+dominio,'w')

		#Reemplazamos en el contenido el usuario y el dominio
		contenido = contenido.replace("//usuario//",usuario) 
		contenido = contenido.replace("//dominio//",dominio) 
		nuevo_vhost.write(contenido)
		nuevo_vhost.close()

		#Activamos el nuevo virtual host
		os.system("a2ensite "+dominio+" 1>/dev/null 2>/dev/null")
		print "El virtualhost del usuario ha sido creado"

		#DNS
		#Creamos las entradas DNS
		#Abrimos la plantilla de zonas en modo lectura
		p_zonas = open('/srv/plantillas/p_zonas','r')
		#Leemos las líneas y las guardamos en una variable
		contenido = p_zonas.read()
		p_zonas.close()
		#Sustituimos en la variable el dominio
		contenido = contenido.replace("//dominio//",dominio)
		#Abrimos el fichero de zonas en modo 'a' para añadir
		zonas = open('/etc/bind/named.conf.local','a')
		zonas.write('\n'+contenido)
		zonas.close()
		#Abrimos la plantilla de definicion de las zonas y metemos su contenido en una variable
		p_defzona = open('/srv/plantillas/p_defzona','r')
		contenido = p_defzona.read()
		p_defzona.close()
		#Sustituimos en la variable el dominio
		contenido = contenido.replace("//dominio//",dominio)
		#Creamos y abrimos en modo escritura el fichero con la definicion de la zona
		os.system('touch /var/cache/bind/db.'+dominio)
		definicionzona = open('/var/cache/bind/db.'+dominio,'w')
		definicionzona.write(contenido)
		definicionzona.close()
		print "La zona DNS del usuario ha sido creada"


		#Creamos las contraseñas para ftp y mysql
		contra_ftp = GenPasswd(7)
		contra_mysql = GenPasswd(7)

		#FTP
		#Creamos el usuario ftp en la base de datos ftpd
		#Ya estamos conectados a la base de datos porque no cerramos la conexión
		#Buscamos el uid maximo
		cursor = conn.cursor()
		query = "select max(uid) from usuarios;"
		cursor.execute(query)
		#Obtenemos un elemento del cursor
		uidmax = cursor.fetchone()
		if uidmax[0] == None:
			uid = "2100"
		else:
			uid = str(int(uidmax[0])+1)
		cursor.close()

		cursor = conn.cursor()
		query = "insert into usuarios values ('"+usuario+"',password('"+contra_ftp+"'),"+uid+",2005,'/srv/www/"+usuario+"','/bin/bash',1,'"+dominio+"');"
		#query = "insert into usuarios values ('%s',password('%s'),'%s','2005','/srv/ftp/%s','/bin/bash',1,'%s');" % usuario contra_ftp uid usuario dominio
		cursor.execute(query)
		conn.commit()
		cursor.close()
		#Cerramos la conexión
		conn.close()
		#Le damos permisos a la carpeta del usuario
		os.system('chown -R '+uid+':www-data /srv/www/'+usuario)
		os.system('chmod -R 770 /srv/www/'+usuario)
		print "------Datos Usuario FTP--------"
		print "Usuario: %s" % usuario
		print "Contraseña: %s" % contra_ftp

		#PHPMYADMIN
		#Abrimos nueva conexión a la base de datos
		conn = MySQLdb.connect(host="localhost",user="root",passwd="root")
		cursor = conn.cursor()
		query = "create database my"+usuario
		cursor.execute(query)
		conn.commit()

		query = "grant all on my"+usuario+".* to my"+usuario+"@localhost identified by '"+contra_mysql+"';"
		cursor.execute(query)
		conn.commit()
		cursor.close()
		conn.close()
		print "------Datos usuario mysql------"
		print "Usuario: my"+usuario
		print "Contraseña: "+contra_mysql

		#Creamos el virtualhost del usuario para acceder a phpmyadmin
		#Abrimos la plantilla en modo lectura
		plantilla = open('/srv/plantillas/mysqlhost','r')

		#Leemos las líneas y las guardamos en una variable
		contenido = plantilla.read()
		plantilla.close()

		#Creamos y abrimos el virtualhost en modo escritura
		os.system('touch /etc/apache2/sites-available/mysql_%s' % usuario)
		mysql_host = open('/etc/apache2/sites-available/mysql_'+usuario,'w')

		#Reemplazamos en el contenido el usuario y el dominio
		contenido = contenido.replace("//usuario//",usuario) 
		contenido = contenido.replace("//dominio//",dominio) 
		mysql_host.write(contenido)
		mysql_host.close()

		#Activamos el nuevo virtual host
		os.system("a2ensite mysql_"+usuario+" 1>/dev/null 2>/dev/null")
		print "El host virtual para phpmyadmin del usuario ha sido creado"



		#Reiniciamos servicios
		os.system("service apache2 restart 1>/dev/null 2>/dev/null")
		os.system("service bind9 restart 1>/dev/null 2>/dev/null")
		os.system("service proftpd restart 1>/dev/null 2>/dev/null")
