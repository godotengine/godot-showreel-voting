# Godot showreel rating website

This repository hosts the Godot Showreel webapp. It is a video submission and
voting platform meant to help contributors selecting the best videos to
showcase Godot engine.

It uses Keycloak as the authentication provider.


## Deployment
Please see the instructions for the [guided deployment](deployment/README.md).
This will configure most values for you. The informations below are only
provided for more advanced usecases and for local development.

## Application

### Structure
The showreel is implemented as a django app. You can find the main package and
entrypoints in `./gdshowreelvote`. The actual app logic is separated into the
`./vote` module. In the root directory you will also find djangos standard
`manage.py`.

In addition, there is also a helper script `makesuperuser.py` to
promote a normal user to a superuser.

### Configuration
Settings are read from environment variables. For your convenience the app
automatically loads `.env` files too. So for configuration create a `.env` file
in the project root. You can find a list of all possible variables in the
[available settings](#available-settings) section.

If you need even more control you can modify the `./gdshowreelvote/settings.py`
file directly.

### External Requirements
To run this project you need to provide a **mysql database** as well as a
**keycloak instance**.

#### Keycloak Setup:
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
- Provide the [configuration](#configuration) to the showreel app.

#### MySQL Database Setup:
- Setup a new mysql user and make a database for that user.
- Provide the [configuration](#configuration) to the showreel app.


## Available Settings

Here is the list of all settings and their default values. To use these as
environment variables, you need to prefix them with `GDSHOWREEL_` (it's
not included in the table below to keep everything easy to read).

| Name                              | Description                                                                                        | Default                                   |
|-----------------------------------|----------------------------------------------------------------------------------------------------|-------------------------------------------|
| DJANGO_SECRET_KEY                 | Django's  [SECRET_KEY](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-SECRET_KEY) |                                           |
| DJANGO_DEBUG                      | Whether or not to run django in debug mode                                                         |                                           |
| DJANGO_ALLOWED_HOSTS              | Allowed hosts (comma separated, should match the fqdn)                                             |                                           |
| DATABASE_HOST                     | Database host                                                                                      | database                                  |
| DATABASE_PORT                     | Database port                                                                                      |                                           |
| DATABASE_NAME                     | Database name                                                                                      | gdshowreel                                |
| DATABASE_USER                     | Name of database user                                                                              | mysql                                     |
| DATABASE_PASSWORD                 | Password for the database user                                                                     |                                           |
| VOTE_MAX_SUBMISSIONS_PER_SHOWREEL | How many submissions users can make to the same showreel                                           | 3                                         |
| VOTE_ONLY_STAFF_CAN_VOTE          | If yes, only users with the staff role can rate the showreel videos                                | yes                                       |
| SERVE_STATICS                     | Whether or not django should serve static files                                                    | yes                                       |
| DJANGO_STATIC_ROOT                | Location of the static files                                                                       | /var/www/showreel.godotengine.org/static/ |
| KEYCLOAK_HOSTNAME                 | Keycloak host                                                                                      | keycloak:8080                             |
| KEYCLOAK_REALM                    | Keycloak realm for the application                                                                 | master                                    |
| KEYCLOAK_ROLES_PATH_IN_CLAIMS     | Path to roles in keycloak claims                                                                   | realm_access,roles                        |
| KEYCLOAK_STAFF_ROLE               | Staff role in keycloak. Staff has access to the administration interface.                          | staff                                     |
| KEYCLOAK_SUPERUSER_ROLE           | Superusers role in keycloak. Same as staff plus a few more permissions.                            | admin                                     |
| OIDC_RP_CLIENT_ID                 | Keycloak OpenID Connect client ID                                                                  |                                           |
| OIDC_RP_CLIENT_SECRET             | Keycloak OpenID Connect client secret                                                              |                                           |

In addition to these, you can also override each OIDC API endpoint separately with
these environment variables:
- `GDSHOWREEL_OIDC_OP_AUTHORIZATION_ENDPOINT`
- `GDSHOWREEL_OIDC_OP_TOKEN_ENDPOINT`
- `GDSHOWREEL_OIDC_OP_USER_ENDPOINT`
- `GDSHOWREEL_OIDC_OP_JWKS_ENDPOINT`
- `GDSHOWREEL_OIDC_OP_LOGOUT_ENDPOINT`


## License

The code for this webapp is provided under the [MIT license](LICENSE.txt).
