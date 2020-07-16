from datetime import datetime
from enum import IntEnum

from bson.objectid import ObjectId
from pyfastogt.utils import is_valid_email
from pymodm import MongoModel, fields
from pymongo.operations import IndexModel
from werkzeug.security import generate_password_hash, check_password_hash

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Maker
from pyfastocloud_models.epg.entry import EpgSettings
from pyfastocloud_models.load_balance.entry import LoadBalanceSettings
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.subscriber.entry import Subscriber
from pyfastocloud_models.utils.utils import date_to_utc_msec


class Provider(MongoModel, Maker):
    ID_FIELD = 'id'
    EMAIL_FIELD = 'email'
    FIRST_NAME_FIELD = 'first_name'
    LAST_NAME_FIELD = 'last_name'
    CREATED_DATE_FIELD = 'created_date'
    STATUS_FIELD = 'status'
    TYPE_FIELD = 'type'
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
        ADMIN = 0,
        RESELLER = 1

    class Meta:
        collection_name = 'providers'
        allow_inheritance = True
        indexes = [IndexModel([('email', 1)], unique=True)]

    email = fields.EmailField(required=True)
    first_name = fields.CharField(min_length=2, max_length=64, required=True)
    last_name = fields.CharField(min_length=2, max_length=64, required=True)
    password = fields.CharField(required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)  #
    type = fields.IntegerField(default=Type.RESELLER, required=True)  #
    status = fields.IntegerField(default=Status.NO_ACTIVE, required=True)  #
    country = fields.CharField(min_length=2, max_length=3, required=True)
    language = fields.CharField(default=constants.DEFAULT_LOCALE, required=True)

    servers = fields.ListField(fields.ReferenceField(ServiceSettings, on_delete=fields.ReferenceField.PULL), blank=True)
    subscribers = fields.ListField(fields.ReferenceField(Subscriber, on_delete=fields.ReferenceField.PULL), blank=True)
    load_balancers = fields.ListField(fields.ReferenceField(LoadBalanceSettings, on_delete=fields.ReferenceField.PULL),
                                      blank=True)
    epgs = fields.ListField(fields.ReferenceField(EpgSettings, on_delete=fields.ReferenceField.PULL), blank=True)

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def is_admin(self) -> bool:
        return self.type == Provider.Type.ADMIN

    def add_subscriber(self, subscriber: Subscriber):
        if not subscriber:
            return

        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def remove_subscriber(self, subscriber: Subscriber):
        if not subscriber:
            return

        try:
            self.subscribers.remove(subscriber)
        except ValueError:
            pass

    def add_server(self, server: ServiceSettings):
        if not server:
            return

        if server not in self.servers:
            self.servers.append(server)

    def remove_server(self, server: ServiceSettings):
        if not server:
            return

        try:
            self.servers.remove(server)
        except ValueError:
            pass

    def add_load_balancer(self, server: LoadBalanceSettings):
        if not server:
            return

        if server not in self.load_balancers:
            self.load_balancers.append(server)

    def remove_load_balancer(self, server: LoadBalanceSettings):
        if not server:
            return

        try:
            self.load_balancers.remove(server)
        except ValueError:
            pass

    def add_epg(self, server: EpgSettings):
        if not server:
            return

        if server not in self.epgs:
            self.epgs.append(server)

    def remove_epg(self, server: EpgSettings):
        if not server:
            return

        try:
            self.epgs.remove(server)
        except ValueError:
            pass

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
        Maker.update_entry(self, json)

        res, email_field = self.check_required_type(Provider.EMAIL_FIELD, str, json)
        if res:
            email = email_field.lower()
            if not is_valid_email(email):
                raise ValueError('Invalid email')
            self.email = email

        res, password = self.check_required_type(Provider.PASSWORD_FIELD, str, json)
        if res:
            self.password = Provider.generate_password_hash(password)

        res, first_name = Provider.check_required_type(Provider.FIRST_NAME_FIELD, str, json)
        if res:
            self.first_name = first_name

        res, last_name = Provider.check_required_type(Provider.LAST_NAME_FIELD, str, json)
        if res:
            self.last_name = last_name

        res, created_date_msec = self.check_optional_type(Provider.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, ptype = self.check_optional_type(Provider.TYPE_FIELD, int, json)
        if res:
            self.type = ptype

        res, status = self.check_optional_type(Provider.STATUS_FIELD, int, json)
        if res:
            self.status = status

        res, country = self.check_required_type(Provider.COUNTRY_FIELD, str, json)
        if res:
            if not constants.is_valid_country_code(country):
                ValueError('Invalid country')
            self.country = country

        res, language = self.check_required_type(Provider.LANGUAGE_FIELD, str, json)
        if res:
            if not constants.is_valid_locale_code(language):
                raise ValueError('Invalid language')
            self.language = language

    def to_front_dict(self):
        return {Provider.ID_FIELD: self.get_id(), Provider.EMAIL_FIELD: self.email,
                Provider.PASSWORD_FIELD: self.password,
                Provider.FIRST_NAME_FIELD: self.first_name, Provider.LAST_NAME_FIELD: self.last_name,
                Provider.CREATED_DATE_FIELD: date_to_utc_msec(self.created_date), Provider.STATUS_FIELD: self.status,
                Provider.TYPE_FIELD: self.type, Provider.LANGUAGE_FIELD: self.language,
                Provider.COUNTRY_FIELD: self.country}

    def delete(self, *args, **kwargs):
        from pyfastocloud_models.service.entry import ServiceSettings
        servers = ServiceSettings.objects.all()
        for server in servers:
            server.remove_provider(self.id)
            server.save()

        from pyfastocloud_models.load_balance.entry import LoadBalanceSettings
        loads = LoadBalanceSettings.objects.all()
        for load in loads:
            load.remove_provider(self.id)
            load.save()

        from pyfastocloud_models.epg.entry import EpgSettings
        epgs = EpgSettings.objects.all()
        for epg in epgs:
            epg.remove_provider(self.id)
            epg.save()
        return super(Provider, self).delete(*args, **kwargs)
