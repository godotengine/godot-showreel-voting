# Godot showreel rating website

This repository hosts the Godot showreel website. It is a video submission and
voting platform meant to help contributors selecting the best videos to
showcase Godot engine.

It uses Keycloak as the authentication provider.

## Web application setup

The repository is built as a docker-compose project. The `gdshowreelvote`
folder contains the main application as a standard django project. When using
docker-compose to start the service, it also starts an nginx proxy and a
postgres database. The `secrets`, `certificates` and `pgdata` folders are
defaults folders used as mount points, but they may not be useful in a
production environment.

The next section requires a good understanding of hwo to use docker compose,
ngingx and a postgres database. The use of docker-compose should simplify the
processus a lot but setting up everything in a real production environment
might be more complex.

### Keycloak setup

To setup your keycloak instance you will have at least to:
- Connect to you keycloak instance (the default credential for the local
  keycloak instance are admin/admin).
- Create a new client.
- Setup the client access type as "confidential".
- Get the secret in the Crendetials section, it's needed in the web app
  configuration.
- In the Mappers section, create a **built-in** mapper for "realm roles" and
  another for "email".
- If you are using the default admin account, give it a fake email address in
  keycloack's user configuration and check the "email verified" checkbox.

### Running into testing environment

The default configuration is the one used for testing, so you don't have to
modify it. However you will need to:
- Add a certificate in to the `./certificates` folder. It should contain two
 files named `showreel.godotengine.org.crt` and `showreel.godotengine.org.key`,
 which are the private key and the certificate for the website. In a testing
 environment, you should probably use a self-signed certificate,
- Create five files in the `./secrets` folder, named
  `gdshowreel_django_db_root_password.txt`,
  `gdshowreel_django_db_password.txt`, `gdshowreel_django_secret.txt`,
  `gdshowreel_oidc_rp_client_id.txt` and
  `gdshowreel_oidc_rp_client_secret.txt`. The first threee should contains
  random passwords, they are used to, respectively, setup the mysql root
  password, communicate between django and the database, and the internal
  django secret. The last two ones are should be provided by the keycloak
  instance, when setting up a client.

By default, the `./pgdata` will contain the database data.

With docker-compose installed, you should then be able to buil and run the
app using: `docker-compose build; docker-compose up nginx`

Note that, the first time you run the application, you might need to setup the
django database by running: `docker-compose run web ./manage.py migrate`. Any
change to django models might also require running `docker-compose run web
./manage.py makemigrations` first. But that's in Django's documentation.

The app is, by default, listening on the default HTTP and HTTPS port (80 and
433), but any HTTP request will be redirected to HTTPS. Accessing the keycloak
server is possible via the 8080 port on the localhost machine, however, by
default, the testing environment will redirect you to `keycloak:8080`. As a
consequence, `keycloak` should be added to `/etc/hosts` to redirect to
`127.0.0.1`.

### Running into production

To run in production, you will have at least to:
- set `DJANGO_DEBUG=False` and ` DJANGO_ALLOWED_HOSTS=<the_website_domain>` in
  the *web* service's environment variables configuration,
- possibly modify the mount point for your database data
  `<pgdata_folder>:/var/lib/postgresql` in `docker-compose.yml`,
- possibly modify the mount point for your certificates
  `<certificates_folder>:/etc/nginx/ssl/` in `docker-compose.yml`,
- possibly modify the location of your secrets in  `docker-compose.yml` (if
  they are not in the `./secrets` folder),
- setup your certificates and secrets as you would do for the testing use case.

This should be enough to run in production with docker compose. For other more
complex use case, each of the postagres, nginx, and web application components
could require specific setup. As a tip on how to configure each one of them,
you might have a look to the files:

- `nginx/nginx.conf` for the nginx proxy configuration,
- `docker-compose.yml` for the postgres database configuration,
- `gdshowreelvote/gdshowreelvote/settings.py` for the web app.

Indeed, you should also refer to the documentations of each of those components
to undertand what those file do.

### Web application standablone setup

As it may be ran in an independent setup too, the web application also exposes
some of its settings as environment variables. Here is the list of exposed
settings and their default values:

```
GDSHOWREEL_DJANGO_SECRET_KEY = <provided via docker secrets> # Django's SECRET_KEY
GDSHOWREEL_DJANGO_DEBUG = "" # Whether or not to run django in debug mode
GDSHOWREEL_DJANGO_ALLOWED_HOSTS = "" # Allowed hosts

GDSHOWREEL_DATABASE_NAME = "gdshowreel" # Database name
GDSHOWREEL_DATABASE_USER = "mysql" # Database user name
GDSHOWREEL_DATABASE_PASSWORD = <provided via docker secrets> # Database password
GDSHOWREEL_DATABASE_HOST = "database" # Database host
GDSHOWREEL_DATABASE_PORT = "" # database port

GDSHOWREEL_SERVE_STATICS = "yes" # Whether or not django should serve static files
GDSHOWREEL_DJANGO_STATIC_ROOT = "/var/www/showreel.godotengine.org/static/" # Location of the static files

GDSHOWREEL_OIDC_RP_CLIENT_ID = <provided via docker secrets> # Keycloak OICD client IC
GDSHOWREEL_OIDC_RP_CLIENT_SECRET = <provided via docker secrets> # Keycloak OICD client password

GDSHOWREEL_KEYCLOAK_REALM = "master" # Keycloak realm for the application
GDSHOWREEL_KEYCLOAK_HOSTNAME = "keycloak:8080" # Keycloak host
GDSHOWREEL_KEYCLOAK_ROLES_PATH_IN_CLAIMS = "realm_access,roles" # Path to roles in keycloak claims
GDSHOWREEL_KEYCLOAK_STAFF_ROLE = "staff" # Staff role in keycloak. Staff has access to the administration interface.
GDSHOWREEL_KEYCLOAK_SUPERUSER_ROLE = "admin" # Superusers role in keycloak. Same as staff plus a few more permissions.

# OICD endpoints
GDSHOWREEL_OIDC_OP_AUTHORIZATION_ENDPOINT = "http://{KEYCLOAK_HOSTNAME}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"
GDSHOWREEL_OIDC_OP_TOKEN_ENDPOINT = "http://{KEYCLOAK_HOSTNAME}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
GDSHOWREEL_OIDC_OP_USER_ENDPOINT = "http://{KEYCLOAK_HOSTNAME}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
GDSHOWREEL_OIDC_OP_JWKS_ENDPOINT = "http://{KEYCLOAK_HOSTNAME}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
GDSHOWREEL_OIDC_OP_LOGOUT_ENDPOINT = "http://{KEYCLOAK_HOSTNAME}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/logout"

GDSHOWREEL_VOTE_MAX_SUBMISSIONS_PER_SHOWREEL = 3 # How many submissions users can make to the same showreel
GDSHOWREEL_VOTE_ONLY_STAFF_CAN_VOTE = "yes" # If yes, only users with the staff role can rate the showreel videos
```

## License

This website's code is provided under the MIT license.
