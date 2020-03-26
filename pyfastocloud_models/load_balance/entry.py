from bson import ObjectId
from pymodm import MongoModel, fields

from pyfastocloud_models.common_entries import HostAndPort
from pyfastocloud_models.provider.entry_pair import ProviderPair


class LoadBalanceSettings(MongoModel):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    CLIENTS_HOST = 'clients_host'

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
    DEFAULT_SERVICE_CLIENTS_HOST = 'localhost'
    DEFAULT_SERVICE_CLIENTS_PORT = 6000

    providers = fields.EmbeddedDocumentListField(ProviderPair, default=[], blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedDocumentField(HostAndPort,
                                        default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    clients_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CLIENTS_HOST,
                                                                                 port=DEFAULT_SERVICE_CLIENTS_PORT))

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

    def to_front_dict(self) -> dict:
        return {LoadBalanceSettings.ID_FIELD: self.get_id(), LoadBalanceSettings.NAME_FIELD: self.name,
                LoadBalanceSettings.HOST_FIELD: str(self.host),
                LoadBalanceSettings.CLIENTS_HOST: str(self.clients_host)}
