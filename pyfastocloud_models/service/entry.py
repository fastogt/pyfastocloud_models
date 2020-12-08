from bisect import bisect_right
from datetime import datetime

from bson import ObjectId
from mongoengine import Document, fields, errors, PULL

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import HostAndPort, Maker
from pyfastocloud_models.machine_entry import Machine
from pyfastocloud_models.provider.entry_pair import ProviderPair
from pyfastocloud_models.series.entry import Serial
from pyfastocloud_models.stream.entry import IStream
from pyfastocloud_models.utils.utils import date_to_utc_msec


class ServiceSettings(Document, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    HOST_FIELD = 'host'
    HTTP_HOST_FIELD = 'http_host'
    VODS_HOST_FIELD = 'vods_host'
    CODS_HOST_FIELD = 'cods_host'
    NGINX_HOST_FIELD = 'nginx_host'
    RTMP_HOST_FIELD = 'rtmp_host'
    FEEDBACK_DIRECOTRY_FIELD = 'feedback_directory'
    TIMESHIFTS_DIRECTORY_FIELD = 'timeshifts_directory'
    HLS_DIRECTORY_FIELD = 'hls_directory'
    VODS_DIRECTORY_FIELD = 'vods_directory'
    CODS_DIRECTORY_FIELD = 'cods_directory'
    PROXY_DIRECTORY_FIELD = 'proxy_directory'
    DATA_DIRECTORY_FIELD = 'data_directory'
    PROVIDERS_FIELD = 'providers'
    PRICE_PACKAGE_FIELD = 'price_package'
    CREATED_DATE_FIELD = 'created_date'
    MONITORING_FILED = 'monitoring'
    AUTO_START_FIELD = 'auto_start'
    ACTIVATION_KEY_FIELD = 'activation_key'
    DESCRIPTION_FIELD = 'description'

    meta = {'collection': 'services', 'allow_inheritance': False}

    @staticmethod
    def get_by_id(sid: ObjectId):
        return ServiceSettings.objects(id=sid).first()

    DEFAULT_SERVICE_NAME = 'Service'
    MIN_SERVICE_NAME_LENGTH = 3
    MAX_SERVICE_NAME_LENGTH = 30

    DEFAULT_FEEDBACK_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/feedback'
    DEFAULT_TIMESHIFTS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/timeshifts'
    DEFAULT_HLS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/hls'
    DEFAULT_VODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/vods'
    DEFAULT_CODS_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/cods'
    DEFAULT_PROXY_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/proxy'
    DEFAULT_DATA_DIR_PATH = constants.DEFAULT_SERVICE_ROOT_DIR_PATH + '/data'

    DEFAULT_SERVICE_HOST = '127.0.0.1'
    DEFAULT_SERVICE_PORT = 6317
    DEFAULT_SERVICE_HTTP_HOST = '0.0.0.0'
    DEFAULT_SERVICE_HTTP_PORT = 8000
    DEFAULT_SERVICE_VODS_HOST = '0.0.0.0'
    DEFAULT_SERVICE_VODS_PORT = 7000
    DEFAULT_SERVICE_CODS_HOST = '0.0.0.0'
    DEFAULT_SERVICE_CODS_PORT = 6001
    DEFAULT_SERVICE_NGINX_HOST = '0.0.0.0'
    DEFAULT_SERVICE_NGINX_PORT = 81
    DEFAULT_SERVICE_RTMP_HOST = '0.0.0.0'
    DEFAULT_SERVICE_RTMP_PORT = 1935

    streams = fields.ListField(fields.ReferenceField(IStream), blank=True)
    series = fields.ListField(fields.ReferenceField(Serial, on_delete=PULL), blank=True)
    providers = fields.EmbeddedDocumentListField(ProviderPair, blank=True)

    name = fields.StringField(default=DEFAULT_SERVICE_NAME, max_length=MAX_SERVICE_NAME_LENGTH,
                              min_length=MIN_SERVICE_NAME_LENGTH, required=True)
    host = fields.EmbeddedDocumentField(HostAndPort,
                                        default=HostAndPort(host=DEFAULT_SERVICE_HOST, port=DEFAULT_SERVICE_PORT),
                                        required=True)
    http_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_HTTP_HOST,
                                                                              port=DEFAULT_SERVICE_HTTP_PORT),
                                             required=True)
    vods_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_VODS_HOST,
                                                                              port=DEFAULT_SERVICE_VODS_PORT),
                                             required=True)
    cods_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_CODS_HOST,
                                                                              port=DEFAULT_SERVICE_CODS_PORT),
                                             required=True)
    nginx_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_NGINX_HOST,
                                                                               port=DEFAULT_SERVICE_NGINX_PORT),
                                              required=True)
    rtmp_host = fields.EmbeddedDocumentField(HostAndPort, default=HostAndPort(host=DEFAULT_SERVICE_RTMP_HOST,
                                                                              port=DEFAULT_SERVICE_RTMP_PORT),
                                             required=True)

    feedback_directory = fields.StringField(default=DEFAULT_FEEDBACK_DIR_PATH, required=True)
    timeshifts_directory = fields.StringField(default=DEFAULT_TIMESHIFTS_DIR_PATH, required=True)
    hls_directory = fields.StringField(default=DEFAULT_HLS_DIR_PATH, required=True)
    vods_directory = fields.StringField(default=DEFAULT_VODS_DIR_PATH, required=True)
    cods_directory = fields.StringField(default=DEFAULT_CODS_DIR_PATH, required=True)
    proxy_directory = fields.StringField(default=DEFAULT_PROXY_DIR_PATH, required=True)
    data_directory = fields.StringField(default=DEFAULT_DATA_DIR_PATH, required=True)

    price_package = fields.FloatField(default=constants.DEFAULT_PRICE, min_value=constants.MIN_PRICE,
                                      max_value=constants.MAX_PRICE, required=True)

    auto_start = fields.BooleanField(default=False, required=True)
    activation_key = fields.StringField(max_length=constants.ACTIVATION_KEY_LENGTH,
                                        min_length=constants.ACTIVATION_KEY_LENGTH, required=False)
    monitoring = fields.BooleanField(default=False, required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)  #
    description = fields.StringField(required=False, blank=True)
    # stats
    stats = fields.EmbeddedDocumentListField(Machine, blank=True)

    def get_net_bytes(self, start_timestamp) -> float:
        stats_len = len(self.stats)
        if stats_len < 2:
            return 0.0

        fake = Machine(timestamp=start_timestamp)
        ind = bisect_right(self.stats, fake)
        if ind == stats_len:
            return 0.0

        first = self.stats[ind]
        result = 0.0
        for i in range(ind + 1, stats_len):
            cur = self.stats[i]
            if first.total_bytes_out < cur.total_bytes_out:
                result += cur.total_bytes_out - first.total_bytes_out
            first = cur

        return result

    def get_store_bytes(self, start_timestamp) -> float:
        stats_len = len(self.stats)
        if stats_len == 0:
            return 0.0

        fake = Machine(timestamp=start_timestamp)
        ind = bisect_right(self.stats, fake)
        if ind == stats_len:
            last = self.stats[stats_len - 1]
            if last.timestamp == start_timestamp:
                return last.hdd_used
            return 0.0

        result = 0.0
        for i in range(ind, stats_len):
            result += self.stats[i].hdd_used

        return result / (stats_len - ind)

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

    def get_nginx_host(self) -> str:
        return 'http://{0}'.format(str(self.nginx_host))

    def get_rtmp_host(self) -> str:
        return 'rtmp://{0}'.format(str(self.rtmp_host))

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

    def add_stat(self, stat: Machine):
        if not stat:
            return

        self.stats.append(stat)

    def remove_stat(self, stat: Machine):
        if not stat:
            return

        self.stats.remove(stat)

    def add_series(self, serials: [Serial]):
        for serial in serials:
            if serial:
                self.add_serial(serial)

    def add_serial(self, serial: Serial):
        if serial:
            self.series.append(serial)

    def remove_serial(self, serial: Serial):
        if serial:
            self.series.remove(serial)
            serial.delete()

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

    def find_stream_by_id(self, sid: ObjectId) -> IStream:
        for stream in self.streams:
            if stream.id == sid:
                return stream

        return None

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def delete(self, *args, **kwargs):
        for stream in self.streams:
            if stream:
                stream.delete()
        return super(ServiceSettings, self).delete(*args, **kwargs)

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, name = self.check_required_type(ServiceSettings.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, host = self.check_required_type(ServiceSettings.HOST_FIELD, dict, json)
        if res:  # required field
            self.host = HostAndPort.make_entry(host)

        res, http_host = self.check_required_type(ServiceSettings.HTTP_HOST_FIELD, dict, json)
        if res:  # required field
            self.http_host = HostAndPort.make_entry(http_host)

        res, vods_host = self.check_required_type(ServiceSettings.VODS_HOST_FIELD, dict, json)
        if res:  # required field
            self.vods_host = HostAndPort.make_entry(vods_host)

        res, cods_host = self.check_required_type(ServiceSettings.CODS_HOST_FIELD, dict, json)
        if res:  # required field
            self.cods_host = HostAndPort.make_entry(cods_host)

        res, nginx_host = self.check_required_type(ServiceSettings.NGINX_HOST_FIELD, dict, json)
        if res:  # required field
            self.nginx_host = HostAndPort.make_entry(nginx_host)

        res, rtmp_host = self.check_required_type(ServiceSettings.RTMP_HOST_FIELD, dict, json)
        if res:  # required field
            self.rtmp_host = HostAndPort.make_entry(rtmp_host)

        res, feedback = self.check_required_type(ServiceSettings.FEEDBACK_DIRECOTRY_FIELD, str, json)
        if res:  # required field
            self.feedback_directory = feedback

        res, timeshift = self.check_required_type(ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.timeshifts_directory = timeshift

        res, hls = self.check_required_type(ServiceSettings.HLS_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.hls_directory = hls

        res, vods = self.check_required_type(ServiceSettings.VODS_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.vods_directory = vods

        res, cods = self.check_required_type(ServiceSettings.CODS_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.cods_directory = cods

        res, proxy = self.check_required_type(ServiceSettings.PROXY_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.proxy_directory = proxy

        res, data = self.check_required_type(ServiceSettings.DATA_DIRECTORY_FIELD, str, json)
        if res:  # required field
            self.data_directory = data

        res, price_package = self.check_required_type(ServiceSettings.PRICE_PACKAGE_FIELD, float, json)
        if res:  # required field
            self.price_package = price_package

        res, created_date_msec = self.check_optional_type(ServiceSettings.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, monitoring = self.check_required_type(ServiceSettings.MONITORING_FILED, bool, json)
        if res:  # required field
            self.monitoring = monitoring

        res, auto_start = self.check_required_type(ServiceSettings.AUTO_START_FIELD, bool, json)
        if res:  # required field
            self.auto_start = auto_start

        res, activation_key = self.check_optional_type(ServiceSettings.ACTIVATION_KEY_FIELD, str, json)
        if res:  # optional field
            self.activation_key = activation_key

        res, description = self.check_optional_type(ServiceSettings.DESCRIPTION_FIELD, str, json)
        if res:  # optional field
            self.description = description

        try:
            self.validate()
        except errors.ValidationError as err:
            raise ValueError(err.message)

    def to_front_dict(self) -> dict:
        providers = []
        for prov in self.providers:
            providers.append(prov.to_front_dict())
        return {ServiceSettings.ID_FIELD: self.get_id(), ServiceSettings.NAME_FIELD: self.name,
                ServiceSettings.HOST_FIELD: self.host.to_front_dict(),
                ServiceSettings.HTTP_HOST_FIELD: self.http_host.to_front_dict(),
                ServiceSettings.VODS_HOST_FIELD: self.vods_host.to_front_dict(),
                ServiceSettings.CODS_HOST_FIELD: self.cods_host.to_front_dict(),
                ServiceSettings.NGINX_HOST_FIELD: self.nginx_host.to_front_dict(),
                ServiceSettings.RTMP_HOST_FIELD: self.rtmp_host.to_front_dict(),
                ServiceSettings.FEEDBACK_DIRECOTRY_FIELD: self.feedback_directory,
                ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD: self.timeshifts_directory,
                ServiceSettings.HLS_DIRECTORY_FIELD: self.hls_directory,
                ServiceSettings.VODS_DIRECTORY_FIELD: self.vods_directory,
                ServiceSettings.CODS_DIRECTORY_FIELD: self.cods_directory,
                ServiceSettings.PROXY_DIRECTORY_FIELD: self.proxy_directory,
                ServiceSettings.DATA_DIRECTORY_FIELD: self.data_directory,
                ServiceSettings.PRICE_PACKAGE_FIELD: self.price_package,
                ServiceSettings.MONITORING_FILED: self.monitoring,
                ServiceSettings.AUTO_START_FIELD: self.auto_start,
                ServiceSettings.ACTIVATION_KEY_FIELD: self.activation_key,
                ServiceSettings.DESCRIPTION_FIELD: self.description,
                ServiceSettings.CREATED_DATE_FIELD: self.created_date_utc_msec(),
                ServiceSettings.PROVIDERS_FIELD: providers}

    def is_valid(self) -> bool:
        try:
            self.validate()
        except errors.ValidationError:
            return False
        return True
