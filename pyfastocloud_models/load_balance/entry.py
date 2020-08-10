from datetime import datetime

from bson import ObjectId
from pymodm import MongoModel, fields, errors

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort, Maker
from pyfastocloud_models.machine_entry import Machine
from pyfastocloud_models.provider.entry_pair import ProviderPair
from pyfastocloud_models.utils.utils import date_to_utc_msec


class LoadBalanceSettings(MongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    CLIENTS_HOST = 'clients_host'
    CATCHUPS_HOST_FIELD = 'catchups_host'
    CATCHUPS_HTTP_ROOT_FIELD = 'catchups_http_root'
    PROVIDERS_FIELD = 'providers'
    CREATED_DATE_FIELD = 'created_date'
    MONITORING_FILED = 'monitoring'
    AUTO_START_FIELD = 'auto_start'
    ACTIVATION_KEY_FIELD = 'activation_key'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            ser = LoadBalanceSettings.objects.get({'_id': sid})
        except LoadBalanceSettings.DoesNotExist:
            return None
        else:
            return ser

    class Meta:
        allow_inheritance = False
        collection_name = 'load_balance'

    DEFAULT_SERVICE_NAME = 'Load Balance'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_SERVICE_HOST = '127.0.0.1'
    DEFAULT_SERVICE_PORT = 5317
    DEFAULT_SERVICE_CLIENTS_HOST = '0.0.0.0'
    DEFAULT_SERVICE_CLIENTS_PORT = 6000

    DEFAULT_CATCHUPS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/hls'
    DEFAULT_CATCHUPS_HTTP_HOST = '0.0.0.0'
    DEFAULT_CATCHUPS_HTTP_PORT = 8000

    providers = fields.EmbeddedModelListField(ProviderPair, blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedModelField(HostAndPort,
                                     default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    clients_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CLIENTS_HOST,
                                                                              port=DEFAULT_SERVICE_CLIENTS_PORT))
    catchups_http_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_CATCHUPS_HTTP_HOST,
                                                                                    port=DEFAULT_CATCHUPS_HTTP_PORT))
    catchups_hls_directory = fields.CharField(default=DEFAULT_CATCHUPS_DIR_PATH)
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

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, name = self.check_required_type(LoadBalanceSettings.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, host = self.check_required_type(LoadBalanceSettings.HOST_FIELD, dict, json)
        if res:  # required field
            self.host = HostAndPort.make_entry(host)

        res, clhost = self.check_required_type(LoadBalanceSettings.CLIENTS_HOST, dict, json)
        if res:  # required field
            self.clients_host = HostAndPort.make_entry(clhost)

        res, cat = self.check_required_type(LoadBalanceSettings.CATCHUPS_HOST_FIELD, dict, json)
        if res:  # required field
            self.catchups_http_host = HostAndPort.make_entry(cat)

        res, http = self.check_required_type(LoadBalanceSettings.CATCHUPS_HTTP_ROOT_FIELD, str, json)
        if res:  # required field
            self.catchups_hls_directory = http

        res, created_date_msec = self.check_optional_type(LoadBalanceSettings.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, monitoring = self.check_required_type(LoadBalanceSettings.MONITORING_FILED, bool, json)
        if res:  # required field
            self.monitoring = monitoring

        res, auto_start = self.check_required_type(LoadBalanceSettings.AUTO_START_FIELD, bool, json)
        if res:  # required field
            self.auto_start = auto_start

        res, activation_key = self.check_optional_type(LoadBalanceSettings.ACTIVATION_KEY_FIELD, str, json)
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
        return {LoadBalanceSettings.ID_FIELD: self.get_id(), LoadBalanceSettings.NAME_FIELD: self.name,
                LoadBalanceSettings.HOST_FIELD: self.host.to_front_dict(),
                LoadBalanceSettings.CLIENTS_HOST: self.clients_host.to_front_dict(),
                LoadBalanceSettings.CATCHUPS_HOST_FIELD: self.catchups_http_host.to_front_dict(),
                LoadBalanceSettings.CATCHUPS_HTTP_ROOT_FIELD: self.catchups_hls_directory,
                LoadBalanceSettings.CREATED_DATE_FIELD: self.created_date_utc_msec(),
                LoadBalanceSettings.AUTO_START_FIELD: self.auto_start,
                LoadBalanceSettings.ACTIVATION_KEY_FIELD: self.activation_key,
                LoadBalanceSettings.PROVIDERS_FIELD: providers, LoadBalanceSettings.MONITORING_FILED: self.monitoring}
