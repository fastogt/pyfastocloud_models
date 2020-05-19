from bson import ObjectId
from pymodm import MongoModel, EmbeddedMongoModel, fields

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort, Maker
from pyfastocloud_models.provider.entry_pair import ProviderPair


class EpgUrl(EmbeddedMongoModel, Maker):
    ID_FIELD = 'id'
    ROLE_FIELD = 'role'

    uri = fields.CharField(default='http://0.0.0.0/epg.xml', max_length=constants.MAX_URI_LENGTH, required=True)
    extension = fields.CharField(max_length=5, required=False)

    def to_front_dict(self) -> dict:
        return {ProviderPair.ID_FIELD: str(self.user.id), ProviderPair.ROLE_FIELD: self.role}


class EpgSettings(MongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    URLS_FIELD = 'urls'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            ser = EpgSettings.objects.get({'_id': sid})
        except EpgSettings.DoesNotExist:
            return None
        else:
            return ser

    class Meta:
        collection_name = 'epg'

    DEFAULT_SERVICE_NAME = 'Epg'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_SERVICE_HOST = 'localhost'
    DEFAULT_SERVICE_PORT = 4317

    providers = fields.EmbeddedModelListField(ProviderPair, default=[], blank=True)
    urls = fields.EmbeddedModelListField(EpgUrl, default=[], blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedModelField(HostAndPort,
                                     default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))

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

        name_field = json.get(EpgSettings.NAME_FIELD, None)
        if not name_field:
            raise ValueError('Invalid input({0} required)'.format(EpgSettings.NAME_FIELD))
        self.name = name_field

        host_field = json.get(EpgSettings.HOST_FIELD, None)
        if not host_field:
            raise ValueError('Invalid input({0} required)'.format(EpgSettings.HOST_FIELD))
        self.host = HostAndPort.make_entry(host_field)

    def to_front_dict(self) -> dict:
        providers = []
        for prov in self.providers:
            providers.append(prov.to_front_dict())
        return {EpgSettings.ID_FIELD: self.get_id(), EpgSettings.NAME_FIELD: self.name,
                EpgSettings.HOST_FIELD: self.host.to_front_dict(), EpgSettings.PROVIDERS_FIELD: providers}
