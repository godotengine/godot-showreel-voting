#!/usr/bin/env bash
set -euo pipefail

# Helper constants
RED='\033[1;31m'
NC='\033[0m'

# Helper methods
function ask {
	dialog \
		--title "Showreel Configuration" \
		--inputbox "${1}" \
		--stdout \
		--keep-tite \
		0 60 ${2:-}
}



# .=================================================================.
# | Configuration Values                                            |
# '================================================================='

# Git Repo
git_repo="https://github.com/godotengine/godot-showreel-voting.git"
git_branch="master"

# File Paths
fqdn="$(ls /var/www)"
www_dir="/var/www/${fqdn}"
app_dir="${www_dir}/app"
dotenv="${app_dir}/.env"
apache_conf="/etc/apache2/sites-enabled/000-default-le-ssl.conf"

# Known Secrets (provides mysql_showreel_pass)
source /root/.hcloud_password

# User Questions
keycloak_host="$(ask "Keycloak hostname (without http in front):")"
keycloak_realm="$(ask "Keycloak realm:" "master")"
keycloak_client_id="$(ask "Keycloak client ID:" "showreel")"
keycloak_client_secret="$(ask "Keycloak client secret:")"
keycloak_role_staff="$(ask "Keycloak role for staff:" "staff")"
keycloak_role_superuse="$(ask "Keycloak role for superusers:" "admin")"



# .=================================================================.
# | Validate Paths                                                  |
# '================================================================='

if [ ! -d "${www_dir}" ]; then
	printf "\n${RED}Could not find website directory at expected location:${NC}\n"
	printf "${RED}${www_dir}${NC}\n\n"
	exit 1
fi
if [ ! -f "${apache_conf}" ]; then
	printf "\n${RED}Could not find apache config at expected location:${NC}\n"
	printf "${RED}${apache_conf}${NC}\n\n"
	exit 1
fi
if [ -d "${app_dir}" ]; then
	printf "\n${RED}App was already set up at the following location:${NC}\n"
	printf "${RED}${app_dir}${NC}\n"
	printf "Please use the .env file for further configuration.\n\n"
	exit 1
fi



# .=================================================================.
# | Setup Application                                               |
# '================================================================='

# Clone repo into app directory and use that as workdir
git clone --branch "${git_branch}" "${git_repo}" "${app_dir}"
pushd "${app_dir}"

# Create .env config file
# (secret key will be added later once django is installed)
cat << EOF > "${dotenv}"
# General
GDSHOWREEL_DJANGO_ALLOWED_HOSTS = "${fqdn}"
GDSHOWREEL_STATIC_ROOT = "${app_dir}/static"

# Database
GDSHOWREEL_DATABASE_NAME = "showreel"
GDSHOWREEL_DATABASE_USER = "showreel"
GDSHOWREEL_DATABASE_PASSWORD = "${mysql_showreel_pass}"
GDSHOWREEL_DATABASE_HOST = "localhost"
GDSHOWREEL_DATABASE_PORT = "3306"

# Keycloak
GDSHOWREEL_KEYCLOAK_HOSTNAME = "${keycloak_host}"
GDSHOWREEL_KEYCLOAK_REALM = "${keycloak_realm}"
GDSHOWREEL_OIDC_RP_CLIENT_ID = "${keycloak_client_id}"
GDSHOWREEL_OIDC_RP_CLIENT_SECRET = "${keycloak_client_secret}"
GDSHOWREEL_KEYCLOAK_STAFF_ROLE = "${keycloak_role_staff}"
GDSHOWREEL_KEYCLOAK_SUPERUSER_ROLE = "${keycloak_role_superuse}"

# Crypthography
EOF

# Create apache config
cat << EOF > "${apache_conf}"
<IfModule mod_ssl.c>

WSGIDaemonProcess ${fqdn} python-home=${app_dir}/venv python-path=${app_dir}
WSGIScriptAlias / ${app_dir}/gdshowreelvote/wsgi.py process-group=${fqdn}

Alias /static/ ${app_dir}/static/

<VirtualHost *:443>
	ServerAdmin contact@godotengine.org
	ServerName ${fqdn}

	<Directory ${app_dir}/static>
		Require all granted
	</Directory>

	<Directory ${app_dir}/gdshowreelvote>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

	ErrorLog \${APACHE_LOG_DIR}/${fqdn}.error.log
	CustomLog \${APACHE_LOG_DIR}/${fqdn}.access.log combined

SSLCertificateFile /etc/letsencrypt/live/${fqdn}/fullchain.pem
SSLCertificateKeyFile /etc/letsencrypt/live/${fqdn}/privkey.pem
Include /etc/letsencrypt/options-ssl-apache.conf
</VirtualHost>
</IfModule>
EOF

# Setup django app inside venv
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
secret_key="$(python - <<-EOF
	from django.core.management.utils import get_random_secret_key 
	print(get_random_secret_key())
EOF
)"
echo "GDSHOWREEL_DJANGO_SECRET_KEY=\"${secret_key}\"" >> "${dotenv}"
python manage.py migrate
python manage.py collectstatic
deactivate

# Leave app directory
popd

# Remove default index file
rm "${www_dir}/index.php" || true

# Restart apache
systemctl restart apache2.service
