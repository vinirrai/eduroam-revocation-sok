#!/usr/bin/env python3
"""Generate a FreeRADIUS config dir for one revocation mechanism.

usage: gen.py <outdir> <mechanism> [tls_max]
mechanisms: baseline | crl | ocsp | directory | all
"""
import os, re, shutil, sys

TB = os.path.dirname(os.path.abspath(__file__))
PKI = os.path.join(TB, "pki")
out, mech = sys.argv[1], sys.argv[2]
tls_max = sys.argv[3] if len(sys.argv) > 3 else "1.2"
crl_reload = os.environ.get("CRL_RELOAD", "30")

if os.path.exists(out):
    shutil.rmtree(out)
shutil.copytree("/etc/freeradius/3.0", out, symlinks=True)
os.makedirs(os.path.join(out, "logs"), exist_ok=True)
os.makedirs(os.path.join(out, "run"), exist_ok=True)

conf = open(os.path.join(out, "radiusd.conf")).read()
conf = conf.replace("raddbdir = /etc/freeradius/3.0", f"raddbdir = {out}")
conf = conf.replace("logdir = /var/log/freeradius", f"logdir = {out}/logs")
conf = conf.replace("run_dir = ${localstatedir}/run/${name}", f"run_dir = {out}/run")
conf = re.sub(r"\n\s*user = freerad", "\n#user", conf)
conf = re.sub(r"reject_delay = \d+", "reject_delay = 0", conf)
conf = re.sub(r"\n\s*group = freerad", "\n#group", conf)
open(os.path.join(out, "radiusd.conf"), "w").write(conf)

# only our site
for f in os.listdir(os.path.join(out, "sites-enabled")):
    os.remove(os.path.join(out, "sites-enabled", f))
os.remove(os.path.join(out, "mods-enabled", "eap"))

use_crl = mech in ("crl", "all")
use_ocsp = mech in ("ocsp", "all")
use_dir = mech in ("directory", "all")

crl_lines = f"check_crl = yes\n\t\tca_path_reload_interval = {crl_reload}" if use_crl else "check_crl = no"
vs_line = "virtual_server = check-eap-tls" if use_dir else ""

eap = f"""
eap {{
	default_eap_type = tls
	timer_expire = 60
	ignore_unknown_eap_types = no
	max_sessions = ${{max_requests}}
	tls-config tls-common {{
		private_key_file = {PKI}/server.key
		certificate_file = {PKI}/server.crt
		ca_file = {PKI}/ca.crt
		ca_path = {PKI}/capath
		{crl_lines}
		cipher_list = "DEFAULT"
		tls_min_version = "1.2"
		tls_max_version = "{tls_max}"
		cache {{
			enable = no
		}}
		verify {{
		}}
		ocsp {{
			enable = {"yes" if use_ocsp else "no"}
			override_cert_url = yes
			url = "http://127.0.0.1:8888/"
			use_nonce = yes
			timeout = 2
			softfail = no
		}}
	}}
	tls {{
		tls = tls-common
		{vs_line}
	}}
}}
"""
open(os.path.join(out, "mods-enabled", "eap"), "w").write(eap)

site = """
server unc {
	listen {
		type = auth
		ipaddr = 127.0.0.1
		port = 18120
	}
	client localhost {
		ipaddr = 127.0.0.1
		secret = testing123
	}
	authorize {
		eap {
			ok = return
		}
	}
	authenticate {
		eap
	}
	post-auth {
		Post-Auth-Type REJECT {
			eap
		}
	}
}
"""
open(os.path.join(out, "sites-enabled", "unc"), "w").write(site)

if use_dir:
    # Runs once the device cert has been verified. Ask the directory if this person is still enrolled.
    check = """
server check-eap-tls {
	authorize {
		update control {
			&Tmp-String-0 := "%{ldap:ldap:///ou=people,dc=unc,dc=test?employeeType?sub?(mail=%{TLS-Client-Cert-Common-Name})}"
		}
		if (&control:Tmp-String-0 != "student") {
			reject
		}
		update control {
			&Auth-Type := Accept
		}
	}
}
"""
    open(os.path.join(out, "sites-enabled", "check-eap-tls"), "w").write(check)
    ldap = """
ldap {
	server = 'ldap://127.0.0.1:3890'
	identity = 'cn=admin,dc=unc,dc=test'
	password = secret
	base_dn = 'dc=unc,dc=test'
	user {
		base_dn = "ou=people,${..base_dn}"
		filter = "(mail=%{%{Stripped-User-Name}:-%{User-Name}})"
	}
	pool {
		start = 1
		min = 1
		max = 4
		spare = 1
		uses = 0
		retry_delay = 1
		lifetime = 0
		idle_timeout = 60
	}
}
"""
    open(os.path.join(out, "mods-enabled", "ldap"), "w").write(ldap)

print(out)
