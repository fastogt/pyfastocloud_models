import os
from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse

from bson.objectid import ObjectId
from pymodm import MongoModel, fields, EmbeddedMongoModel

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Rational, Size, Logo, RSVGLogo, InputUrl, OutputUrl
from pyfastocloud_models.utils.utils import date_to_utc_msec


class BaseFields:
    NAME_FIELD = 'name'
    ID_FIELD = 'id'
    PRICE_FIELD = 'price'
    GROUP_FIELD = 'group'
    VISIBLE_FIELD = 'visible'
    IARC_FIELD = 'iarc'
    VIEW_COUNT_FIELD = 'view_count'
    TYPE_FIELD = 'type'


class StreamFields(BaseFields):
    ICON_FIELD = 'icon'


class VodFields(BaseFields):
    DESCRIPTION_FIELD = 'description'  #
    VOD_TYPE_FIELD = 'vod_type'
    TRAILER_URL_FIELD = 'trailer_url'
    USER_SCORE_FIELD = 'user_score'
    PRIME_DATE_FIELD = 'date'
    COUNTRY_FIELD = 'country'
    DURATION_FIELD = 'duration'


class CatchupsFields(BaseFields):
    START_RECORD_FIELD = 'start'
    STOP_RECORD_FIELD = 'stop'


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


class IStream(MongoModel):
    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            stream = IStream.objects.get({'_id': sid})
        except IStream.DoesNotExist:
            return None
        else:
            return stream

    class Meta:
        collection_name = 'streams'
        allow_inheritance = True

    created_date = fields.DateTimeField(default=datetime.now)  # for inner use
    name = fields.CharField(default=constants.DEFAULT_STREAM_NAME, max_length=constants.MAX_STREAM_NAME_LENGTH,
                            min_length=constants.MIN_STREAM_NAME_LENGTH, required=True)
    group = fields.CharField(default=constants.DEFAULT_STREAM_GROUP_TITLE,
                             max_length=constants.MAX_STREAM_GROUP_TITLE_LENGTH,
                             min_length=constants.MIN_STREAM_GROUP_TITLE_LENGTH, required=True, blank=True)

    tvg_id = fields.CharField(default=constants.DEFAULT_STREAM_TVG_ID, max_length=constants.MAX_STREAM_TVG_ID_LENGTH,
                              min_length=constants.MIN_STREAM_TVG_ID_LENGTH, blank=True)
    tvg_name = fields.CharField(default=constants.DEFAULT_STREAM_TVG_NAME, max_length=constants.MAX_STREAM_NAME_LENGTH,
                                min_length=constants.MIN_STREAM_NAME_LENGTH, blank=True)  #
    tvg_logo = fields.CharField(default=constants.DEFAULT_STREAM_ICON_URL, max_length=constants.MAX_URL_LENGTH,
                                min_length=constants.MIN_URL_LENGTH, required=True)  #

    price = fields.FloatField(default=0.0, min_value=constants.MIN_PRICE, max_value=constants.MAX_PRICE, required=True)
    visible = fields.BooleanField(default=True, required=True)
    iarc = fields.IntegerField(default=21, min_value=0,
                               required=True)  # https://support.google.com/googleplay/answer/6209544

    view_count = fields.IntegerField(default=0)
    parts = fields.ListField(fields.ReferenceField('IStream'), default=[])
    output = fields.EmbeddedDocumentListField(OutputUrl, default=[])  #

    def add_part(self, stream):
        if stream:
            self.parts.append(stream)

    def remove_part(self, stream):
        if stream:
            self.parts.remove(stream)

    def get_groups(self) -> list:
        return self.group.split(';')

    def to_front_dict(self) -> dict:
        return {StreamFields.NAME_FIELD: self.name, StreamFields.ID_FIELD: self.get_id(),
                StreamFields.TYPE_FIELD: self.get_type(),
                StreamFields.ICON_FIELD: self.tvg_logo, StreamFields.PRICE_FIELD: self.price,
                StreamFields.VISIBLE_FIELD: self.visible,
                StreamFields.IARC_FIELD: self.iarc, StreamFields.VIEW_COUNT_FIELD: self.view_count,
                StreamFields.GROUP_FIELD: self.group}

    def get_type(self) -> constants.StreamType:
        raise NotImplementedError('subclasses must override get_type()!')

    @property
    def id(self) -> ObjectId:
        return self.pk

    def get_id(self) -> str:
        return str(self.pk)

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
                    self.tvg_id, self.tvg_name, self.tvg_logo, self.group, self.name, out.uri)

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
                    result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'.format(
                        self.tvg_id, self.tvg_name, self.tvg_logo, self.group, self.name, url)

        return result

    def generate_input_playlist(self, header=True) -> str:
        raise NotImplementedError('subclasses must override generate_input_playlist()!')

    def delete(self, *args, **kwargs):
        from pyfastocloud_models.subscriber.entry import Subscriber
        subscribers = Subscriber.objects.all()
        for subscriber in subscribers:
            subscriber.remove_official_stream(self)
            subscriber.remove_official_vod(self)
            subscriber.remove_official_catchup(self)
            subscriber.save()
        return super(IStream, self).delete(*args, **kwargs)


