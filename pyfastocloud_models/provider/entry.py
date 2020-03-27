from datetime import datetime
from enum import IntEnum

from bson.objectid import ObjectId
from pymodm import MongoModel, fields
from pymongo.operations import IndexModel
from werkzeug.security import generate_password_hash, check_password_hash

import pyfastocloud_models.constants as constants
from pyfastocloud_models.load_balance.entry import LoadBalanceSettings
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.utils.utils import date_to_utc_msec, is_valid_email


class Provider(MongoModel):
    ID_FIELD = 'id'
    EMAIL_FIELD = 'email'
    FIRST_NAME_FIELD = 'first_name'
    LAST_NAME_FIELD = 'last_name'
    CREATED_DATE_FIELD = 'created_date'
    STATUS_FIELD = 'status'
    LANGUAGE_FIELD = 'language'
    COUNTRY_FIELD = 'country'
    PASSWORD_FIELD = 'password'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            provider = Provider.objects.get({'_id': sid})
        except Provider.DoesNotExist:
            return None
        else:
            return provider

    @staticmethod
    def get_by_email(email: str):
        try:
            provider = Provider.objects.get({'email': email})
        except Provider.DoesNotExist:
            return None
        else:
            return provider

    class Status(IntEnum):
        NO_ACTIVE = 0
        ACTIVE = 1
        BANNED = 2

    class Type(IntEnum):
        GUEST = 0,
        USER = 1

    class Meta:
        collection_name = 'providers'
        allow_inheritance = True
        indexes = [IndexModel([('email', 1)], unique=True)]

    email = fields.EmailField(required=True)
    first_name = fields.CharField(min_length=2, max_length=64, required=True)
    last_name = fields.CharField(min_length=2, max_length=64, required=True)
    password = fields.CharField(required=True)
    created_date = fields.DateTimeField(default=datetime.now)
    status = fields.IntegerField(default=Status.NO_ACTIVE)
    country = fields.CharField(min_length=2, max_length=3, required=True)
    language = fields.CharField(default=constants.DEFAULT_LOCALE, required=True)

    servers = fields.ListField(fields.ReferenceField(ServiceSettings, on_delete=fields.ReferenceField.PULL), default=[])
    load_balancers = fields.ListField(fields.ReferenceField(LoadBalanceSettings, on_delete=fields.ReferenceField.PULL),
                                      default=[])

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def add_server(self, server):
        if server:
            self.servers.append(server)

    def remove_server(self, server):
        if server:
            self.servers.remove(server)

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return generate_password_hash(password, method='sha256')

    @staticmethod
    def check_password_hash(hash_str: str, password: str) -> bool:
        return check_password_hash(hash_str, password)

    @classmethod
    def make_provider(cls, email: str, first_name: str, last_name: str, password: str, country: str, language: str):
        return cls(email=email, first_name=first_name, last_name=last_name,
                   password=Provider.generate_password_hash(password), country=country, language=language)

    @classmethod
    def make_entry(cls, json: dict) -> 'Provider':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        if not json:
            raise ValueError('Invalid input')

        email_field = json.get(Provider.EMAIL_FIELD, None)
        if not email_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.EMAIL_FIELD))
        email = email_field.lower()
        if not is_valid_email(email, False):
            return ValueError('Invalid email')
        self.email = email

        password_field = json.get(Provider.PASSWORD_FIELD, None)
        if not password_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.PASSWORD_FIELD))
        self.password = Provider.generate_password_hash(password_field)

        first_name_field = json.get(Provider.FIRST_NAME_FIELD, None)
        if not first_name_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.FIRST_NAME_FIELD))
        self.first_name = first_name_field

        last_name_field = json.get(Provider.LAST_NAME_FIELD, None)
        if not last_name_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.LAST_NAME_FIELD))
        self.last_name = last_name_field

        created_date_field = json.get(Provider.CREATED_DATE_FIELD, None)
        if not created_date_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.CREATED_DATE_FIELD))
        self.created_date = datetime.utcfromtimestamp(created_date_field)

        status_field = json.get(Provider.STATUS_FIELD, None)
        if not status_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.STATUS_FIELD))
        self.status = status_field

        country_field = json.get(Provider.COUNTRY_FIELD, None)
        if not country_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.COUNTRY_FIELD))
        if not isinstance(country_field, str) or not constants.is_valid_country_code(country_field):
            ValueError('Invalid country')
        self.country = country_field

        language_field = json.get(Provider.LANGUAGE_FIELD, None)
        if not language_field:
            raise ValueError('Invalid input({0} required)'.format(Provider.LANGUAGE_FIELD))
        if not isinstance(language_field, str) or not constants.is_valid_locale_code(language_field):
            raise ValueError('Invalid language')
        self.language = language_field

    def to_front_dict(self):
        return {Provider.ID_FIELD: self.get_id(), Provider.EMAIL_FIELD: self.email,
                Provider.FIRST_NAME_FIELD: self.first_name, Provider.LAST_NAME_FIELD: self.last_name,
                Provider.CREATED_DATE_FIELD: date_to_utc_msec(self.created_date), Provider.STATUS_FIELD: self.status,
                Provider.LANGUAGE_FIELD: self.language, Provider.COUNTRY_FIELD: self.country}
