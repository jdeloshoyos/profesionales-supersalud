# coding=Latin-1

# Script para descargar todos los registros de médicos en el portal de la Superintendencia de Salud,
# incluyendo su universidad, año de egreso, etc.
# 2011 por Jaime de los Hoyos M.

# Historial de versiones:
# 1.05:
# - Incluye medición de lapso de tiempo en proceso
# - Descarga todos los profesionales
# 1.04:
# - Primera versión que logra una descarga completa de los médicos

# Copyright 2011 Jaime de los Hoyos M.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
# of the Software, and to permit persons to whom the Software is furnished to do 
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.

version="1.05"

import urllib
import re
import sys
import time
import msvcrt    # Para detectar teclas presionadas
import traceback    # Para debugging
from datetime import datetime

############################################
# Funciones comunes                        #
############################################

# descargaUrl: Descarga y devuelve, como un string, el HTML del URL que se le pase como parámetro.
def descargaUrl(url):
    f = urllib.urlopen(url)
    s = f.read()
    f.close()
    return s

# encuentraPatron: Devuelve el primer grupo de paréntesis en un match de regex.
# El regex pasado debe tener al menos un grupo encerrado en paréntesis
def encuentraPatron(regex, contenido, grupo):
    m=re.search(regex, contenido)
    if (m==None):
        # La regex no matcheó en el contenido... Devolvemos un string vacío.
        return ""
    else:
        return m.group(grupo)


# formateaFecha: Pequeña función para pasar de mm-dd-aaaa a dd-mm-aaaa
def formateaFecha(fecha):
    # Algunos registros no tienen fecha de nacimiento (especialmente para extranjeros)... Controlamos ese caso especial.
    if (fecha==""):
        buffer=""
    else:
        m=re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', fecha)
        buffer=m.group(2)+"-"+m.group(1)+"-"+m.group(3)
    return buffer

# extraeEspecialidad: Retorna la glosa en el link de "Ver más antecedentes..."
def extraeEspecialidad(url):
    # Antecedente [^<]+</font></td></tr>\s+<tr valign="top"><td width="100%" colspan="2"><font size="2" face="Arial">([^<]+)</font>
    contenido=descargaUrl(url)
    glosa=encuentraPatron('Antecedente [^<]+</font></td></tr>\s+<tr valign="top"><td width="100%" colspan="2"><font size="2" face="Arial">([^<]+)</font>', contenido, 1)
    # Ya que este texto es básicamente libre, podría eventualmente contener el caracter delimitador (;). Testeamos esto, y de ser así, encerramos
    # el texto entre comillas de acuerdo a la "especificación" CSV.
    if (glosa.find(';')>-1):
        # Tiene al menos un delimitador. Hacemos los cambios necesarios
        glosa='"'+glosa.replace('"', '""')+'"'
    return glosa