class ProxyStream(IStream):
    def __init__(self, *args, **kwargs):
        super(ProxyStream, self).__init__(*args, **kwargs)

    def get_type(self):
        return constants.StreamType.PROXY

    def generate_input_playlist(self, header=True) -> str:
        return self.generate_playlist(header)


class HardwareStream(IStream):
    log_level = fields.IntegerField(default=StreamLogLevel.LOG_LEVEL_INFO, required=True)

    input = fields.EmbeddedDocumentListField(InputUrl, default=[])
    have_video = fields.BooleanField(default=constants.DEFAULT_HAVE_VIDEO, required=True)
    have_audio = fields.BooleanField(default=constants.DEFAULT_HAVE_AUDIO, required=True)
    audio_select = fields.IntegerField(default=constants.INVALID_AUDIO_SELECT, required=True)
    loop = fields.BooleanField(default=constants.DEFAULT_LOOP, required=True)
    restart_attempts = fields.IntegerField(default=constants.DEFAULT_RESTART_ATTEMPTS, required=True)
    auto_exit_time = fields.IntegerField(default=constants.DEFAULT_AUTO_EXIT_TIME, required=True)
    extra_config_fields = fields.CharField(default='', blank=True)

    def __init__(self, *args, **kwargs):
        super(HardwareStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        raise NotImplementedError('subclasses must override get_type()!')

    def get_log_level(self):
        return self.log_level

    def get_audio_select(self):
        return self.audio_select

    def get_have_video(self):
        return self.have_video

    def get_have_audio(self):
        return self.have_audio

    def get_loop(self):
        return self.loop

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
                    self.tvg_id, self.tvg_name, self.tvg_logo, self.group, self.name, out.uri)

        return result


class RelayStream(HardwareStream):
    def __init__(self, *args, **kwargs):
        super(RelayStream, self).__init__(*args, **kwargs)

    video_parser = fields.CharField(default=constants.DEFAULT_VIDEO_PARSER, required=True)
    audio_parser = fields.CharField(default=constants.DEFAULT_AUDIO_PARSER, required=True)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.RELAY

    def get_video_parser(self):
        return self.video_parser

    def get_audio_parser(self):
        return self.audio_parser


class EncodeStream(HardwareStream):
    def __init__(self, *args, **kwargs):
        super(EncodeStream, self).__init__(*args, **kwargs)

    relay_video = fields.BooleanField(default=constants.DEFAULT_RELAY_VIDEO, required=True)
    relay_audio = fields.BooleanField(default=constants.DEFAULT_RELAY_AUDIO, required=True)
    deinterlace = fields.BooleanField(default=constants.DEFAULT_DEINTERLACE, required=True)
    frame_rate = fields.IntegerField(default=constants.INVALID_FRAME_RATE, required=True)
    volume = fields.FloatField(default=constants.DEFAULT_VOLUME, required=True)
    video_codec = fields.CharField(default=constants.DEFAULT_VIDEO_CODEC, required=True)
    audio_codec = fields.CharField(default=constants.DEFAULT_AUDIO_CODEC, required=True)
    audio_channels_count = fields.IntegerField(default=constants.INVALID_AUDIO_CHANNELS_COUNT, required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())
    video_bit_rate = fields.IntegerField(default=constants.INVALID_VIDEO_BIT_RATE, required=True)
    audio_bit_rate = fields.IntegerField(default=constants.INVALID_AUDIO_BIT_RATE, required=True)
    logo = fields.EmbeddedDocumentField(Logo, default=Logo())
    rsvg_logo = fields.EmbeddedDocumentField(RSVGLogo, default=RSVGLogo())
    aspect_ratio = fields.EmbeddedDocumentField(Rational, default=Rational())

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


