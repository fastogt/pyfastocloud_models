from flask_login import UserMixin, login_user, logout_user

from pyfastocloud_models.provider.entry import Provider


class ProviderUser(UserMixin, Provider):
    def login(self):
        login_user(self)

    def logout(self):
        logout_user()
