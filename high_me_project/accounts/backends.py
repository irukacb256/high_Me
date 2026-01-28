from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        try:
            # Case-insensitive email search
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # If multiple users have the same email, create a security risk or just fail.
            # Best to return the first one or fail. Failing is safer.
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
