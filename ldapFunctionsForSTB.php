<?php
/*
    LDAP functions to use with the Stellenbosch University network
    LDAP server. Authentication and info.
    Copyright (C) 2014  JP Meijers (and other: Solar, Verdi, Pada)

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
*/


define("LDAP_SERVER", "ldap://stbldap02.sun.ac.za");
define("BASE_DN", "O=su");

	function ldap_zm_getcontext($auth_user)
	{
		// connect to server
		if (!($ldap = ldap_connect(LDAP_SERVER)))
		{
			die("Could not connect to ldap server");
			return false;
		}

		// bind to server with fixed search username
		if (!(ldap_bind($ldap))) 
		{
			die("Unable to login on server");
		}

		if (!($search = ldap_search($ldap, "OU=users," . BASE_DN, "CN=" . $auth_user)))
		{
			die("Unable to search ldap server");
			return false;
		}

		$info = ldap_get_entries($ldap, $search);

		if ($info["count"] < 1)
		{
			return false;
		}

		ldap_close($ldap);

		return $info[0]["dn"];	
	}

function ldap_zm_getfullnames($auth_user)
	{
		// connect to server
		if (!($ldap = ldap_connect(LDAP_SERVER)))
		{
			die("Could not connect to ldap server");
			return false;
		}

		// bind to server with fixed search username
		if (!(ldap_bind($ldap))) 
		{
			die("Unable to login on server");
		}

		if (!($search = ldap_search($ldap, "OU=users," . BASE_DN, "CN=" . $auth_user)))
		{
			die("Unable to search ldap server");
			return false;
		}

		$info = ldap_get_entries($ldap, $search);

		if ($info["count"] < 1)
		{
			return false;
		}

		ldap_close($ldap);

		return $info[0];	
	//return $info;

	}

function ldap_zm_getname($auth_user)
	{
		// connect to server
		if (!($ldap = ldap_connect(LDAP_SERVER)))
		{
			die("Could not connect to ldap server");
			return false;
		}

		// bind to server with fixed search username
		if (!(ldap_bind($ldap))) 
		{
			die("Unable to login on server");
		}

		if (!($search = ldap_search($ldap, "OU=users," . BASE_DN, "CN=" . $auth_user)))
		{
			die("Unable to search ldap server");
			return false;
		}

		$info = ldap_get_entries($ldap, $search);

		if ($info["count"] < 1)
		{
			return false;
		}

		ldap_close($ldap);

		return $info[0]["fullname"][0];	
	//return $info;

	}








	function ldap_zm_password($auth_user, $auth_pass)
	{
		// connect to server
		if (!($ldap = ldap_connect(LDAP_SERVER)))
		{
			die("Could not connect to ldap server");
			return false;
		}

		// bind to server with fixed search username
		if (!(ldap_bind($ldap, $auth_user, $auth_pass)))
		{
			ldap_close($ldap);
			return false;
		}

		ldap_close($ldap);
		return true;
	}


	function ldap_zm_auth($auth_user, $auth_pass)
	{
		$getdc = (ldap_zm_getcontext($auth_user));

		if ($getdc)
		{
			if (ldap_zm_password($getdc, $auth_pass))
			{
				return true;
			}
		}

		return false;
	}


?>
