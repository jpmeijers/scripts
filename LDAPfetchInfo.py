#!/usr/bin/python
'''
	Created on 17 Mar 2014

    Pull study info from the LDAP address book for a list of student numbers
    Copyright (C) 2014  JP Meijers & Jacques Marais

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
import pandas as pd
from pprint import pprint
import ldap
import getpass

csv_file = 'Temp - students.csv'
data_column = 2

faculty=str(raw_input('Faculty: '))
studentnr=str(raw_input('Student Nr: '))
password=getpass.getpass('Your password: ')

print faculty, studentnr, password

if __name__ == '__main__':

	df = pd.read_csv(csv_file, sep=',')

	data = list(df['Student'])

	try:
		ldapcon = ldap.initialize('ldap://stbad01.stb.sun.ac.za')
		username = 'cn='+studentnr+',ou='+faculty+',ou=STUD,dc=stb,dc=sun,dc=ac,dc=za'
		result = ldapcon.bind_s(username,password, ldap.AUTH_SIMPLE)
		# pprint(result)

	except ldap.LDAPError, e:
		print "Error\n"+str(e)

	except ldap.INVALID_CREDENTIALS, e :
		print str(e)

	for number in data:
		#number="17965098"

		baseDN="ou=STUD,dc=stb,dc=sun,dc=ac,dc=za"
		searchScope=ldap.SCOPE_SUBTREE
		searchFilter="(cn="+str(number)+")"
		retrieveAttributes=None

		try:
			ldap_result_id = ldapcon.search(baseDN, searchScope, searchFilter, retrieveAttributes)
			result_set = []
			while 1:
				#print "reading result"
				result_type, result_data = ldapcon.result(ldap_result_id, 0)
				#print "result read"
				if (result_data == []):
					break
				else:
					## here you don't have to append to a list
					## you could do whatever you want with the individual entry
					## The appending to list is just for illustration. 
					if result_type == ldap.RES_SEARCH_ENTRY:
						result_set.append(result_data)
						#print "Appending entry"
					else:
						print "Not a result search entry"

			#pprint (result_set)
			print str(number)+";",
			try:
				print result_set[0][0][1]['department'][0] + ";",
			except:
				print ";",

			try:
				print result_set[0][0][1]['title'][0] + ";",
			except:
				print ";",

			try:
				print result_set[0][0][0]
			except:
				print ""

		except ldap.LDAPError, e:
			print "LDAP search error\n"+str(e)
