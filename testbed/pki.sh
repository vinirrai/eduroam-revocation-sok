#!/bin/bash
# Build a tiny "UNC" PKI: a CA, a RADIUS server cert, an OCSP signer and device certs.
# usage: pki.sh init | pki.sh issue <name> <days|+SECONDS> | pki.sh revoke <name> | pki.sh crl
set -e
TB=$(cd "$(dirname "$0")" && pwd)
P=${PKI_DIR:-$TB/pki}
cnf=$P/ca.cnf

mk_cnf() {
cat > $cnf <<EOF
[ ca ]
default_ca = unc
[ unc ]
dir = $P
database = \$dir/index.txt
new_certs_dir = \$dir/newcerts
certificate = \$dir/ca.crt
private_key = \$dir/ca.key
serial = \$dir/serial
crlnumber = \$dir/crlnumber
default_md = sha256
default_crl_days = 7
policy = any
unique_subject = no
copy_extensions = none
[ any ]
commonName = supplied
[ req ]
distinguished_name = dn
prompt = no
[ dn ]
CN = placeholder
[ v3_ca ]
basicConstraints = critical,CA:true
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
[ server ]
basicConstraints = CA:false
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:radius.unc.test
authorityInfoAccess = OCSP;URI:http://127.0.0.1:8888/
[ client ]
basicConstraints = CA:false
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
authorityInfoAccess = OCSP;URI:http://127.0.0.1:8888/
crlDistributionPoints = URI:http://127.0.0.1:8899/unc.crl
[ ocsp ]
basicConstraints = CA:false
keyUsage = critical,digitalSignature
extendedKeyUsage = OCSPSigning
EOF
}

issue() { # name ext validity(days or +seconds)
  local n=$1 ext=$2 v=$3 cn=$4
  openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
    -keyout $P/$n.key -out $P/$n.csr -subj "/CN=$cn" 2>/dev/null
  if [[ $v == +* ]]; then
    local end=$(date -u -d "@$(( $(date +%s) + ${v#+} ))" +%Y%m%d%H%M%SZ)
    openssl ca -batch -config $cnf -extensions $ext -enddate $end -in $P/$n.csr -out $P/$n.crt 2>/dev/null
  else
    openssl ca -batch -config $cnf -extensions $ext -days $v -in $P/$n.csr -out $P/$n.crt 2>/dev/null
  fi
}

crl() {
  openssl ca -batch -config $cnf -gencrl -out $P/crl.pem 2>/dev/null
  rm -rf $P/capath && mkdir -p $P/capath
  cp $P/ca.crt $P/crl.pem $P/capath/
  openssl rehash $P/capath 2>/dev/null
}

case $1 in
init)
  rm -rf $P && mkdir -p $P/newcerts && touch $P/index.txt && echo 1000 > $P/serial && echo 1000 > $P/crlnumber
  mk_cnf
  openssl req -x509 -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 3650 \
    -keyout $P/ca.key -out $P/ca.crt -subj "/CN=UNC Test Wi-Fi CA" -config $cnf -extensions v3_ca 2>/dev/null
  issue server server 730 radius.unc.test
  issue ocsp ocsp 730 "UNC Test OCSP Responder"
  crl ;;
issue)  issue $2 client $3 "$2@unc.test" ;;
issue-server) issue $2 server $3 radius.unc.test ;;
revoke) openssl ca -batch -config $cnf -revoke $P/$2.crt -crl_reason affiliationChanged 2>/dev/null; crl ;;
crl) crl ;;
esac
