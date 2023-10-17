# Guided Deployment

## Overview
This will create a LAMP server that runs the showreel app via the WSGI apache
module. The database will be set up automatically. The only component that needs
manual configuration is the keycloak server, but you will be guided through the
process.

## Server Creation

1. Create a new server in the [Hetzner Cloud](https://console.hetzner.cloud/projects)
   with the following options:
	- In the image section select "**LAMP Stack**" from the available apps.
	- At the bottom enter the following cloud-init config:
	  ```
	  #include
	  https://raw.githubusercontent.com/godotengine/godot-showreel-voting/master/deployment/cloud_config.yml
	  ```
	- Configure the other options as you see fit, for example by selecting
      your SSH key.
2. Configure a domain in Cloudflare DNS to point to the new server. Then grab a
   cup of coffee and wait for the automatic cloud-init to finish. This may take
   5 minutes, you can see when it finishes as the CPU load goes back to zero in
   the Hetzner graphs for the server.
3. SSH into the server. You will now have to do some manual setup:
	1. Once prompted, enter the domain you set up in Cloudflare earlier.
	2. Proceed to activate certbot (once prompted) to get SSL certs.
	3. After the domain and certbot are correctly set up, enter the command
	   `showreel-guided-setup`. This will guide you through the first time
	   configuration. It will ask for values like the keycloak secret.
4. Congratulations! You should now have a working showreel app. A few important
   file paths (assuming the domain is `showreel.godotengine.org`, adjust if
   necessary):
	- `/var/www/showreel.godotengine.org/` is the path of the website. You will
	  find the clone of this repository in the `./app` subdirectory. Feel free
	  to creates copies of that as `./backup` before doing any changes or updates.
	  In the app directory you will also find the `.env` file which is the main
	  place for configuration. You can find possible options in the list of
	  [available settings](/README.md#available-settings) (be sure to prefix
	  them with `GDSHOWREEL_`).
	- `/etc/apache2/sites-enabled/000-default-le-ssl.conf` is the configuration
	  for the Apache server. It enables SSL and uses WSGI to run the django app.

## Operation

### Updates
Simply run the included `pull-update.sh` script. It will automatically perform the
following steps:
- pull newest version from git repo
- ensure any newly added python packages are installed
- run database migrations and collect static files
- restart apache systemd service

You can find the script in the root of the app directory.

### Components

#### Apache2 Server
You can control apache via `systemctl`, for example to restart the service you would
use `systemctl restart apache2.service`. The website configuration can be found at
`/etc/apache2/sites-enabled/000-default-le-ssl.conf`.

#### Django Showreel App
The showreel app has it's own virtual environment. You need to activate it before
you can interact with it:
```bash
# Adjust the domain name as necessary
cd /var/www/showreel.godotengine.org/app
source venv/bin/activate
python manage.py --help
```

#### MySQL Database
You can find the automatically generated passwords in `/root/.hcloud_password`.
With those you can use the `mysql -u showreel -p` command to inspect
and modify the database.
