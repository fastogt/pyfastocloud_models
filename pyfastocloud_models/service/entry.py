from bson import ObjectId
from pymodm import MongoModel, fields

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort
from pyfastocloud_models.provider.entry_pair import ProviderPair
from pyfastocloud_models.series.entry import Serial
from pyfastocloud_models.stream.entry import IStream


class ServiceSettings(MongoModel):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    HTTP_HOST_FIELD = 'http_host'
    VODS_HOST_FIELD = 'vods_host'
    CODS_HOST_FIELD = 'cods_host'
    FEEDBACK_DIRECOTRY_FIELD = 'feedback_directory'
    TIMESHIFTS_DIRECTORY_FIELD = 'timeshifts_directory'
    HLS_DIRECTORY_FIELD = 'hls_directory'
    VODS_IN_DIRECTORY_FIELD = 'vods_in_directory'
    VODS_DIRECTORY_FIELD = 'vods_directory'
    CODS_DIRECTORY_FIELD = 'cods_directory'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            ser = ServiceSettings.objects.get({'_id': sid})
        except ServiceSettings.DoesNotExist:
            return None
        else:
            return ser

    class Meta:
        collection_name = 'services'

    DEFAULT_SERVICE_NAME = 'Service'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_FEEDBACK_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/feedback'
    DEFAULT_TIMESHIFTS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/timeshifts'
    DEFAULT_HLS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/hls'
    DEFAULT_VODS_IN_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/vods_in'
    DEFAULT_VODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/vods'
    DEFAULT_CODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/cods'

    DEFAULT_SERVICE_HOST = 'localhost'
    DEFAULT_SERVICE_PORT = 6317
    DEFAULT_SERVICE_HTTP_HOST = 'localhost'
    DEFAULT_SERVICE_HTTP_PORT = 8000
    DEFAULT_SERVICE_VODS_HOST = 'localhost'
    DEFAULT_SERVICE_VODS_PORT = 7000
    DEFAULT_SERVICE_CODS_HOST = 'localhost'
    DEFAULT_SERVICE_CODS_PORT = 6001

    streams = fields.ListField(fields.ReferenceField(IStream), default=[], blank=True)
    series = fields.ListField(fields.ReferenceField(Serial, on_delete=fields.ReferenceField.PULL), default=[],
                              blank=True)
    providers = fields.EmbeddedModelListField(ProviderPair, default=[], blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedModelField(HostAndPort,
                                     default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    http_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_HTTP_HOST,
                                                                           port=DEFAULT_SERVICE_HTTP_PORT))
    vods_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_VODS_HOST,
                                                                           port=DEFAULT_SERVICE_VODS_PORT))
    cods_host = fields.EmbeddedModelField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CODS_HOST,
                                                                           port=DEFAULT_SERVICE_CODS_PORT))

    feedback_directory = fields.CharField(default=DEFAULT_FEEDBACK_DIR_PATH)
    timeshifts_directory = fields.CharField(default=DEFAULT_TIMESHIFTS_DIR_PATH)
    hls_directory = fields.CharField(default=DEFAULT_HLS_DIR_PATH)
    vods_in_directory = fields.CharField(default=DEFAULT_VODS_IN_DIR_PATH)
    vods_directory = fields.CharField(default=DEFAULT_VODS_DIR_PATH)
    cods_directory = fields.CharField(default=DEFAULT_CODS_DIR_PATH)

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def get_host(self) -> str:
        return str(self.host)

    def get_http_host(self) -> str:
        return 'http://{0}'.format(str(self.http_host))

    def get_vods_host(self) -> str:
        return 'http://{0}'.format(str(self.vods_host))

    def get_cods_host(self) -> str:
        return 'http://{0}'.format(str(self.cods_host))

    def generate_http_link(self, url: str) -> str:
        return url.replace(self.hls_directory, self.get_http_host())

    def generate_vods_link(self, url: str) -> str:
        return url.replace(self.vods_directory, self.get_vods_host())

    def generate_cods_link(self, url: str) -> str:
        return url.replace(self.cods_directory, self.get_cods_host())

    def generate_playlist(self) -> str:
        result = '#EXTM3U\n'
        for stream in self.streams:
            result += stream.generate_playlist(False)

        return result

    def add_streams(self, streams: [IStream]):
        for stream in streams:
            if stream:
                self.add_stream(stream)

    def add_stream(self, stream: IStream):
        if stream:
            self.streams.append(stream)

    def remove_stream(self, stream: IStream):
        if stream:
            self.streams.remove(stream)
            stream.delete()

    def remove_all_streams(self):
        for stream in list(self.streams):
            stream.delete()
        self.streams = []

    def add_provider(self, user: ProviderPair):
        if user:
            self.providers.append(user)

    def remove_provider(self, provider):
        for prov in list(self.providers):
            if prov.user == provider:
                self.providers.remove(prov)

    def find_stream_by_id(self, sid: ObjectId):
        for stream in self.streams:
            if stream.id == sid:
                return stream

        return None

    def delete(self, *args, **kwargs):
        for stream in self.streams:
            if stream:
                stream.delete()
        return super(ServiceSettings, self).delete(*args, **kwargs)

    @classmethod
    def make_entry(cls, json: dict) -> 'ServiceSettings':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        if not json:
            raise ValueError('Invalid input')

        name_field = json.get(ServiceSettings.NAME_FIELD, None)
        if not name_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.NAME_FIELD))
        self.name = name_field

        host_field = json.get(ServiceSettings.HOST_FIELD, None)
        if not host_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.HOST_FIELD))
        self.host = HostAndPort.make_entry(host_field)

        http_host_field = json.get(ServiceSettings.HTTP_HOST_FIELD, None)
        if not http_host_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.HTTP_HOST_FIELD))
        self.http_host = HostAndPort.make_entry(http_host_field)

        vods_host_field = json.get(ServiceSettings.VODS_HOST_FIELD, None)
        if not vods_host_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.VODS_HOST_FIELD))
        self.vods_host = HostAndPort.make_entry(vods_host_field)

        cods_host_field = json.get(ServiceSettings.CODS_HOST_FIELD, None)
        if not cods_host_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.CODS_HOST_FIELD))
        self.cods_host = HostAndPort.make_entry(cods_host_field)

        feedback_field = json.get(ServiceSettings.FEEDBACK_DIRECOTRY_FIELD, None)
        if not feedback_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.FEEDBACK_DIRECOTRY_FIELD))
        self.feedback_directory = feedback_field

        timeshift_field = json.get(ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD, None)
        if not timeshift_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD))
        self.timeshifts_directory = timeshift_field

        hls_field = json.get(ServiceSettings.HLS_DIRECTORY_FIELD, None)
        if not hls_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.HLS_DIRECTORY_FIELD))
        self.hls_directory = hls_field

        vods_in_field = json.get(ServiceSettings.VODS_IN_DIRECTORY_FIELD, None)
        if not vods_in_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.VODS_IN_DIRECTORY_FIELD))
        self.vods_in_directory = vods_in_field

        vods_field = json.get(ServiceSettings.VODS_DIRECTORY_FIELD, None)
        if not vods_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.VODS_DIRECTORY_FIELD))
        self.vods_directory = vods_field

        cods_field = json.get(ServiceSettings.CODS_DIRECTORY_FIELD, None)
        if not cods_field:
            raise ValueError('Invalid input({0} required)'.format(ServiceSettings.CODS_DIRECTORY_FIELD))
        self.cods_directory = cods_field

    def to_front_dict(self) -> dict:
        return {ServiceSettings.ID_FIELD: self.get_id(), ServiceSettings.NAME_FIELD: self.name,
                ServiceSettings.HOST_FIELD: self.host.to_front_dict(),
                ServiceSettings.HTTP_HOST_FIELD: self.http_host.to_front_dict(),
                ServiceSettings.VODS_HOST_FIELD: self.vods_host.to_front_dict(),
                ServiceSettings.CODS_HOST_FIELD: self.cods_host.to_front_dict(),
                ServiceSettings.FEEDBACK_DIRECOTRY_FIELD: self.feedback_directory,
                ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD: self.timeshifts_directory,
                ServiceSettings.HLS_DIRECTORY_FIELD: self.hls_directory,
                ServiceSettings.VODS_IN_DIRECTORY_FIELD: self.vods_in_directory,
                ServiceSettings.VODS_DIRECTORY_FIELD: self.vods_directory,
                ServiceSettings.CODS_DIRECTORY_FIELD: self.cods_directory}
