from datetime import datetime

from bson import ObjectId
from pymodm import MongoModel, EmbeddedMongoModel, fields, errors
from pymodm.errors import ValidationError

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort, Maker
from pyfastocloud_models.machine_entry import Machine
from pyfastocloud_models.provider.entry_pair import ProviderPair
from pyfastocloud_models.utils.utils import date_to_utc_msec


class EpgUrl(EmbeddedMongoModel, Maker):
    ID_FIELD = 'id'
    URL_FIELD = 'url'

    id = fields.ObjectIdField(required=True, default=ObjectId, primary_key=True)
    url = fields.CharField(default='http://0.0.0.0/epg.xml', max_length=constants.MAX_URI_LENGTH, required=True)

    def get_id(self) -> str:
        return str(self.id)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, url = self.check_required_type(EpgUrl.URL_FIELD, str, json)
        if res:
            self.url = url

    def to_front_dict(self) -> dict:
        return {EpgUrl.ID_FIELD: self.get_id(), EpgUrl.URL_FIELD: self.url}


class EpgSettings(MongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    URLS_FIELD = 'urls'
    PROVIDERS_FIELD = 'providers'
    CREATED_DATE_FIELD = 'created_date'
    MONITORING_FILED = 'monitoring'
    AUTO_START_FIELD = 'auto_start'
    ACTIVATION_KEY_FIELD = 'activation_key'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            ser = EpgSettings.objects.get({'_id': sid})
        except EpgSettings.DoesNotExist:
            return None
        else:
            return ser

    class Meta:
        allow_inheritance = False
        collection_name = 'epg'

    DEFAULT_SERVICE_NAME = 'Epg'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_SERVICE_HOST = '127.0.0.1'
    DEFAULT_SERVICE_PORT = 4317

    providers = fields.EmbeddedModelListField(ProviderPair, blank=True)
    urls = fields.EmbeddedModelListField(EpgUrl, blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedModelField(HostAndPort,
                                     default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    # stats
    auto_start = fields.BooleanField(default=False, required=True)
    activation_key = fields.CharField(max_length=constants.ACTIVATION_KEY_LENGTH,
                                      min_length=constants.ACTIVATION_KEY_LENGTH, required=False)
    monitoring = fields.BooleanField(default=False, required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)  #
    stats = fields.EmbeddedModelListField(Machine, blank=True)

    def get_id(self) -> str:
        return str(self.pk)

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    @property
    def id(self):
        return self.pk

    def add_stat(self, stat: Machine):
        if not stat:
            return

        self.stats.append(stat)

    def remove_stat(self, stat: Machine):
        if not stat:
            return

        self.stats.remove(stat)

    def add_provider(self, user: ProviderPair) -> ProviderPair:
        if not user:
            return None

        if user not in self.providers:
            self.providers.append(user)
            return user

        return None

    def remove_provider(self, provider: ObjectId) -> ProviderPair:
        for prov in self.providers:
            if prov.user == provider:
                self.providers.remove(prov)
                return prov

        return None

    def add_url(self, url: EpgUrl) -> EpgUrl:
        if not url:
            return None

        if url not in self.urls:
            self.urls.append(url)
            return url

        return None

    def remove_url(self, uid: ObjectId) -> EpgUrl:
        for url in self.urls:
            if url.id == uid:
                self.urls.remove(url)
                return url

        return None

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, name = self.check_required_type(EpgSettings.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, host = self.check_required_type(EpgSettings.HOST_FIELD, dict, json)
        if res:  # required field
            self.host = HostAndPort.make_entry(host)

        res, created_date_msec = self.check_optional_type(EpgSettings.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, monitoring = self.check_required_type(EpgSettings.MONITORING_FILED, bool, json)
        if res:  # required field
            self.monitoring = monitoring

        res, auto_start = self.check_required_type(EpgSettings.AUTO_START_FIELD, bool, json)
        if res:  # required field
            self.auto_start = auto_start

        res, activation_key = self.check_optional_type(EpgSettings.ACTIVATION_KEY_FIELD, str, json)
        if res:  # optional field
            self.activation_key = activation_key

        try:
            self.full_clean()
        except errors.ValidationError as err:
            raise ValueError(err.message)

    def to_front_dict(self) -> dict:
        providers = []
        for prov in self.providers:
            providers.append(prov.to_front_dict())
        urls = []
        for url in self.urls:
            urls.append(url.to_front_dict())
        return {EpgSettings.ID_FIELD: self.get_id(), EpgSettings.NAME_FIELD: self.name,
                EpgSettings.HOST_FIELD: self.host.to_front_dict(), EpgSettings.URLS_FIELD: urls,
                EpgSettings.CREATED_DATE_FIELD: self.created_date_utc_msec(),
                EpgSettings.AUTO_START_FIELD: self.auto_start,
                EpgSettings.ACTIVATION_KEY_FIELD: self.activation_key,
                EpgSettings.PROVIDERS_FIELD: providers, EpgSettings.MONITORING_FILED: self.monitoring}
