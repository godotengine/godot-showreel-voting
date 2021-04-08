# Godot showreel rating website

This repository hosts the Godot showreel website. It is a video submission and
voting platform meant to help contributors selecting the best videos to
showcase Godot engine.

It uses Github as the authentication provider.

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

### Running into testing envronment

The default configuration is the one used for testing, so you don't have to
modify it. However you will need to:
- Add a certificate in to the `./certificates` folder. It should contain two
 files named `showreel.godotengine.org.crt` and `showreel.godotengine.org.key`,
 which are the private key and the certificate for the website. In a testing
 environment, you should probably use a self-signed certificate,
- Create four files in the `./secrets` folder, named
  `gdshowreel_django_db_root_password.txt`,
  `gdshowreel_django_db_password.txt`, `gdshowreel_django_secret.txt` and
  `gdshowreel_social_auth_github_secret.txt`.  The first two should contains
  random passwords, they are used to, respectively, setupm the mysql root
  password, communicate between django and the database, and as the internal
  django secret. The last one should contain an oauth token provided by Github
  (see their documentation).

By default, the `./pgdata` will contain the database data.

With docker-compose installed, shoud should then be able to buil and run the
app using: `docker-compose build; docker-compose up nginx`

Note that, the first time you run the application, you might need to setup the
django database by running: `docker-compose run web ./manage.py migrate`. Any
change to django models might also require running `docker-compose run web
./manage.py makemigratios` first. But that's in Django's documentation.

The app is, by default, listening on the default HTTP and HTTPS port (80 and
433), but any HTTP request will be redirected to HTTPS.

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

## License

This website's code is provided under the MIT license.
