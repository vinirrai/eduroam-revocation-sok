#!/bin/bash
# Install testbed dependencies on Ubuntu 24.04 (run as root).
set -e
export DEBIAN_FRONTEND=noninteractive
echo "slapd slapd/no_configuration boolean true" | debconf-set-selections
apt-get update -qq
apt-get install -y -qq freeradius freeradius-ldap eapoltest hostapd slapd ldap-utils openssl tcpdump python3
# The packaged services are not used; the testbed starts its own instances on custom ports.
systemctl disable --now freeradius slapd hostapd 2>/dev/null || true
echo "setup done"
