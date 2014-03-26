#!/usr/bin/python
'''
    A simple script to change your Stellenbosch University network password
    enough times to change it back to the original. Bypassing the 10 times
    same password limit.
    Copyright (C) 2014  JP Meijers

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

import urllib, urllib2, base64
from pprint import pprint

username="12345678"
start_password_base="password"
start_password_number=1
password = start_password_base+str(start_password_number)

for i in range(50):
  new_pass = start_password_base+str(start_password_number+i+1)
  print "Changing password from \""+password+"\" to \""+new_pass+"\""
  
  data = urllib.urlencode({"username":username, "password":new_pass, "verify":new_pass, "operation":"Update"})
  
  request = urllib2.Request("https://maties2.sun.ac.za/rtad4/useradm/auth/passsync1.rtad", data)
  base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
  request.add_header("Authorization", "Basic %s" % base64string)   
  #pprint(request)
  result = urllib2.urlopen(request)
  
  print result.read()
  
  password = new_pass
  
print "Last set to: "+password
