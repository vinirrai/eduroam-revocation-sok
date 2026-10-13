#!/bin/bash
# A stand-in for the Onyen directory: slapd on 127.0.0.1:3890, one entry per person.
# usage: ldap.sh start | ldap.sh stop | ldap.sh set <name> <student|alumni>
TB=$(cd "$(dirname "$0")" && pwd)
L=$TB/ldap
URI=ldap://127.0.0.1:3890
ADMIN="cn=admin,dc=unc,dc=test"
PW=secret
case $1 in
start)
  pkill -f "slapd.*3890" 2>/dev/null; sleep 0.5
  rm -rf $L && mkdir -p $L/db
  cat > $L/slapd.conf <<EOF
include /etc/ldap/schema/core.schema
include /etc/ldap/schema/cosine.schema
include /etc/ldap/schema/inetorgperson.schema
modulepath /usr/lib/ldap
moduleload back_mdb
pidfile $L/slapd.pid
database mdb
suffix "dc=unc,dc=test"
rootdn "$ADMIN"
rootpw $PW
directory $L/db
index mail eq
EOF
  slapd -f $L/slapd.conf -h "$URI" -u root
  sleep 1
  ldapadd -x -H $URI -D "$ADMIN" -w $PW >/dev/null <<EOF
dn: dc=unc,dc=test
objectClass: dcObject
objectClass: organization
o: UNC Test
dc: unc

dn: ou=people,dc=unc,dc=test
objectClass: organizationalUnit
ou: people
EOF
  for u in alice bob carol; do
  ldapadd -x -H $URI -D "$ADMIN" -w $PW >/dev/null <<EOF
dn: uid=$u,ou=people,dc=unc,dc=test
objectClass: inetOrgPerson
uid: $u
cn: $u
sn: $u
mail: $u@unc.test
employeeType: student
EOF
  done
  echo "ldap up" ;;
stop) pkill -f "slapd.*3890" ;;
set)
  ldapmodify -x -H $URI -D "$ADMIN" -w $PW >/dev/null <<EOF
dn: uid=$2,ou=people,dc=unc,dc=test
changetype: modify
replace: employeeType
employeeType: $3
EOF
;;
esac
