from flask_login import UserMixin, login_user, logout_user

from pyfastocloud_models.subscriber.entry import Subscriber


class SubscriberUser(UserMixin, Subscriber):
    def login(self):
        login_user(self)

    def logout(self):
        logout_user()
