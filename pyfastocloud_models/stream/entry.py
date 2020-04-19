import os
from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse

from bson.objectid import ObjectId
from pymodm import MongoModel, fields, EmbeddedMongoModel

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Rational, Size, Logo, RSVGLogo, InputUrl, OutputUrl, Maker
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


class IStream(MongoModel, Maker):
    NAME_FIELD = 'name'
    ID_FIELD = 'id'
    PRICE_FIELD = 'price'
    GROUP_FIELD = 'group'
    VISIBLE_FIELD = 'visible'
    IARC_FIELD = 'iarc'
    VIEW_COUNT_FIELD = 'view_count'
    TYPE_FIELD = 'type'
    CREATED_DATE_FIELD = 'created_date'
    OUTPUT_FIELD = 'output'
    ICON_FIELD = 'icon'
    TVG_ID_FIELD = 'tvg_id'
    TVG_NAME_FIELD = 'tvg_name'

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

    name = fields.CharField(min_length=constants.MIN_STREAM_NAME_LENGTH, max_length=constants.MAX_STREAM_NAME_LENGTH,
                            required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)
    group = fields.CharField(min_length=constants.MIN_STREAM_GROUP_TITLE_LENGTH,
                             max_length=constants.MAX_STREAM_GROUP_TITLE_LENGTH, required=False)

    tvg_id = fields.CharField(min_length=constants.MIN_STREAM_TVG_ID_LENGTH,
                              max_length=constants.MAX_STREAM_TVG_ID_LENGTH, required=False)
    tvg_name = fields.CharField(min_length=constants.MIN_STREAM_TVG_NAME_LENGTH,
                                max_length=constants.MAX_STREAM_TVG_NAME_LENGTH, required=False)  # for inner use
    tvg_logo = fields.CharField(default=constants.DEFAULT_STREAM_ICON_URL, max_length=constants.MAX_URI_LENGTH,
                                min_length=constants.MIN_URI_LENGTH, required=True)

    price = fields.FloatField(default=constants.DEFAULT_PRICE, min_value=constants.MIN_PRICE,
                              max_value=constants.MAX_PRICE, required=True)
    visible = fields.BooleanField(default=True, required=True)
    iarc = fields.IntegerField(default=constants.DEFAULT_IARC, min_value=constants.MIN_IARC,
                               max_value=constants.MAX_IARC,
                               required=True)  # https://support.google.com/googleplay/answer/6209544

    view_count = fields.IntegerField(default=0, required=True)
    parts = fields.ListField(fields.ReferenceField('IStream'), default=[])
    output = fields.EmbeddedDocumentListField(OutputUrl, default=[], required=True)  #

    def to_front_dict(self) -> dict:
        output = []
        for out in self.output:
            output.append(out.to_front_dict())

        return {IStream.ID_FIELD: self.get_id(), IStream.NAME_FIELD: self.name,
                IStream.CREATED_DATE_FIELD: self.created_date_utc_msec(), IStream.GROUP_FIELD: self.group,
                IStream.TYPE_FIELD: self.get_type(), IStream.TVG_ID_FIELD: self.tvg_id,
                IStream.TVG_NAME_FIELD: self.tvg_name, IStream.ICON_FIELD: self.tvg_logo,
                IStream.PRICE_FIELD: self.price, IStream.VISIBLE_FIELD: self.visible, IStream.IARC_FIELD: self.iarc,
                IStream.VIEW_COUNT_FIELD: self.view_count, IStream.OUTPUT_FIELD: output}

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def add_part(self, stream):
        if stream:
            self.parts.append(stream)

    def remove_part(self, stream):
        if stream:
            self.parts.remove(stream)

    def get_groups(self) -> list:
        return self.group.split(';')

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
                    result += '#EXTINF:-1 tvg-id="{0}" tvg-name="{1}" tvg-logo="{2}" group-title="{3}",{4}\n{5}\n'. \
                        format(self.tvg_id, self.tvg_name, self.tvg_logo, self.group, self.name, url)

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

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, name = self.check_required_type(IStream.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, created_date_msec = self.check_optional_type(IStream.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, group = self.check_optional_type(IStream.GROUP_FIELD, str, json)
        if res:  # optional field
            self.group = group

        res, tvg_id = self.check_optional_type(IStream.TVG_ID_FIELD, str, json)
        if res:  # optional field
            self.tvg_id = tvg_id

        res, tvg_name = self.check_optional_type(IStream.TVG_NAME_FIELD, str, json)
        if res:  # optional field
            self.tvg_name = tvg_name

        res, icon = self.check_optional_type(IStream.ICON_FIELD, str, json)
        if res:  # optional field
            self.tvg_logo = icon

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
        elif stream_type == constants.StreamType.VOD_RELAY:
            return VodRelayStream.make_entry(json)
        elif stream_type == constants.StreamType.VOD_ENCODE:
            return VodEncodeStream.make_entry(json)
        elif stream_type == constants.StreamType.COD_RELAY:
            return CodRelayStream.make_entry(json)
        elif stream_type == constants.StreamType.COD_ENCODE:
            return CodEncodeStream.make_entry(json)
        elif stream_type == constants.StreamType.CATCHUP:
            return CatchupStream.make_entry(json)
        else:
            return TestLifeStream.make_entry(json)


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
    LOOP_FIELD = 'loop'
    RESTART_ATTEMPTS_FIELD = 'restart_attempts'
    AUTO_EXIT_TIME_FIELD = 'auto_exit_time'
    EXTRA_CONFIG_FIELD = 'extra_config'

    log_level = fields.IntegerField(default=StreamLogLevel.LOG_LEVEL_INFO, min_value=StreamLogLevel.LOG_LEVEL_EMERG,
                                    max_value=StreamLogLevel.LOG_LEVEL_DEBUG, required=True)
    restart_attempts = fields.IntegerField(default=constants.DEFAULT_RESTART_ATTEMPTS,
                                           min_value=constants.MIN_RESTART_ATTEMPTS,
                                           max_value=constants.MAX_RESTART_ATTEMPTS, required=True)
    auto_exit_time = fields.IntegerField(default=constants.DEFAULT_AUTO_EXIT_TIME,
                                         min_value=constants.MIN_AUTO_EXIT_TIME, max_value=constants.MAX_AUTO_EXIT_TIME,
                                         required=True)
    audio_select = fields.IntegerField(min_value=constants.MIN_AUDIO_SELECT,
                                       max_value=constants.MAX_AUDIO_SELECT, required=False)
    have_video = fields.BooleanField(default=constants.DEFAULT_HAVE_VIDEO, required=True)
    have_audio = fields.BooleanField(default=constants.DEFAULT_HAVE_AUDIO, required=True)
    loop = fields.BooleanField(default=constants.DEFAULT_LOOP, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, default=[], required=True)
    extra_config_fields = fields.CharField(default='{}', required=True)

    def __init__(self, *args, **kwargs):
        super(HardwareStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        IStream.update_entry(self, json)

        res, log_level = IStream.check_optional_type(HardwareStream.LOG_LEVEL_FIELD, int, json)
        if res:  # optional field
            self.log_level = log_level

        res, inp = IStream.check_required_type(HardwareStream.INPUT_FIELD, list, json)
        if res:  # optional field
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

        res, audio_select = IStream.check_optional_type(HardwareStream.AUDIO_SELECT_FIELD, int, json)
        if res:  # optional field
            self.audio_select = audio_select

        res, loop = IStream.check_optional_type(HardwareStream.LOOP_FIELD, bool, json)
        if res:  # optional field
            self.loop = loop

        res, restart = IStream.check_optional_type(HardwareStream.RESTART_ATTEMPTS_FIELD, int, json)
        if res:  # optional field
            self.restart_attempts = restart

        res, auto_exit = IStream.check_optional_type(HardwareStream.AUTO_EXIT_TIME_FIELD, int, json)
        if res:  # optional field
            self.auto_exit_time = auto_exit

        res, extra = IStream.check_optional_type(HardwareStream.EXTRA_CONFIG_FIELD, str, json)
        if res:  # optional field
            self.extra_config_fields = extra

    def to_front_dict(self) -> dict:
        base = super(HardwareStream, self).to_front_dict()
        input = []
        for inp in self.input:
            input.append(inp.to_front_dict())
        base[HardwareStream.LOG_LEVEL_FIELD] = self.log_level
        base[HardwareStream.INPUT_FIELD] = input
        base[HardwareStream.HAVE_VIDEO_FIELD] = self.have_video
        base[HardwareStream.HAVE_AUDIO_FIELD] = self.have_audio
        base[HardwareStream.AUDIO_SELECT_FIELD] = self.audio_select
        base[HardwareStream.LOOP_FIELD] = self.loop
        base[HardwareStream.RESTART_ATTEMPTS_FIELD] = self.restart_attempts
        base[HardwareStream.AUTO_EXIT_TIME_FIELD] = self.auto_exit_time
        base[HardwareStream.EXTRA_CONFIG_FIELD] = self.extra_config_fields
        return base

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
    VIDEO_PARSER_FIELD = 'video_parser'
    AUDIO_PARSER_FIELD = 'audio_parser'

    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, required=True)

    video_parser = fields.CharField(default=constants.DEFAULT_VIDEO_PARSER, required=True)
    audio_parser = fields.CharField(default=constants.DEFAULT_AUDIO_PARSER, required=True)

    def __init__(self, *args, **kwargs):
        super(RelayStream, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        HardwareStream.update_entry(self, json)

        res, video = IStream.check_optional_type(RelayStream.VIDEO_PARSER_FIELD, str, json)
        if res:  # optional field
            self.video_parser = video

        res, audio = IStream.check_optional_type(RelayStream.AUDIO_PARSER_FIELD, str, json)
        if res:  # optional field
            self.audio_parser = audio

    def to_front_dict(self) -> dict:
        base = super(RelayStream, self).to_front_dict()
        base[RelayStream.VIDEO_PARSER_FIELD] = self.video_parser
        base[RelayStream.AUDIO_PARSER_FIELD] = self.audio_parser
        return base

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.RELAY

    def get_video_parser(self):
        return self.video_parser

    def get_audio_parser(self):
        return self.audio_parser


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
    VIDEO_BITRATE_FIELD = 'video_bit_rate'
    AUDIO_BITRATE_FIELD = 'audio_bit_rate'
    LOGO_FIELD = 'logo'
    RSVG_LOGO_FIELD = 'rsvg_logo'
    ASPECT_RATIO_FIELD = 'aspect_ratio'

    output = fields.EmbeddedDocumentListField(OutputUrl, required=True)
    input = fields.EmbeddedDocumentListField(InputUrl, required=True)

    relay_video = fields.BooleanField(default=constants.DEFAULT_RELAY_VIDEO, required=True)
    relay_audio = fields.BooleanField(default=constants.DEFAULT_RELAY_AUDIO, required=True)
    deinterlace = fields.BooleanField(default=constants.DEFAULT_DEINTERLACE, required=True)
    frame_rate = fields.IntegerField(min_value=constants.MIN_FRAME_RATE,
                                     max_value=constants.MAX_FRAME_RATE, required=False)
    volume = fields.FloatField(default=constants.DEFAULT_VOLUME, min_value=constants.MIN_VOLUME,
                               max_value=constants.MAX_VOLUME, required=True)
    video_codec = fields.CharField(default=constants.DEFAULT_VIDEO_CODEC, required=True)
    audio_codec = fields.CharField(default=constants.DEFAULT_AUDIO_CODEC, required=True)
    audio_channels_count = fields.IntegerField(min_value=constants.MIN_AUDIO_CHANNELS_COUNT,
                                               max_value=constants.MAX_AUDIO_CHANNELS_COUNT, required=False)
    size = fields.EmbeddedDocumentField(Size, required=False)
    video_bit_rate = fields.IntegerField(required=False)
    audio_bit_rate = fields.IntegerField(required=False)
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

        res, volume = IStream.check_optional_type(EncodeStream.VOLUME_FIELD, float, json)
        if res:  # optional field
            self.volume = volume

        res, video_codec = IStream.check_optional_type(EncodeStream.VIDEO_CODEC_FIELD, str, json)
        if res:  # optional field
            self.video_codec = video_codec

        res, audio_codec = IStream.check_optional_type(EncodeStream.AUDIO_CODEC_FIELD, str, json)
        if res:  # optional field
            self.audio_codec = audio_codec

        res, size = IStream.check_optional_type(EncodeStream.SIZE_FIELD, dict, json)
        if res:  # optional field
            self.size = Size.make_entry(size)

        res, video_bit_rate = IStream.check_optional_type(EncodeStream.VIDEO_BITRATE_FIELD, int, json)
        if res:  # optional field
            self.video_bit_rate = video_bit_rate

        res, audio_bit_rate = IStream.check_optional_type(EncodeStream.AUDIO_BITRATE_FIELD, int, json)
        if res:  # optional field
            self.audio_bit_rate = audio_bit_rate

        res, logo = IStream.check_optional_type(EncodeStream.LOGO_FIELD, dict, json)
        if res:  # optional field
            self.logo = Logo.make_entry(logo)

        res, rlogo = IStream.check_optional_type(EncodeStream.RSVG_LOGO_FIELD, dict, json)
        if res:  # optional field
            self.rsvg_logo = RSVGLogo.make_entry(rlogo)

        res, aspect = IStream.check_optional_type(EncodeStream.ASPECT_RATIO_FIELD, dict, json)
        if res:  # optional field
            self.aspect_ratio = Rational.make_entry(aspect)

    def to_front_dict(self) -> dict:
        base = super(EncodeStream, self).to_front_dict()
        base[EncodeStream.RELAY_AUDIO_FIELD] = self.relay_audio
        base[EncodeStream.RELAY_VIDEO_FIELD] = self.relay_video
        base[EncodeStream.DEINTERLACE_FIELD] = self.deinterlace
        base[EncodeStream.FRAME_RATE_FIELD] = self.frame_rate
        base[EncodeStream.VOLUME_FIELD] = self.volume
        base[EncodeStream.VIDEO_CODEC_FIELD] = self.video_codec
        base[EncodeStream.AUDIO_CODEC_FIELD] = self.audio_codec
        base[EncodeStream.AUDIO_CHANNELS_COUNT_FIELD] = self.audio_channels_count
        base[EncodeStream.SIZE_FIELD] = self.size.to_front_dict()
        base[EncodeStream.VIDEO_BITRATE_FIELD] = self.video_bit_rate
        base[EncodeStream.AUDIO_BITRATE_FIELD] = self.audio_bit_rate
        base[EncodeStream.LOGO_FIELD] = self.logo.to_front_dict()
        base[EncodeStream.RSVG_LOGO_FIELD] = self.rsvg_logo.to_front_dict()
        base[EncodeStream.ASPECT_RATIO_FIELD] = self.aspect_ratio.to_front_dict()
        return base

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
    TIMESHIFT_CHUNK_DURATION = 'timeshift_chunk_duration'
    TIMESHIFT_CHUNK_LIFE_TIME = 'timeshift_chunk_life_time'

    output = fields.EmbeddedDocumentListField(OutputUrl, default=[], required=True, blank=True)  #

    timeshift_chunk_duration = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_CHUNK_DURATION,
                                                   min_value=constants.MIN_TIMESHIFT_CHUNK_DURATION, required=True)
    timeshift_chunk_life_time = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_CHUNK_LIFE_TIME,
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

    def to_front_dict(self) -> dict:
        base = super(TimeshiftRecorderStream, self).to_front_dict()
        base[TimeshiftRecorderStream.TIMESHIFT_CHUNK_DURATION] = self.timeshift_chunk_duration
        base[TimeshiftRecorderStream.TIMESHIFT_CHUNK_LIFE_TIME] = self.timeshift_chunk_life_time
        return base

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_RECORDER

    def get_timeshift_chunk_duration(self):
        return self.timeshift_chunk_duration


class CatchupStream(TimeshiftRecorderStream):
    START_RECORD_FIELD = 'start'
    STOP_RECORD_FIELD = 'stop'

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
        base = super(CatchupStream, self).to_front_dict()
        base[CatchupStream.START_RECORD_FIELD] = self.start_utc_msec()
        base[CatchupStream.STOP_RECORD_FIELD] = self.stop_utc_msec()
        return base


class TimeshiftPlayerStream(RelayStream):
    TIMESHIFT_DIR_FIELD = 'timeshift_dir'
    TIMESHIFT_DELAY = 'timeshift_delay'

    input = fields.EmbeddedDocumentListField(InputUrl, default=[], required=True, blank=True)  #

    timeshift_dir = fields.CharField(required=True)  # FIXME default
    timeshift_delay = fields.IntegerField(default=constants.DEFAULT_TIMESHIFT_DELAY,
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

    def to_front_dict(self) -> dict:
        base = super(TimeshiftPlayerStream, self).to_front_dict()
        base[TimeshiftPlayerStream.TIMESHIFT_DIR_FIELD] = self.timeshift_dir
        base[TimeshiftPlayerStream.TIMESHIFT_DELAY] = self.timeshift_delay
        return base

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.TIMESHIFT_PLAYER


class TestLifeStream(RelayStream):
    output = fields.EmbeddedDocumentListField(OutputUrl, default=[], required=True, blank=True)  #

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
    DESCRIPTION_FIELD = 'description'  #
    VOD_TYPE_FIELD = 'vod_type'
    TRAILER_URL_FIELD = 'trailer_url'
    USER_SCORE_FIELD = 'user_score'
    PRIME_DATE_FIELD = 'date'
    COUNTRY_FIELD = 'country'
    DURATION_FIELD = 'duration'

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
    trailer_url = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH,
                                   required=False)
    user_score = fields.FloatField(default=0, min_value=0, max_value=100, required=True)
    prime_date = fields.DateTimeField(default=MIN_DATE, required=True)
    country = fields.CharField(default=DEFAULT_COUNTRY, required=True)
    duration = fields.IntegerField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC, required=True)

    def prime_date_utc_msec(self):
        return date_to_utc_msec(self.prime_date)

    def update_entry(self, json: dict):
        if not json:
            raise ValueError('Invalid input')

        res, vod_type = Maker.check_required_type(VodBasedStream.VOD_TYPE_FIELD, int, json)
        if res:
            self.vod_type = vod_type

        res, description = Maker.check_optional_type(VodBasedStream.DESCRIPTION_FIELD, str, json)
        if res:
            self.description = description

        res, trailer = Maker.check_optional_type(VodBasedStream.TRAILER_URL_FIELD, str, json)
        if res:
            self.trailer_url = trailer

        res, score = Maker.check_optional_type(VodBasedStream.USER_SCORE_FIELD, float, json)
        if res:
            self.user_score = score

        res, prime_date = self.check_required_type(VodBasedStream.PRIME_DATE_FIELD, int, json)
        if res:
            self.prime_date = datetime.utcfromtimestamp(prime_date / 1000)

        res, country = Maker.check_optional_type(VodBasedStream.COUNTRY_FIELD, str, json)
        if res:
            self.country = country

        res, duration = Maker.check_optional_type(VodBasedStream.DURATION_FIELD, int, json)
        if res:
            self.duration = duration

    def to_front_dict(self):
        return {VodBasedStream.DESCRIPTION_FIELD: self.description,
                VodBasedStream.TRAILER_URL_FIELD: self.trailer_url,
                VodBasedStream.USER_SCORE_FIELD: self.user_score,
                VodBasedStream.PRIME_DATE_FIELD: self.prime_date_utc_msec(),
                VodBasedStream.COUNTRY_FIELD: self.country,
                VodBasedStream.DURATION_FIELD: self.duration}


class ProxyVodStream(ProxyStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(ProxyVodStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def update_entry(self, json: dict):
        ProxyStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_PROXY

    def to_front_dict(self) -> dict:
        front = ProxyStream.to_front_dict(self)
        base = VodBasedStream.to_front_dict(self)
        return {**front, **base}


class VodRelayStream(RelayStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodRelayStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def update_entry(self, json: dict):
        RelayStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_RELAY

    def to_front_dict(self) -> dict:
        front = RelayStream.to_front_dict(self)
        base = VodBasedStream.to_front_dict(self)
        return {**front, **base}


class VodEncodeStream(EncodeStream, VodBasedStream):
    def __init__(self, *args, **kwargs):
        super(VodEncodeStream, self).__init__(*args, **kwargs)
        self.tvg_logo = constants.DEFAULT_STREAM_PREVIEW_ICON_URL

    def update_entry(self, json: dict):
        EncodeStream.update_entry(self, json)
        VodBasedStream.update_entry(self, json)

    def get_type(self) -> constants.StreamType:
        return constants.StreamType.VOD_ENCODE

    def to_front_dict(self) -> dict:
        front = ProxyStream.to_front_dict(self)
        base = VodBasedStream.to_front_dict(self)
        return {**front, **base}


class EventStream(VodEncodeStream):
    def get_type(self) -> constants.StreamType:
        return constants.StreamType.EVENT


# if remove catchup also clean parts
CatchupStream.register_delete_rule(IStream, 'parts', fields.ReferenceField.PULL)
