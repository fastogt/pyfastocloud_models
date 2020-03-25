from datetime import datetime
from enum import IntEnum

from bson.objectid import ObjectId
from pymodm import MongoModel, fields
from pymongo.operations import IndexModel
from werkzeug.security import generate_password_hash, check_password_hash

import pyfastocloud_models.constants as constants
from pyfastocloud_models.load_balance.entry import LoadBalanceSettings
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.utils.utils import date_to_utc_msec


class Provider(MongoModel):
    ID_FIELD = 'id'
    EMAIL_FIELD = 'email'
    FIRST_NAME_FIELD = 'first_name'
    LAST_NAME_FIELD = 'last_name'
    CREATED_DATE_FIELD = 'created_date'
    STATUS_FIELD = 'status'
    LANGUAGE_FIELD = 'language'
    COUNTRY_FIELD = 'country'

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

    def to_front_dict(self):
        return {Provider.ID_FIELD: self.get_id(), Provider.EMAIL_FIELD: self.email,
                Provider.FIRST_NAME_FIELD: self.first_name, Provider.LAST_NAME_FIELD: self.last_name,
                Provider.CREATED_DATE_FIELD: date_to_utc_msec(self.created_date), Provider.STATUS_FIELD: self.status,
                Provider.LANGUAGE_FIELD: self.language, Provider.COUNTRY_FIELD: self.country}
