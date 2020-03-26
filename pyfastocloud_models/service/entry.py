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
    HTTP_HOST = 'http_host'
    VODS_HOST = 'vods_host'
    CODS_HOST = 'cods_host'
    FEEDBACK_DIRECOTRY = 'feedback_directory'
    TIMESHIFTS_DIRECTORY = 'timeshifts_directory'
    HLS_DIRECTORY = 'hls_directory'
    PLAYLIST_DIRECTORY = 'playlists_directory'
    DVB_DIRECTORY = 'dvb_directory'
    CAPTURE_CARD_DIRECTORY = 'capture_card_directory'
    VODS_IN_DIRECTORY = 'vods_in_directory'
    VODS_DIRECTORY = 'vods_directory'
    CODS_DIRECTORY = 'cods_directory'

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
    DEFAULT_PLAYLISTS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/playlists'
    DEFAULT_DVB_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/dvb'
    DEFAULT_CAPTURE_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/capture_card'
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
    providers = fields.EmbeddedDocumentListField(ProviderPair, default=[], blank=True)

    name = fields.CharField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                            min_length=MIN_SERVICE_NAME_LENGTH)
    host = fields.EmbeddedDocumentField(HostAndPort,
                                        default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT))
    http_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_HTTP_HOST,
                                                                              port=DEFAULT_SERVICE_HTTP_PORT))
    vods_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_VODS_HOST,
                                                                              port=DEFAULT_SERVICE_VODS_PORT))
    cods_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CODS_HOST,
                                                                              port=DEFAULT_SERVICE_CODS_PORT))

    feedback_directory = fields.CharField(default=DEFAULT_FEEDBACK_DIR_PATH)
    timeshifts_directory = fields.CharField(default=DEFAULT_TIMESHIFTS_DIR_PATH)
    hls_directory = fields.CharField(default=DEFAULT_HLS_DIR_PATH)
    playlists_directory = fields.CharField(default=DEFAULT_PLAYLISTS_DIR_PATH)
    dvb_directory = fields.CharField(default=DEFAULT_DVB_DIR_PATH)
    capture_card_directory = fields.CharField(default=DEFAULT_CAPTURE_DIR_PATH)
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
        self.streams.extend(streams)

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

    def to_front_dict(self) -> dict:
        return {ServiceSettings.ID_FIELD: self.get_id(), ServiceSettings.NAME_FIELD: self.name,
                ServiceSettings.HOST_FIELD: self.host, ServiceSettings.HTTP_HOST: self.http_host,
                ServiceSettings.VODS_HOST: self.vods_host, ServiceSettings.CODS_HOST: self.cods_directory,
                ServiceSettings.FEEDBACK_DIRECOTRY: self.feedback_directory,
                ServiceSettings.TIMESHIFTS_DIRECTORY: self.timeshifts_directory,
                ServiceSettings.HLS_DIRECTORY: self.hls_directory,
                ServiceSettings.PLAYLIST_DIRECTORY: self.playlists_directory,
                ServiceSettings.DVB_DIRECTORY: self.dvb_directory,
                ServiceSettings.CAPTURE_CARD_DIRECTORY: self.capture_card_directory,
                ServiceSettings.VODS_IN_DIRECTORY: self.vods_in_directory,
                ServiceSettings.VODS_DIRECTORY: self.vods_directory,
                ServiceSettings.CODS_DIRECTORY: self.cods_directory}