class TimeshiftRecorderStream(RelayStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, default=[], blank=True)
    timeshift_chunk_duration = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_CHUNK_DURATION, required=True)
    timeshift_chunk_life_time = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_CHUNK_LIFE_TIME, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftRecorderStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_RECORDER

    def get_timeshift_chunk_duration(self):
        return self.timeshift_chunk_duration


class CatchupStream(TimeshiftRecorderStream):
    start = fields.DateTimeField(default=datetime.utcfromtimestamp(0))
    stop = fields.DateTimeField(default=datetime.utcfromtimestamp(0))

    def __init__(self, *args, **kwargs):
        super(CatchupStream, self).__init__(*args, **kwargs)
        self.timeshift_chunk_duration = constants.DEFAULT_CATCHUP_CHUNK_DURATION
        self.auto_exit_time = constants.DEFAULT_CATCHUP_EXIT_TIME

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.CATCHUP

    def to_front_dict(self) -> dict:
        base = super(CatchupStream, self).to_front_dict()
        start_utc = date_to_utc_msec(self.start)
        stop_utc = date_to_utc_msec(self.stop)
        base[CatchupsFields.START_RECORD_FIELD] = start_utc
        base[CatchupsFields.STOP_RECORD_FIELD] = stop_utc
        return base


class TimeshiftPlayerStream(RelayStream):
    timeshift_dir = fields.CharField(required=True)  # FIXME default
    timeshift_delay = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_DELAY, required=True)

    def __init__(self, *args, **kwargs):
        super(TimeshiftPlayerStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_PLAYER


class TestLifeStream(RelayStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, default=[], blank=True)

    def __init__(self, *args, **kwargs):
        super(TestLifeStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TEST_LIFE


class CodRelayStream(RelayStream):
    def __init__(self, *args, **kwargs):
        super(CodRelayStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.COD_RELAY


class CodEncodeStream(EncodeStream):
    def __init__(self, *args, **kwargs):
        super(CodEncodeStream, self).__init__(*args, **kwargs)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.COD_ENCODE


# VODS


class VodBasedStream(EmbeddedMongoModel):
    MAX_DATE = datetime(2100, 1, 1)
    MIN_DATE = datetime(1970, 1, 1)
    DEFAULT_COUNTRY = 'Unknown'

    def __init__(self, *args, **kwargs):
        super(VodBasedStream, self).__init__(*args, **kwargs)

    vod_type = fields.IntegerField(default=constants.VodType.VODS, required=True)
    description = fields.CharField(default=constants.DEFAULT_VOD_DESCRIPTION,
                                   min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                                   max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH,
                                   required=True)
    trailer_url = fields.CharField(default=constants.INVALID_TRAILER_URL, max_length=constants.MAX_URL_LENGTH,
                                   min_length=constants.MIN_URL_LENGTH, required=True)
    user_score = fields.FloatField(default=0, min_value=0, max_value=100, required=True)
    prime_date = fields.DateTimeField(default=MIN_DATE, required=True)
    country = fields.CharField(default=DEFAULT_COUNTRY, required=True)
    duration = fields.IntegerField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC, required=True)


class ProxyVodStream(ProxyStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(ProxyVodStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_PROXY


class VodRelayStream(RelayStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodRelayStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_RELAY


class VodEncodeStream(EncodeStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodEncodeStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_ENCODE


class EventStream(VodEncodeStream):
    def get_type(self) -> constants.StreamType:
        return constants.StreamType.EVENT


# if remove catchup also clean parts
CatchupStream.register_delete_rule(IStream, 'parts', fields.ReferenceField.PULL)