# parseaFichaProfesional: Descarga el URL pasado y parsea los datos de la ficha inicial del médico.
def parseaFichaProfesional(url):
    contenido=descargaUrl(url)
    # Acá hay algo interesante. En Python, si queremos que un string no le de interpretación especial al caracter de escape, simplemente
    # antecedemos el string (antes de la primera comilla) con una r. Es parecido, por ejemplo, a usar en C# @"Hola\!"
    no_registro=encuentraPatron(r'Nro de registro :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    fecha_registro=encuentraPatron(r'Fecha de registro :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    rut=encuentraPatron(r'Rut :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    rut_dv=encuentraPatron(r'Rut :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">[^<]*</font><font face="Verdana">-</font><font face="Verdana">([\dkK])</font>', contenido, 1)
    nombre=encuentraPatron(r'Nombre Completo:</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    ap_pat=encuentraPatron(r'Nombre Completo:</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font><font face="Verdana"> </font><font face="Verdana">([^<]*)</font><font face="Verdana"> </font><font face="Verdana">([^<]*)</font>', contenido, 2)
    ap_mat=encuentraPatron(r'Nombre Completo:</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font><font face="Verdana"> </font><font face="Verdana">([^<]*)</font><font face="Verdana"> </font><font face="Verdana">([^<]*)</font>', contenido, 3)
    sexo=encuentraPatron(r'Sexo </font>\s*<font [^>]+>:</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    nacion=encuentraPatron(r'Nacionalidad</font>\s*<font [^>]+> :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    fecha=encuentraPatron(r'Fecha Nacimiento</font>\s*<font [^>]+> :</font>\s*</td>\s*<td width="81%">\s*<font face="Verdana">([^<]*)</font>', contenido, 1)
    
    # Algunas conversiones necesarias. No entiendo por qué el RUT y las fechas llegan cambiados... Quick and dirty solution.
    rut=rut.replace(',', '.')
    fecha_registro=formateaFecha(fecha_registro)
    fecha=formateaFecha(fecha)
    
    buffer=no_registro+";"+fecha_registro+";"+rut+"-"+rut_dv+";"+nombre+";"+ap_pat+";"+ap_mat+";"+sexo+";"+nacion+";"+fecha+";"
    #buffer=buffer.decode('utf-8')
    #buffer=buffer.encode('latin-1')
    
    # Extraemos la lista de especialidades y URLs con la glosa extendida.
    lista_titulos=re.findall('src="/icons/ecblank.gif" border="0" alt=""><font face="Verdana">[^:]+: ([^<]+)</font></td><td><u><font face="Verdana"><a href="([^"]+)">Ver m.s antecedentes</a>', contenido)
    
    # Interesante, re.findall, si se le pasa una regex con varios grupos (), devuelve una lista con todos los matches encontrados, en que
    # cada elemento de la lista es a su vez una lista cuyos miembros son lo capturado por los grupos en el orden correspondiente. Práctico!
    for i in lista_titulos:
        temp=i[0]
        #temp=temp.decode('utf-8')
        #temp=temp.encode('latin-1')
        buffer=buffer+temp+";"
        buffer=buffer+extraeEspecialidad("http://webhosting.superdesalud.gob.cl"+i[1])+";"
    
    # src="/icons/ecblank.gif" border="0" alt=""><font face="Verdana">[^:]+: ([^<]+)</font></td><td><u><font face="Verdana"><a href="([^"]+)">Ver m..s antecedentes</a>
    return buffer
    
# parseaLinksFichas: Extrae todos los links de profesionales presentes en una página índice
def parseaLinksFichas(contenido, esPrimera):
    lista_urls=re.findall(r'/bases/prestadoresindividuales.nsf/[^?]+\?OpenDocument', contenido)  # Esta regex es ligeramente distinta que para sólo los médicos.
    # map(function, list) permite aplicar una función a todos los miembros de una lista; en este caso, definí la función como una expresión lambda.
    # Ojo, que la lista modificada es devuelta por la función map (no modifica la lista original).
    out=map(lambda s: "http://webhosting.superdesalud.gob.cl"+s, lista_urls)
    # Si es desde la segunda página en adelante, excluimos el primer resultado.
    # Esto es debido a que de la segunda en adelante, el primer link a un médico es repetido de la anterior.
    if (esPrimera==False):  out.pop(0)  # Sacamos el primero de la lista.
    buffer=""
    for i in out:
        buffer=buffer+parseaFichaProfesional(i)+"\n"
        print "|",
    print
    return buffer


############################################
# Punto de entrada                         #
############################################

print "Descargador de profesionales de SuperSalud v"+version
print

# Obtenemos el nombre del archivo de salida
try:
    out_file=sys.argv[1]    # OJO, el argumento [0] ES EL SCRIPT PYTHON MISMO!!!!!!!
except:
    print "Forma de uso: descarga_medicos.py archivo_salida.csv"
    sys.exit(1)

# ¿Es un nombre de archivo válido?
try:
    f=open(out_file, 'w')
except:
    print "ERROR - No es posible abrir el archivo de salida: "+out_file
    sys.exit(1)

print "Procesando la lista de profesionales de la Superintendencia de Salud"
print "(Presione ESC para finalizar y procesar resultados parciales)"
hora_inicio=datetime.now()
print "Hora de inicio del proceso: ",
print hora_inicio

# Descargamos la primera página
#index_url="http://webhosting.superdesalud.gob.cl/bases/prestadoresindividuales.nsf/WebRegConsulta?OpenForm&~(AntecedentesRegistrados)~~~M%C3%A9dico%20Cirujano|-Todos-|Todas~1"
index_url="http://webhosting.superdesalud.gob.cl/bases/prestadoresindividuales.nsf/WebRegConsulta?OpenForm&~(RegistradosxApellido)~~~-Todos-~1"
contenido=descargaUrl(index_url)

# Obtenemos el total de páginas a procesar
m=re.search('P..gina \d{1,5} de (\d{1,5})', contenido)
# print m.group(0)    # Todo el match
num_paginas=int(m.group(1))    # El primer subpatrón (el total de páginas), convertido a int

# Parseamos los links de médicos presentes en esta página, y los agregamos a una lista
buffer=[]
buffer.append('no_registro;fecha_registro;rut;nombre;ap_paterno;ap_materno;sexo;nacionalidad;fecha_nacimiento;titulo1;titulo_glosa1;titulo2;titulo_glosa2;titulo3;titulo_glosa3;titulo4;titulo_glosa4;titulo5;titulo_glosa5;titulo6;titulo_glosa6;titulo7;titulo_glosa7;titulo8;titulo_glosa8;titulo9;titulo_glosa9;titulo10;titulo_glosa10\n')
print "Procesando pagina 1 de "+str(num_paginas)+" ("+str(1*100/num_paginas)+"%) ",
buffer.append(parseaLinksFichas(contenido, True))

# La segunda página parte con el índice 17. (1+16 por página) (en realidad son 17 por página... Desde la segunda página en adelante, el
# primero es repetido...)
pagina=2
indice=1+(pagina-1)*16

# Aquí parte el loop que recuperará todas las páginas desde la segunda en adelante.
while True:
    
    # A veces, la conexión al sitio se cae.
    # Si esto pasa, lo interceptamos y esperamos 10 segundos antes de reintentar.
    while True:
        try:
            #index_url="http://webhosting.superdesalud.gob.cl/bases/prestadoresindividuales.nsf/WebRegConsulta?OpenForm&Start="+str(indice)+"&~(AntecedentesRegistrados)~~~M%C3%A9dico%20Cirujano|-Todos-|Todas~"+str(indice)+"~"
            index_url="http://webhosting.superdesalud.gob.cl/bases/prestadoresindividuales.nsf/WebRegConsulta?OpenForm&Start="+str(indice)+"&~(RegistradosxApellido)~~~-Todos-~"+str(indice)+"~"
            contenido=descargaUrl(index_url)
            print "Procesando pagina "+str(pagina)+" de "+str(num_paginas)+" ("+str(pagina*100/num_paginas)+"%) ",
            buffer.append(parseaLinksFichas(contenido, False))
            break
        except:
            print "Error en la conexion, esperando 10 segundos para reintentar..."
            print sys.exc_info()
            print traceback.print_tb(sys.exc_info()[2])
            time.sleep(10)
    
    indice=indice+16
    pagina=pagina+1
    if (indice>(num_paginas-1)*16+1): break     # Llegamos al fin de las páginas   # (num_paginas-1)*16+1
    if (msvcrt.kbhit()):
        if (ord(msvcrt.getch()) == 27):   break   # Si se presiona ESC, salimos
    
# Escribimos al archivo de salida
print "Escribiendo resultados a archivo: "+out_file
buffer2=''.join(buffer)
f.write(buffer2)
f.close()

hora_fin=datetime.now()
lapso=hora_fin-hora_inicio
print "Hora de termino: ",
print hora_fin
print "Tiempo transcurrido: ",
print lapso
