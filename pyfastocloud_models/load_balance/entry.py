from bson import ObjectId
from pymodm import MongoModel, fields

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort, Maker
from pyfastocloud_models.provider.entry_pair import ProviderPair


class LoadBalanceSettings(MongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    CLIENTS_HOST = 'clients_host'
    CATCHUPS_HOST_FIELD = 'catchups_host'
    CATCHUPS_HTTP_ROOT_FIELD = 'catchups_http_root'
    PROVIDERS_FIELD = 'providers'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            ser = LoadBalanceSettings.objects.get({'_id': sid})
        except LoadBalanceSettings.DoesNotExist:
            return None
        else:
            return ser

    class Meta:
        collection_name = 'load_balance'

    DEFAULT_SERVICE_NAME = 'Load Balance'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_SERVICE_HOST = 'localhost'
    DEFAULT_SERVICE_PORT = 5317
    DEFAULT_SERVICE_CLIENTS_HOST = '0.0.0.0'
    DEFAULT_SERVICE_CLIENTS_PORT = 6000

    DEFAULT_CATCHUPS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/hls'
    DEFAULT_CATCHUPS_HTTP_HOST = '0.0.0.0'
    DEFAULT_CATCHUPS_HTTP_PORT = 8000

    providers = fields.EmbeddedModelListField(ProviderPair, default=[], blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedModelField(HostAndPort,
                                     default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    clients_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CLIENTS_HOST,
                                                                              port=DEFAULT_SERVICE_CLIENTS_PORT))
    catchups_http_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_CATCHUPS_HTTP_HOST,
                                                                                    port=DEFAULT_CATCHUPS_HTTP_PORT))
    catchups_hls_directory = fields.CharField(default=DEFAULT_CATCHUPS_DIR_PATH)

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def add_provider(self, user: ProviderPair):
        if user:
            self.providers.append(user)

    def remove_provider(self, provider):
        for prov in list(self.providers):
            if prov.user == provider:
                self.providers.remove(prov)

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        name_field = json.get(LoadBalanceSettings.NAME_FIELD, None)
        if not name_field:
            raise ValueError('Invalid input({0} required)'.format(LoadBalanceSettings.NAME_FIELD))
        self.name = name_field

        host_field = json.get(LoadBalanceSettings.HOST_FIELD, None)
        if not host_field:
            raise ValueError('Invalid input({0} required)'.format(LoadBalanceSettings.HOST_FIELD))
        self.host = HostAndPort.make_entry(host_field)

        clients_host_field = json.get(LoadBalanceSettings.CLIENTS_HOST, None)
        if not clients_host_field:
            raise ValueError('Invalid input({0} required)'.format(LoadBalanceSettings.CLIENTS_HOST))
        self.clients_host = HostAndPort.make_entry(clients_host_field)

        catchups_host_field = json.get(LoadBalanceSettings.CATCHUPS_HOST_FIELD, None)
        if not catchups_host_field:
            raise ValueError('Invalid input({0} required)'.format(LoadBalanceSettings.CATCHUPS_HOST_FIELD))
        self.catchups_http_host = HostAndPort.make_entry(catchups_host_field)

        catchups_http_root_field = json.get(LoadBalanceSettings.CATCHUPS_HTTP_ROOT_FIELD, None)
        if not catchups_http_root_field:
            raise ValueError('Invalid input({0} required)'.format(LoadBalanceSettings.CATCHUPS_HTTP_ROOT_FIELD))
        self.catchups_hls_directory = catchups_http_root_field

    def to_front_dict(self) -> dict:
        providers = []
        for prov in self.providers:
            providers.append(prov.to_front_dict())
        return {LoadBalanceSettings.ID_FIELD: self.get_id(), LoadBalanceSettings.NAME_FIELD: self.name,
                LoadBalanceSettings.HOST_FIELD: self.host.to_front_dict(),
                LoadBalanceSettings.CLIENTS_HOST: self.clients_host.to_front_dict(),
                LoadBalanceSettings.CATCHUPS_HOST_FIELD: self.catchups_http_host.to_front_dict(),
                LoadBalanceSettings.CATCHUPS_HTTP_ROOT_FIELD: self.catchups_hls_directory,
                LoadBalanceSettings.PROVIDERS_FIELD: providers}
