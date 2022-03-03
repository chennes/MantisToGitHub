# -*- coding: utf-8 -*-

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Chris Hennes <chennes@pioneerlibrarysystem.org>    *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENSE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************



#############################################################################
# REQUIRED CONFIGURATION SETTINGS

MANTIS_DB='' # The name of the MySQL database to select from
MANTIS_DB_USER='' # The user to log into the database with
MANTIS_DB_PASS=''# The password for that DB user
MANTIS_REPORTERID='' # The numeric user ID to assign these posts to

BUG_MAP_CSV='' # The path to the CSV file with the mapping in it

#############################################################################




import mysql.connector
import time

try:
    connection = mysql.connector.connect(
            host='localhost',
            database = MANTIS_DB,
            user = MANTIS_DB_USER,
            password = MANTIS_DB_PASS,
        )
except mysql.connector.Error as e:
    print (f"Failed to connect to Mantis database:\n{str(e)}\n")
    exit(1)

cursor = connection.cursor()

def add_mantis_note(mantis_id, github_id):
    note = f"This ticket has been migrated to GitHub as issue [url=https://github.com/FreeCAD/FreeCAD/issues/{github_id}]{github_id}[/url]."
    
    # Two entries needed: first, we create the entry in mantis_bugnote_text_table
    sql_bugnote = "INSERT INTO mantis_bugnote_text_table (id,note) VALUES (NULL,%s)"
    cursor.execute(sql_bugnote, (note,))

    # Finally, create the entry in mantis_bugnote_table
    bugnote_data = (mantis_id,MANTIS_REPORTERID,10,0,0,int(time.time()),int(time.time()))
    print (bugnote_data)
    sql_reference = "INSERT INTO mantis_bugnote_table (id,bug_id,reporter_id,bugnote_text_id,view_state,note_type,note_attr,time_tracking,last_modified,date_submitted) VALUES (NULL,%s,%s,LAST_INSERT_ID(),%s,%s,NULL,%s,%s,%s)"
    cursor.execute(sql_reference, bugnote_data)

with open (BUG_MAP_CSV, "r") as f:
    lines = f.readlines()
    for line in lines:
        mantis_id, _, github_id = line.partition(",")
        if mantis_id and github_id:
            try:
                m = int(mantis_id)
                g = int(github_id)
                add_mantis_note(m, g)
            except Exception as e:
                print (f"Failed to create note in Mantis bug {mantis_id}, for GitHub bug {github_id}: {str(e)}. Continuing...")

connection.commit()
cursor.close()
connection.close()

