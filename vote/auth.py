from mozilla_django_oidc.auth import OIDCAuthenticationBackend as BaseOIDCAuthenticationBackend

from django.conf import settings
from django.contrib import messages

from vote.models import User

class OIDCAuthenticationBackend(BaseOIDCAuthenticationBackend):
    def update_user(self, user, claims):
        user.email = claims.get('email', '')
        user.username = claims.get('preferred_username', '')

        # Get the roles array.
        roles = claims
        for key in settings.KEYCLOAK_ROLES_PATH_IN_CLAIMS:
            roles = roles.get(key, None)
            if roles is None:
                messages.add_message(self.request, messages.WARNING, "Could not find the user\'s assigned roles from the authentication backend. Using default permissions instead.")
                break

        user.is_staff = False
        if isinstance(roles, list) and settings.KEYCLOAK_STAFF_ROLE in roles:
            user.is_staff = True
        if isinstance(roles, list) and settings.KEYCLOAK_SUPERUSER_ROLE in roles:
            user.is_staff = True
            user.is_superuser = True

        user.save()

        return user

    def create_user(self, claims):
        email = claims.get('email')
        user = self.UserModel.objects.create_user(email=email)
        return self.update_user(user, claims)

    def verify_claims(self, claims):
        if not super(OIDCAuthenticationBackend, self).verify_claims(claims):
            messages.add_message(self.request, messages.ERROR, "Could not login.")
            return False

        if not claims.get('email_verified', False):
            messages.add_message(self.request, messages.ERROR, "Unauthorized login. Please validate your email address.")
            return False
        return True

def logout(request):
    redirect_uri = request.build_absolute_uri("/")
    return f"{settings.OIDC_OP_LOGOUT_ENDPOINT}?redirect_uri={redirect_uri}"