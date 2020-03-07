from enum import IntEnum

from bson import ObjectId
from pymodm import MongoModel, fields, EmbeddedMongoModel

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort
from pyfastocloud_models.stream.entry import IStream
from pyfastocloud_models.series.entry import Serial


# #EXTM3U
# #EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Amptv.png/330px-Amptv.png" group-title="Armenia(Հայաստան)",1TV
# http://amtv1.livestreamingcdn.com/am2abr/tracks-v1a1/index.m3u8

class ProviderPair(EmbeddedMongoModel):
    class Roles(IntEnum):
        READ = 0
        WRITE = 1
        SUPPORT = 2
        ADMIN = 3

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    user = fields.ReferenceField('Provider')
    role = fields.IntegerField(min_value=Roles.READ, max_value=Roles.ADMIN, default=Roles.ADMIN)


class ServiceSettings(MongoModel):
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

    streams = fields.ListField(fields.ReferenceField(IStream, on_delete=fields.ReferenceField.PULL), default=[],
                               blank=True)
    series = fields.ListField(fields.ReferenceField(Serial, on_delete=fields.ReferenceField.PULL), default=[],
                              blank=True)
    providers = fields.EmbeddedDocumentListField(ProviderPair, default=[])

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
        self.save()

    def add_stream(self, stream: IStream):
        if stream:
            self.streams.append(stream)
            self.save()

    def remove_stream(self, stream: IStream):
        if stream:
            self.streams.remove(stream)
            stream.delete()
            self.save()

    def remove_all_streams(self):
        for stream in list(self.streams):
            stream.delete()
        self.streams = []
        self.save()

    def add_provider(self, user: ProviderPair):
        if user:
            self.providers.append(user)
            self.save()

    def remove_provider(self, provider):
        for prov in list(self.providers):
            if prov.user == provider:
                self.providers.remove(provider)
        self.save()

    def find_stream_settings_by_id(self, sid: ObjectId):
        for stream in self.streams:
            if stream.id == sid:
                return stream

        return None

    def delete(self, *args, **kwargs):
        for stream in self.streams:
            stream.delete()
        return super(ServiceSettings, self).delete(*args, **kwargs)
