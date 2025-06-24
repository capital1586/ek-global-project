from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """Custom authentication backend to authenticate users by email"""

    def authenticate(self, request, **credentials):
        email = credentials.get("email", None) or credentials.get("username", None)
        password = credentials.get("password", None)
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
        return None
