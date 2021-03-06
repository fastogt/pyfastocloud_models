import os
from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse

from bson.objectid import ObjectId
from mongoengine import Document, fields, PULL, errors
from pyfastogt.maker import Maker

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Rational, Size, Logo, RSVGLogo, InputUrl, OutputUrl, MetaUrl, \
    MachineLearning
from pyfastocloud_models.utils.utils import date_to_utc_msec


class StreamLogLevel(IntEnum):
    LOG_LEVEL_EMERG = 0
    LOG_LEVEL_ALERT = 1
    LOG_LEVEL_CRIT = 2
    LOG_LEVEL_ERR = 3
    LOG_LEVEL_WARNING = 4
    LOG_LEVEL_NOTICE = 5
    LOG_LEVEL_INFO = 6
    LOG_LEVEL_DEBUG = 7

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(int(item)) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)


class IStream(Document, Maker):
    NAME_FIELD = 'name'
    ID_FIELD = 'id'
    PRICE_FIELD = 'price'
    GROUPS_FIELD = 'groups'
    VISIBLE_FIELD = 'visible'
    IARC_FIELD = 'iarc'
    VIEW_COUNT_FIELD = 'view_count'
    TYPE_FIELD = 'type'
    CREATED_DATE_FIELD = 'created_date'
    OUTPUT_FIELD = 'output'
    ICON_FIELD = 'tvg_logo'
    TVG_ID_FIELD = 'tvg_id'
    TVG_NAME_FIELD = 'tvg_name'
    PARTS_FIELD = 'parts'
    META_FIELD = 'meta'

    meta = {'collection': 'streams', 'allow_inheritance': True}

    @staticmethod
    def all():
        return IStream.objects.all()

    @staticmethod
    def get_by_id(sid: ObjectId):
        return IStream.objects.get(id=sid)

    # required
    name = fields.StringField(min_length=constants.MIN_STREAM_NAME_LENGTH, max_length=constants.MAX_STREAM_NAME_LENGTH,
                              required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)

    price = fields.FloatField(default=constants.DEFAULT_PRICE, min_value=constants.MIN_PRICE,
                              max_value=constants.MAX_PRICE, required=True)
    visible = fields.BooleanField(default=True, required=True)
    iarc = fields.IntField(default=constants.DEFAULT_IARC, min_value=constants.MIN_IARC,
                           max_value=constants.MAX_IARC,
                           required=True)  # https://support.google.com/googleplay/answer/6209544
    view_count = fields.IntField(default=0, required=True)
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)

    # blanks
    tvg_logo = fields.StringField(max_length=constants.MAX_STREAM_ICON_LENGTH,
                                  min_length=constants.MIN_STREAM_ICON_LENGTH)
    groups = fields.ListField(fields.StringField())
    tvg_id = fields.StringField(min_length=constants.MIN_STREAM_TVG_ID_LENGTH,
                                max_length=constants.MAX_STREAM_TVG_ID_LENGTH)
    tvg_name = fields.StringField(min_length=constants.MIN_STREAM_TVG_NAME_LENGTH,
                                  max_length=constants.MAX_STREAM_TVG_NAME_LENGTH)  # for inner use
    # optional
    parts = fields.ListField(fields.ReferenceField('IStream'))
    meta_urls = fields.EmbeddedDocumentListField(MetaUrl, db_field='meta')

    def to_front_dict(self) -> dict:
        result = self.to_mongo()
        result.pop('_cls')
        result.pop('_id')
        result[IStream.CREATED_DATE_FIELD] = self.created_date_utc_msec()
        result[IStream.TYPE_FIELD] = self.get_type()
        result[IStream.ID_FIELD] = self.get_id()

        output = []
        for out in self.output:
            output.append(out.to_front_dict())
        result[IStream.OUTPUT_FIELD] = output

        parts = []
        for part in self.parts:
            parts.append(str(part))
        result[IStream.PARTS_FIELD] = parts

        meta = []
        for met in self.meta_urls:
            meta.append(met.to_front_dict())
        result[IStream.META_FIELD] = meta
        return result.to_dict()

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def add_part(self, stream):
        if not stream:
            return

        if stream not in self.parts:
            self.parts.append(stream)

    def remove_part(self, stream):
        if not stream:
            return

        try:
            self.parts.remove(stream)
        except ValueError:
            pass

    def get_type(self) -> constants.StreamType:
        raise NotImplementedError('subclasses must override get_type()!')

    @property
    def id(self) -> ObjectId:
        return self.pk

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def main_group(self) -> str:
        if self.groups and len(self.groups):
            return self.groups[0]
        return str()

    @property
    def stable_name(self):
        if not self.tvg_name:
            return self.name

        return self.tvg_name

    def generate_playlist(self, header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or \
                stream_type == constants.StreamType.COD_RELAY or stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or \
                stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output:
                result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                    self.tvg_id, self.stable_name, self.tvg_logo, self.main_group, self.name, out.uri)

        return result

    def generate_playlist_dict(self) -> [dict]:
        result = []
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or \
                stream_type == constants.StreamType.COD_RELAY or stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or \
                stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output:
                result.append(
                    {'tvg-id': self.tvg_id, 'tvg-name': self.stable_name, 'tvg-logo': self.tvg_logo,
                     'groups': self.groups,
                     'url': out.uri})

        return result

    def generate_device_playlist(self, uid: str, pass_hash: str, did: str, lb_server_host_and_port: str,
                                 header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or \
                stream_type == constants.StreamType.COD_RELAY or stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or \
                stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output:
                parsed_uri = urlparse(out.uri)
                if parsed_uri.scheme == 'http' or parsed_uri.scheme == 'https':
                    file_name = os.path.basename(parsed_uri.path)
                    url = 'http://{0}/{1}/{2}/{3}/{4}/{5}/{6}'.format(lb_server_host_and_port, uid, pass_hash, did,
                                                                      self.id,
                                                                      out.id, file_name)
                else:
                    url = out.uri
                result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'. \
                    format(self.tvg_id, self.stable_name, self.tvg_logo, self.main_group, self.name, url)

        return result

    def generate_device_playlist_dict(self, uid: str, pass_hash: str, did: str, lb_server_host_and_port: str) -> [dict]:
        result = []
        stream_type = self.get_type()
        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.VOD_RELAY or \
                stream_type == constants.StreamType.COD_RELAY or stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.COD_ENCODE or \
                stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.VOD_PROXY or \
                stream_type == constants.StreamType.VOD_ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or stream_type == constants.StreamType.CATCHUP:
            for out in self.output:
                parsed_uri = urlparse(out.uri)
                if parsed_uri.scheme == 'http' or parsed_uri.scheme == 'https':
                    file_name = os.path.basename(parsed_uri.path)
                    url = 'http://{0}/{1}/{2}/{3}/{4}/{5}/{6}'.format(lb_server_host_and_port, uid, pass_hash, did,
                                                                      self.id,
                                                                      out.id, file_name)
                else:
                    url = out.uri

                result.append({'tvg-id': self.tvg_id, 'tvg-name': self.stable_name, 'tvg-logo': self.tvg_logo,
                               'groups': self.groups, 'url': url})

        return result

    def generate_input_playlist(self, header=True) -> str:
        raise NotImplementedError('subclasses must override generate_input_playlist()!')

    def fixup_input_urls(self, settings):
        return

    def fixup_output_urls(self, settings):
        return

    def save(self, settings=None):
        if self.pk is None:
            self.pk = ObjectId()
        self.fixup_input_urls(settings)
        self.fixup_output_urls(settings)
        return super(IStream, self).save()

    def delete(self, signal_kwargs=None, **write_concern):
        from pyfastocloud_models.subscriber.entry import Subscriber
        from pyfastocloud_models.series.entry import Serial
        subscribers = Subscriber.objects.all()
        for subscriber in subscribers:
            subscriber.remove_official_stream(self)
            subscriber.remove_official_vod(self)
            subscriber.remove_official_catchup(self)
            subscriber.save()

        serials = Serial.objects.all()
        for serial in serials:
            serial.remove_episode(self)
            serial.save()
        return super(IStream, self).delete(signal_kwargs, **write_concern)

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, name = self.check_required_type(IStream.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, created_date_msec = self.check_optional_type(IStream.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, groups = self.check_optional_type(IStream.GROUPS_FIELD, list, json)
        if res:  # optional field
            self.groups = groups
        else:
            self.groups = []

        res, tvg_id = self.check_optional_type(IStream.TVG_ID_FIELD, str, json)
        if res and tvg_id:  # optional field
            self.tvg_id = tvg_id
        else:
            self.tvg_id = None

        res, tvg_name = self.check_optional_type(IStream.TVG_NAME_FIELD, str, json)
        if res and tvg_name:  # optional field
            self.tvg_name = tvg_name
        else:
            self.tvg_name = None

        res, icon = self.check_optional_type(IStream.ICON_FIELD, str, json)
        if res and icon:  # optional field
            self.tvg_logo = icon
        else:
            self.tvg_logo = None

        res, price = self.check_optional_type(IStream.PRICE_FIELD, float, json)
        if res:  # optional field
            self.price = price

        res, visible = self.check_optional_type(IStream.VISIBLE_FIELD, bool, json)
        if res:  # optional field
            self.visible = visible

        res, iarc = self.check_optional_type(IStream.IARC_FIELD, int, json)
        if res:  # optional field
            self.iarc = iarc

        res, output = self.check_required_type(IStream.OUTPUT_FIELD, list, json)
        if res:  # optional field
            stabled = []
            for url in output:
                stabled.append(OutputUrl.make_entry(url))
            self.output = stabled

        res, meta = self.check_optional_type(IStream.META_FIELD, list, json)
        if res:  # optional field
            meta_stabled = []
            for met in meta:
                meta_stabled.append(MetaUrl.make_entry(met))
            self.meta_urls = meta_stabled

    @staticmethod
    def make_stream_entry(json: dict):
        if not json:
            raise ValueError('Invalid input')

        stream_type = json[IStream.TYPE_FIELD]
        if stream_type == constants.StreamType.PROXY:
            return ProxyStream.make_entry(json)
        elif stream_type == constants.StreamType.VOD_PROXY:
            return ProxyVodStream.make_entry(json)
        elif stream_type == constants.StreamType.RELAY:
            return RelayStream.make_entry(json)
        elif stream_type == constants.StreamType.ENCODE:
            return EncodeStream.make_entry(json)
        elif stream_type == constants.StreamType.TIMESHIFT_RECORDER:
            return TimeshiftRecorderStream.make_entry(json)
        elif stream_type == constants.StreamType.TIMESHIFT_PLAYER:
            return TimeshiftPlayerStream.make_entry(json)
        elif stream_type == constants.StreamType.CATCHUP:
            return CatchupStream.make_entry(json)
        elif stream_type == constants.StreamType.TEST_LIFE:
            return TestLifeStream.make_entry(json)
        elif stream_type == constants.StreamType.VOD_RELAY:
            return VodRelayStream.make_entry(json)
        elif stream_type == constants.StreamType.VOD_ENCODE:
            return VodEncodeStream.make_entry(json)
        elif stream_type == constants.StreamType.COD_RELAY:
            return CodRelayStream.make_entry(json)
        elif stream_type == constants.StreamType.COD_ENCODE:
            return CodEncodeStream.make_entry(json)
        elif stream_type == constants.StreamType.CV_DATA:
            return CvDataStream.make_entry(json)
        else:
            return ChangerStream.make_entry(json)

    def is_valid(self) -> bool:
        try:
            self.validate()
        except errors.ValidationError:
            return False
        return True


class ProxyStream(IStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)

    def __init__(self, *args, **kwargs):
        super(ProxyStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.PROXY

    def generate_input_playlist(self, header=True) -> str:
        return self.generate_playlist(header)


class HardwareStream(IStream):
    LOG_LEVEL_FIELD = 'log_level'
    INPUT_FIELD = 'input'
    HAVE_VIDEO_FIELD = 'have_video'
    HAVE_AUDIO_FIELD = 'have_audio'
    AUDIO_SELECT_FIELD = 'audio_select'
    AUDIO_TRACKS_COUNT_FIELD = 'audio_tracks_count'
    LOOP_FIELD = 'loop'
    RELAY_VIDEO_TYPE_FIELD = 'relay_video_type'
    RELAY_AUDIO_TYPE_FIELD = 'relay_audio_type'
    RESTART_ATTEMPTS_FIELD = 'restart_attempts'
    AUTO_EXIT_TIME_FIELD = 'auto_exit_time'
    PHOENIX_FIELD = 'phoenix'
    EXTRA_CONFIG_FIELD = 'extra_config'
    AUTO_START_FIELD = 'auto_start'

    # required
    log_level = fields.IntField(default=StreamLogLevel.LOG_LEVEL_INFO, min_value=StreamLogLevel.LOG_LEVEL_EMERG,
                                max_value=StreamLogLevel.LOG_LEVEL_DEBUG, required=True)
    restart_attempts = fields.IntField(default=constants.DEFAULT_RESTART_ATTEMPTS,
                                       min_value=constants.MIN_RESTART_ATTEMPTS,
                                       max_value=constants.MAX_RESTART_ATTEMPTS, required=True)
    have_video = fields.BooleanField(default=constants.DEFAULT_HAVE_VIDEO, required=True)
    have_audio = fields.BooleanField(default=constants.DEFAULT_HAVE_AUDIO, required=True)
    loop = fields.BooleanField(default=constants.DEFAULT_LOOP, required=True)
    relay_video_type = fields.IntField(default=constants.RelayType.RELAY_DEEP,
                                       min_value=constants.RelayType.RELAY_LITE,
                                       max_value=constants.RelayType.RELAY_DEEP, required=True)
    relay_audio_type = fields.IntField(default=constants.RelayType.RELAY_DEEP,
                                       min_value=constants.RelayType.RELAY_LITE,
                                       max_value=constants.RelayType.RELAY_DEEP, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, required=True)
    extra_config = fields.StringField(default='{}', required=True)
    auto_start = fields.BooleanField(default=False, required=True)
    audio_tracks_count = fields.IntField(min_value=1, default=1, required=True)
    phoenix = fields.BooleanField(default=constants.DEFAULT_PHOENIX, required=True)
    # optional
    auto_exit_time = fields.IntField(min_value=constants.MIN_AUTO_EXIT_TIME, max_value=constants.MAX_AUTO_EXIT_TIME,
                                     required=False)
    audio_select = fields.IntField(min_value=constants.MIN_AUDIO_SELECT,
                                   max_value=constants.MAX_AUDIO_SELECT, required=False)

    def __init__(self, *args, **kwargs):
        super(HardwareStream, self).__init__(*args, **kwargs)

    def to_front_dict(self) -> dict:
        base = super(HardwareStream, self).to_front_dict()
        input = []
        for inp in self.input:
            input.append(inp.to_front_dict())
        base[HardwareStream.INPUT_FIELD] = input
        return base

    def update_entry(self, json: dict):
        IStream.update_entry(self, json)

        res, log_level = IStream.check_optional_type(HardwareStream.LOG_LEVEL_FIELD, int, json)
        if res:  # optional field
            self.log_level = log_level

        res, inp = IStream.check_required_type(HardwareStream.INPUT_FIELD, list, json)
        if res:
            stabled = []
            for url in inp:
                stabled.append(InputUrl.make_entry(url))
            self.input = stabled

        res, have_video = IStream.check_optional_type(HardwareStream.HAVE_VIDEO_FIELD, bool, json)
        if res:  # optional field
            self.have_video = have_video

        res, have_audio = IStream.check_optional_type(HardwareStream.HAVE_AUDIO_FIELD, bool, json)
        if res:  # optional field
            self.have_audio = have_audio

        res, relay_video_type = IStream.check_optional_type(HardwareStream.RELAY_VIDEO_TYPE_FIELD, int, json)
        if res:  # optional field
            self.relay_video_type = relay_video_type

        res, relay_audio_type = IStream.check_optional_type(HardwareStream.RELAY_AUDIO_TYPE_FIELD, int, json)
        if res:  # optional field
            self.relay_audio_type = relay_audio_type

        res, auto_start = IStream.check_optional_type(HardwareStream.AUTO_START_FIELD, bool, json)
        if res:  # optional field
            self.auto_start = auto_start

        res, audio_select = IStream.check_optional_type(HardwareStream.AUDIO_SELECT_FIELD, int, json)
        if res:  # optional field
            self.audio_select = audio_select
        else:
            delattr(self, HardwareStream.AUDIO_SELECT_FIELD)

        res, audio_tracks_count = IStream.check_optional_type(HardwareStream.AUDIO_TRACKS_COUNT_FIELD, int, json)
        if res:  # optional field
            self.audio_tracks_count = audio_tracks_count

        res, loop = IStream.check_optional_type(HardwareStream.LOOP_FIELD, bool, json)
        if res:  # optional field
            self.loop = loop

        res, restart = IStream.check_optional_type(HardwareStream.RESTART_ATTEMPTS_FIELD, int, json)
        if res:  # optional field
            self.restart_attempts = restart

        res, auto_exit = IStream.check_optional_type(HardwareStream.AUTO_EXIT_TIME_FIELD, int, json)
        if res:  # optional field
            self.auto_exit_time = auto_exit
        else:
            delattr(self, HardwareStream.AUTO_EXIT_TIME_FIELD)

        res, phoenix = IStream.check_optional_type(HardwareStream.PHOENIX_FIELD, bool, json)
        if res:  # optional field
            self.phoenix = phoenix

        res, extra = IStream.check_optional_type(HardwareStream.EXTRA_CONFIG_FIELD, str, json)
        if res:  # optional field
            self.extra_config = extra

    def get_type(self) -> constants.StreamType:
        raise NotImplementedError('subclasses must override get_type()!')

    def get_log_level(self):
        return self.log_level

    def get_audio_select(self):
        return self.audio_select

    def get_audio_tracks_count(self):
        return self.audio_tracks_count

    def get_have_video(self):
        return self.have_video

    def get_have_audio(self):
        return self.have_audio

    def get_phoenix(self):
        return self.phoenix

    def get_loop(self):
        return self.loop

    def get_relay_video_type(self):
        return self.relay_video_type

    def get_relay_audio_type(self):
        return self.relay_audio_type

    def get_restart_attempts(self):
        return self.restart_attempts

    def get_auto_exit_time(self):
        return self.auto_exit_time

    def generate_input_playlist(self, header=True) -> str:
        result = '#EXTM3U\n' if header else ''
        stream_type = self.get_type()

        if stream_type == constants.StreamType.RELAY or stream_type == constants.StreamType.ENCODE or \
                stream_type == constants.StreamType.TIMESHIFT_PLAYER or \
                stream_type == constants.StreamType.VOD_ENCODE or stream_type == constants.StreamType.VOD_RELAY:
            for out in self.input:
                result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                    self.tvg_id, self.tvg_name, self.tvg_logo, self.main_group, self.name, out.uri)

        return result

    def generate_http_link(self, settings, hls_type: constants.HlsType, hlssink_type: int, chunk_duration=10,
                           playlist_name=constants.DEFAULT_HLS_PLAYLIST, oid=OutputUrl.generate_id()) -> OutputUrl:
        if not settings:
            raise ValueError('Invalid input, settings required')

        http_root = self._generate_http_root_dir(settings.hls_directory, oid)
        link = '{0}/{1}'.format(http_root, playlist_name)
        result = OutputUrl(id=oid, uri=settings.generate_http_link(link), http_root=http_root)
        if hls_type is not None:
            result.hls_type = hls_type
        if hlssink_type is not None:
            result.hlssink_type = hlssink_type
        if chunk_duration is not None:
            result.chunk_duration = chunk_duration
        return result

    def generate_vod_link(self, settings, hls_type: constants.HlsType, hlssink_type: int, chunk_duration=10,
                          playlist_name=constants.DEFAULT_HLS_PLAYLIST,
                          oid=OutputUrl.generate_id()) -> OutputUrl:
        if not settings:
            raise ValueError('Invalid input, settings required')

        vods_root = self._generate_vods_root_dir(settings.vods_directory, oid)
        link = '{0}/{1}'.format(vods_root, playlist_name)
        result = OutputUrl(id=oid, uri=settings.generate_vods_link(link), http_root=vods_root)
        if hls_type is not None:
            result.hls_type = hls_type
        if hlssink_type is not None:
            result.hlssink_type = hlssink_type
        if chunk_duration is not None:
            result.chunk_duration = chunk_duration
        return result

    def generate_cod_link(self, settings, hls_type: constants.HlsType, hlssink_type: int, chunk_duration=5,
                          playlist_name=constants.DEFAULT_HLS_PLAYLIST,
                          oid=OutputUrl.generate_id()) -> OutputUrl:
        if not settings:
            raise ValueError('Invalid input, settings required')

        cods_root = self._generate_cods_root_dir(settings.cods_directory, oid)
        link = '{0}/{1}'.format(cods_root, playlist_name)
        result = OutputUrl(id=oid, uri=settings.generate_cods_link(link), http_root=cods_root)
        if hls_type is not None:
            result.hls_type = hls_type
        if hlssink_type is not None:
            result.hlssink_type = hlssink_type
        if chunk_duration is not None:
            result.chunk_duration = chunk_duration
        return result

    def fixup_output_urls(self, settings):
        return

    # private
    def _generate_http_root_dir(self, hls_directory: str, oid: int):
        return '{0}/{1}/{2}/{3}'.format(hls_directory, self.get_type(), self.get_id(), oid)

    def _generate_vods_root_dir(self, vods_directory: str, oid: int):
        return '{0}/{1}/{2}/{3}'.format(vods_directory, self.get_type(), self.get_id(), oid)

    def _generate_cods_root_dir(self, cods_directory: str, oid: int):
        return '{0}/{1}/{2}/{3}'.format(cods_directory, self.get_type(), self.get_id(), oid)

    def _fixup_http_output_urls(self, settings):
        if not settings:
            return

        for idx, val in enumerate(self.output):
            url = val.uri
            if constants.is_special_url(url):
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output[idx] = self.generate_http_link(settings, val.hls_type, val.hlssink_type, val.chunk_duration,
                                                           filename, val.id)

    def _fixup_vod_output_urls(self, settings):
        if not settings:
            return

        for idx, val in enumerate(self.output):
            url = val.uri
            if constants.is_special_url(url):
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output[idx] = self.generate_vod_link(settings, val.hls_type, val.hlssink_type, val.chunk_duration,
                                                          filename, val.id)

    def _fixup_cod_output_urls(self, settings):
        if not settings:
            return

        for idx, val in enumerate(self.output):
            url = val.uri
            if constants.is_special_url(url):
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self.output[idx] = self.generate_cod_link(settings, val.hls_type, val.hlssink_type, val.chunk_duration,
                                                          filename, val.id)


class RelayStream(HardwareStream):
    VIDEO_PARSER_FIELD = 'video_parser'
    AUDIO_PARSER_FIELD = 'audio_parser'

    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, required=True)

    video_parser = fields.StringField(required=False)
    audio_parser = fields.StringField(required=False)

    def __init__(self, *args, **kwargs):
        super(RelayStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        HardwareStream.update_entry(self, json)

        res, video = IStream.check_optional_type(RelayStream.VIDEO_PARSER_FIELD, str, json)
        if res:  # optional field
            self.video_parser = video
        else:
            delattr(self, RelayStream.VIDEO_PARSER_FIELD)

        res, audio = IStream.check_optional_type(RelayStream.AUDIO_PARSER_FIELD, str, json)
        if res:  # optional field
            self.audio_parser = audio
        else:
            delattr(self, RelayStream.AUDIO_PARSER_FIELD)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.RELAY

    def get_video_parser(self):
        return self.video_parser

    def get_audio_parser(self):
        return self.audio_parser

    def fixup_output_urls(self, settings):
        return self._fixup_http_output_urls(settings)


class EncodeStream(HardwareStream):
    RELAY_AUDIO_FIELD = 'relay_audio'
    RELAY_VIDEO_FIELD = 'relay_video'
    DEINTERLACE_FIELD = 'deinterlace'
    FRAME_RATE_FIELD = 'frame_rate'
    VOLUME_FIELD = 'volume'
    VIDEO_CODEC_FIELD = 'video_codec'
    AUDIO_CODEC_FIELD = 'audio_codec'
    AUDIO_CHANNELS_COUNT_FIELD = 'audio_channels_count'
    SIZE_FIELD = 'size'
    MACHINE_LEARNING_FIELD = 'machine_learning'
    VIDEO_BITRATE_FIELD = 'video_bit_rate'
    AUDIO_BITRATE_FIELD = 'audio_bit_rate'
    LOGO_FIELD = 'logo'
    RSVG_LOGO_FIELD = 'rsvg_logo'
    ASPECT_RATIO_FIELD = 'aspect_ratio'

    # required
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, required=True)
    relay_video = fields.BooleanField(default=constants.DEFAULT_RELAY_VIDEO, required=True)
    relay_audio = fields.BooleanField(default=constants.DEFAULT_RELAY_AUDIO, required=True)
    deinterlace = fields.BooleanField(default=constants.DEFAULT_DEINTERLACE, required=True)
    volume = fields.FloatField(default=constants.DEFAULT_VOLUME, min_value=constants.MIN_VOLUME,
                               max_value=constants.MAX_VOLUME, required=True)
    video_codec = fields.StringField(default=constants.DEFAULT_VIDEO_CODEC, required=True)
    audio_codec = fields.StringField(default=constants.DEFAULT_AUDIO_CODEC, required=True)
    # optional
    frame_rate = fields.IntField(min_value=constants.MIN_FRAME_RATE,
                                 max_value=constants.MAX_FRAME_RATE, required=False)
    audio_channels_count = fields.IntField(min_value=constants.MIN_AUDIO_CHANNELS_COUNT,
                                           max_value=constants.MAX_AUDIO_CHANNELS_COUNT, required=False)
    size = fields.EmbeddedDocumentField(Size, required=False)
    machine_learning = fields.EmbeddedDocumentField(MachineLearning, required=False)
    video_bit_rate = fields.IntField(required=False)
    audio_bit_rate = fields.IntField(required=False)
    logo = fields.EmbeddedDocumentField(Logo, required=False)
    rsvg_logo = fields.EmbeddedDocumentField(RSVGLogo, required=False)
    aspect_ratio = fields.EmbeddedDocumentField(Rational, required=False)

    def __init__(self, *args, **kwargs):
        super(EncodeStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        HardwareStream.update_entry(self, json)

        res, video = IStream.check_optional_type(EncodeStream.RELAY_VIDEO_FIELD, bool, json)
        if res:  # optional field
            self.relay_video = video

        res, audio = IStream.check_optional_type(EncodeStream.RELAY_AUDIO_FIELD, bool, json)
        if res:  # optional field
            self.relay_audio = audio

        res, deinter = IStream.check_optional_type(EncodeStream.DEINTERLACE_FIELD, bool, json)
        if res:  # optional field
            self.deinterlace = deinter

        res, frame_rate = IStream.check_optional_type(EncodeStream.FRAME_RATE_FIELD, int, json)
        if res:  # optional field
            self.frame_rate = frame_rate
        else:
            delattr(self, EncodeStream.FRAME_RATE_FIELD)

        res, volume = IStream.check_optional_type(EncodeStream.VOLUME_FIELD, float, json)
        if res:  # optional field
            self.volume = volume

        res, video_codec = IStream.check_optional_type(EncodeStream.VIDEO_CODEC_FIELD, str, json)
        if res:  # optional field
            self.video_codec = video_codec

        res, audio_codec = IStream.check_optional_type(EncodeStream.AUDIO_CODEC_FIELD, str, json)
        if res:  # optional field
            self.audio_codec = audio_codec

        res, audio_channel_count = IStream.check_optional_type(EncodeStream.AUDIO_CHANNELS_COUNT_FIELD, int, json)
        if res:  # optional field
            self.audio_channels_count = audio_channel_count
        else:
            delattr(self, EncodeStream.AUDIO_CHANNELS_COUNT_FIELD)

        res, size = IStream.check_optional_type(EncodeStream.SIZE_FIELD, dict, json)
        if res:  # optional field
            self.size = Size.make_entry(size)
        else:
            delattr(self, EncodeStream.SIZE_FIELD)

        res, learning = IStream.check_optional_type(EncodeStream.MACHINE_LEARNING_FIELD, dict, json)
        if res:  # optional field
            self.machine_learning = MachineLearning.make_entry(learning)
        else:
            delattr(self, EncodeStream.MACHINE_LEARNING_FIELD)

        res, video_bit_rate = IStream.check_optional_type(EncodeStream.VIDEO_BITRATE_FIELD, int, json)
        if res:  # optional field
            self.video_bit_rate = video_bit_rate
        else:
            delattr(self, EncodeStream.VIDEO_BITRATE_FIELD)

        res, audio_bit_rate = IStream.check_optional_type(EncodeStream.AUDIO_BITRATE_FIELD, int, json)
        if res:  # optional field
            self.audio_bit_rate = audio_bit_rate
        else:
            delattr(self, EncodeStream.AUDIO_BITRATE_FIELD)

        res, logo = IStream.check_optional_type(EncodeStream.LOGO_FIELD, dict, json)
        if res:  # optional field
            self.logo = Logo.make_entry(logo)
        else:
            delattr(self, EncodeStream.LOGO_FIELD)

        res, rlogo = IStream.check_optional_type(EncodeStream.RSVG_LOGO_FIELD, dict, json)
        if res:  # optional field
            self.rsvg_logo = RSVGLogo.make_entry(rlogo)
        else:
            delattr(self, EncodeStream.RSVG_LOGO_FIELD)

        res, aspect = IStream.check_optional_type(EncodeStream.ASPECT_RATIO_FIELD, dict, json)
        if res:  # optional field
            self.aspect_ratio = Rational.make_entry(aspect)
        else:
            delattr(self, EncodeStream.ASPECT_RATIO_FIELD)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.ENCODE

    def get_relay_video(self):
        return self.relay_video

    def get_relay_audio(self):
        return self.relay_audio

    def get_deinterlace(self):
        return self.deinterlace

    def get_frame_rate(self):
        return self.frame_rate

    def get_volume(self):
        return self.volume

    def get_video_codec(self):
        return self.video_codec

    def get_audio_codec(self):
        return self.audio_codec

    def get_audio_channels_count(self):
        return self.audio_channels_count

    def get_video_bit_rate(self):
        return self.video_bit_rate

    def get_audio_bit_rate(self):
        return self.audio_bit_rate

    def fixup_output_urls(self, settings):
        return self._fixup_http_output_urls(settings)


class TimeshiftRecorderStream(RelayStream):
    TIMESHIFT_CHUNK_DURATION = 'timeshift_chunk_duration'
    TIMESHIFT_CHUNK_LIFE_TIME = 'timeshift_chunk_life_time'

    # required
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True, blank=True)  #
    timeshift_chunk_duration = fields.IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_DURATION,
                                               min_value=constants.MIN_TIMESHIFT_CHUNK_DURATION, required=True)
    timeshift_chunk_life_time = fields.IntField(default=constants.DEFAULT_TIMESHIFT_CHUNK_LIFE_TIME,
                                                min_value=constants.MIN_TIMESHIFT_CHUNK_LIFE_TIME, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftRecorderStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        RelayStream.update_entry(self, json)

        res, chunk_duration = IStream.check_optional_type(TimeshiftRecorderStream.TIMESHIFT_CHUNK_DURATION, int, json)
        if res:  # optional field
            self.timeshift_chunk_duration = chunk_duration

        res, chunk_life = IStream.check_optional_type(TimeshiftRecorderStream.TIMESHIFT_CHUNK_LIFE_TIME, int, json)
        if res:  # optional field
            self.timeshift_chunk_life_time = chunk_life

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_RECORDER

    def get_timeshift_chunk_duration(self):
        return self.timeshift_chunk_duration

    def fixup_output_urls(self, settings):
        return


class CatchupStream(TimeshiftRecorderStream):
    START_RECORD_FIELD = 'start'
    STOP_RECORD_FIELD = 'stop'

    # required
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)
    start = fields.DateTimeField(default=datetime.utcfromtimestamp(0), required=True)
    stop = fields.DateTimeField(default=datetime.utcfromtimestamp(0), required=True)

    def __init__(self, *args, **kwargs):
        super(CatchupStream, self).__init__(*args, **kwargs)
        self.timeshift_chunk_duration = constants.DEFAULT_CATCHUP_CHUNK_DURATION
        self.auto_exit_time = constants.DEFAULT_CATCHUP_EXIT_TIME

    def start_utc_msec(self):
        return date_to_utc_msec(self.start)

    def stop_utc_msec(self):
        return date_to_utc_msec(self.stop)

    def update_entry(self, json: dict):
        TimeshiftRecorderStream.update_entry(self, json)

        res, start = self.check_required_type(CatchupStream.START_RECORD_FIELD, int, json)
        if res:
            self.start = datetime.utcfromtimestamp(start / 1000)

        res, stop = self.check_required_type(CatchupStream.STOP_RECORD_FIELD, int, json)
        if res:
            self.stop = datetime.utcfromtimestamp(stop / 1000)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.CATCHUP

    def to_front_dict(self) -> dict:
        base = super(HardwareStream, self).to_front_dict()
        base[CatchupStream.START_RECORD_FIELD] = self.start_utc_msec()
        base[CatchupStream.STOP_RECORD_FIELD] = self.stop_utc_msec()
        return base


class TimeshiftPlayerStream(RelayStream):
    TIMESHIFT_DIR_FIELD = 'timeshift_dir'
    TIMESHIFT_DELAY = 'timeshift_delay'

    # required
    input = fields.EmbeddedDocumentListField(InputUrl, required=True, blank=True)  #
    timeshift_dir = fields.StringField(required=True)  # FIXME default
    timeshift_delay = fields.IntField(default=constants.DEFAULT_TIMESHIFT_DELAY,
                                      min_value=constants.MIN_TIMESHIFT_DELAY,
                                      max_value=constants.MAX_TIMESHIFT_DELAY, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftPlayerStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        RelayStream.update_entry(self, json)

        res, timeshift_dir = self.check_optional_type(TimeshiftPlayerStream.TIMESHIFT_DIR_FIELD, str, json)
        if res:  # optional field
            self.timeshift_dir = timeshift_dir

        timeshift_delay_field = self.check_optional_type(TimeshiftPlayerStream.TIMESHIFT_DELAY, int, json)
        if timeshift_delay_field is not None:  # optional field
            self.timeshift_chunk_life_time = timeshift_delay_field

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_PLAYER


class TestLifeStream(RelayStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True, blank=True)  #

    def __init__(self, *args, **kwargs):
        super(TestLifeStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TEST_LIFE

    def fixup_output_urls(self, settings):
        return


class CodRelayStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(CodRelayStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.COD_RELAY

    def fixup_output_urls(self, settings):
        return self._fixup_cod_output_urls(settings)


class CodEncodeStream(EncodeStream):
    def __init__(self, *args, **kwargs):
        super(CodEncodeStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.COD_ENCODE

    def fixup_output_urls(self, settings):
        return self._fixup_cod_output_urls(settings)


# VODS


class VodBasedStream(object):
    DESCRIPTION_FIELD = 'description'  #
    VOD_TYPE_FIELD = 'vod_type'
    TRAILER_URL_FIELD = 'trailer_url'
    USER_SCORE_FIELD = 'user_score'
    PRIME_DATE_FIELD = 'prime_date'
    COUNTRY_FIELD = 'country'
    DURATION_FIELD = 'duration'

    MAX_DATE = datetime(2100, 1, 1)
    MIN_DATE = datetime(1970, 1, 1)
    DEFAULT_COUNTRY = 'Unknown'

    def __init__(self, *args, **kwargs):
        super(VodBasedStream, self).__init__(*args, **kwargs)

    # required
    vod_type = fields.IntField(default=constants.VodType.VODS, required=True)
    user_score = fields.FloatField(default=0, min_value=0, max_value=100, required=True)
    prime_date = fields.DateTimeField(default=MIN_DATE, required=True)
    country = fields.StringField(default=DEFAULT_COUNTRY, required=True)
    duration = fields.IntField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC, required=True)
    # blanks
    trailer_url = fields.StringField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH)
    description = fields.StringField(min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                                     max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH)

    def prime_date_utc_msec(self):
        return date_to_utc_msec(self.prime_date)

    def update_entry(self, json: dict):
        if not json:
            raise ValueError('Invalid input')

        res, vod_type = Maker.check_required_type(VodBasedStream.VOD_TYPE_FIELD, int, json)
        if res:
            self.vod_type = vod_type

        res, description = Maker.check_optional_type(VodBasedStream.DESCRIPTION_FIELD, str, json)
        if res and description:
            self.description = description
        else:
            self.description = None

        res, trailer = Maker.check_optional_type(VodBasedStream.TRAILER_URL_FIELD, str, json)
        if res and trailer:
            self.trailer_url = trailer
        else:
            self.trailer_url = None

        res, score = Maker.check_optional_type(VodBasedStream.USER_SCORE_FIELD, float, json)
        if res:
            self.user_score = score

        res, prime_date = Maker.check_required_type(VodBasedStream.PRIME_DATE_FIELD, int, json)
        if res:
            self.prime_date = datetime.utcfromtimestamp(prime_date / 1000)

        res, country = Maker.check_optional_type(VodBasedStream.COUNTRY_FIELD, str, json)
        if res:
            self.country = country

        res, duration = Maker.check_optional_type(VodBasedStream.DURATION_FIELD, int, json)
        if res:
            self.duration = duration


class ProxyVodStream(ProxyStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(ProxyVodStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        ProxyStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_PROXY

    def to_front_dict(self) -> dict:
        front = ProxyStream.to_front_dict(self)
        front[VodBasedStream.PRIME_DATE_FIELD] = self.prime_date_utc_msec()
        return front


class VodRelayStream(RelayStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodRelayStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        RelayStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_RELAY

    def to_front_dict(self) -> dict:
        front = ProxyStream.to_front_dict(self)
        front[VodBasedStream.PRIME_DATE_FIELD] = self.prime_date_utc_msec()
        return front

    def fixup_output_urls(self, settings):
        return self._fixup_vod_output_urls(settings)


class VodEncodeStream(EncodeStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodEncodeStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        EncodeStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_ENCODE

    def to_front_dict(self) -> dict:
        front = ProxyStream.to_front_dict(self)
        front[VodBasedStream.PRIME_DATE_FIELD] = self.prime_date_utc_msec()
        return front

    def fixup_output_urls(self, settings):
        return self._fixup_vod_output_urls(settings)


class EventStream(VodEncodeStream):
    def get_type(self) -> constants.StreamType:
        return constants.StreamType.EVENT


class CvDataStream(EncodeStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, required=True, blank=True)  #

    def __init__(self, *args, **kwargs):
        super(CvDataStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.CV_DATA


class ChangerStream(EncodeStream):
    def __init__(self, *args, **kwargs):
        super(ChangerStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.CHANGER


# if remove catchup also clean parts
CatchupStream.register_delete_rule(IStream, 'parts', PULL)
