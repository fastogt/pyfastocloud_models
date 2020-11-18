from datetime import datetime
from enum import IntEnum
from hashlib import md5

from bson.objectid import ObjectId
from pyfastogt.utils import is_valid_email
from pymodm import MongoModel, fields, EmbeddedMongoModel, errors
from pymongo.operations import IndexModel

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Maker
from pyfastocloud_models.content_request.entry import ContentRequest
from pyfastocloud_models.series.entry import Serial
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.stream.entry import IStream
from pyfastocloud_models.utils.utils import date_to_utc_msec


def is_vod_stream(stream: IStream):
    if not stream:
        return False
    if not stream.visible:
        return False
    stream_type = stream.get_type()
    return stream_type == constants.StreamType.VOD_PROXY or stream_type == constants.StreamType.VOD_RELAY or \
           stream_type == constants.StreamType.VOD_ENCODE


def is_live_stream(stream: IStream):
    if not stream:
        return False
    if not stream.visible:
        return False
    stream_type = stream.get_type()
    return stream_type == constants.StreamType.PROXY or stream_type == constants.StreamType.RELAY or \
           stream_type == constants.StreamType.ENCODE or stream_type == constants.StreamType.TIMESHIFT_PLAYER or \
           stream_type == constants.StreamType.COD_RELAY or stream_type == constants.StreamType.COD_ENCODE or \
           stream_type == constants.StreamType.EVENT


def is_catchup(stream: IStream):
    if not stream:
        return False
    if not stream.visible:
        return False
    stream_type = stream.get_type()
    return stream_type == constants.StreamType.CATCHUP


def for_subscribers_stream(stream: IStream):
    if not stream:
        return False
    if not stream.visible:
        return False
    return is_vod_stream(stream) or is_live_stream(stream) or is_catchup(stream)


def filtered_streams_in_server(server: ServiceSettings, cb) -> [IStream]:
    if not server:
        return []

    streams = []
    for stream in server.streams:
        if cb(stream):
            streams.append(stream)

    return streams


class Device(EmbeddedMongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    STATUS_FIELD = 'status'
    CREATED_DATE_FIELD = 'created_date'

    DEFAULT_DEVICE_NAME = 'Device'
    MIN_DEVICE_NAME_LENGTH = 1
    MAX_DEVICE_NAME_LENGTH = 32

    class Status(IntEnum):
        NOT_ACTIVE = 0
        ACTIVE = 1
        BANNED = 2

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    id = fields.ObjectIdField(required=True, default=ObjectId, primary_key=True)
    created_date = fields.DateTimeField(default=datetime.now)
    status = fields.IntegerField(default=Status.NOT_ACTIVE)
    name = fields.CharField(default=DEFAULT_DEVICE_NAME, min_length=MIN_DEVICE_NAME_LENGTH,
                            max_length=MAX_DEVICE_NAME_LENGTH, required=True)

    def get_id(self) -> str:
        return str(self.id)

    def to_front_dict(self) -> dict:
        return {Device.ID_FIELD: self.get_id(), Device.NAME_FIELD: self.name, Device.STATUS_FIELD: self.status,
                Device.CREATED_DATE_FIELD: self.created_date_utc_msec()}

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    @classmethod
    def make_entry(cls, json: dict) -> 'Device':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, name = Device.check_required_type(Device.NAME_FIELD, str, json)
        if res:
            self.name = name

        res, created_date_msec = self.check_optional_type(Device.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, status = self.check_required_type(Device.STATUS_FIELD, int, json)
        if res:
            self.status = status
        try:
            self.full_clean()
        except errors.ValidationError as err:
            raise ValueError(err.message)


class UserStream(EmbeddedMongoModel):
    FAVORITE_FIELD = 'favorite'
    PRIVATE_FIELD = 'private'
    RECENT_FIELD = 'recent'
    LOCKED_FIELD = 'locked'
    INTERRUPTION_TIME_FIELD = 'interruption_time'

    sid = fields.ReferenceField(IStream, required=True)
    favorite = fields.BooleanField(default=False)
    private = fields.BooleanField(default=False)
    locked = fields.BooleanField(default=False)
    recent = fields.DateTimeField(default=datetime.utcfromtimestamp(0))
    interruption_time = fields.IntegerField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC,
                                            required=True)

    def __init__(self, *args, **kwargs):
        super(UserStream, self).__init__(*args, **kwargs)

    @classmethod
    def make_from_stream(cls, stream: IStream) -> 'UserStream':
        locked = stream.price > 0
        cl = cls(sid=stream.id, locked=locked)
        return cl

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def to_front_dict(self):
        res = self.sid.to_front_dict()
        res[UserStream.FAVORITE_FIELD] = self.favorite
        res[UserStream.PRIVATE_FIELD] = self.private
        res[UserStream.LOCKED_FIELD] = self.locked
        res[UserStream.RECENT_FIELD] = date_to_utc_msec(self.recent)
        res[UserStream.INTERRUPTION_TIME_FIELD] = self.interruption_time
        return res


class Subscriber(MongoModel, Maker):
    ID_FIELD = 'id'
    EMAIL_FIELD = 'email'
    FIRST_NAME_FIELD = 'first_name'
    LAST_NAME_FIELD = 'last_name'
    PASSWORD_FIELD = 'password'
    CREATED_DATE_FIELD = 'created_date'
    EXP_DATE_FIELD = 'exp_date'
    STATUS_FIELD = 'status'
    MAX_DEVICE_COUNT_FIELD = 'max_devices_count'
    LANGUAGE_FIELD = 'language'
    COUNTRY_FIELD = 'country'
    SERVERS_FIELD = 'servers'
    DEVICES_COUNT_FIELD = 'devices_count'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            sub = Subscriber.objects.get({'_id': sid})
        except Subscriber.DoesNotExist:
            return None
        else:
            return sub

    @staticmethod
    def get_by_email(email: str):
        try:
            sub = Subscriber.objects.get({'email': email})
        except Subscriber.DoesNotExist:
            return None
        else:
            return sub

    class Meta:
        collection_name = 'subscribers'
        allow_inheritance = False
        indexes = [IndexModel([('email', 1)], unique=True)]

    MAX_DATE = datetime(2100, 1, 1)

    class Status(IntEnum):
        NOT_ACTIVE = 0
        ACTIVE = 1
        DELETED = 2

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    SUBSCRIBER_HASH_LENGTH = 32

    email = fields.EmailField(required=True)
    first_name = fields.CharField(max_length=64, required=True)
    last_name = fields.CharField(max_length=64, required=True)
    password = fields.CharField(min_length=SUBSCRIBER_HASH_LENGTH, max_length=SUBSCRIBER_HASH_LENGTH, required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)  #
    exp_date = fields.DateTimeField(default=MAX_DATE, required=True)
    status = fields.IntegerField(default=Status.NOT_ACTIVE, required=True)  #
    country = fields.CharField(min_length=2, max_length=3, required=True)
    language = fields.CharField(default=constants.DEFAULT_LOCALE, required=True)

    servers = fields.ListField(fields.ReferenceField(ServiceSettings, on_delete=fields.ReferenceField.PULL), blank=True)
    devices = fields.EmbeddedModelListField(Device, blank=True, required=False)
    max_devices_count = fields.IntegerField(default=constants.DEFAULT_DEVICES_COUNT, required=False)
    # content
    streams = fields.EmbeddedModelListField(UserStream, blank=True, required=False)
    vods = fields.EmbeddedModelListField(UserStream, blank=True, required=False)
    catchups = fields.EmbeddedModelListField(UserStream, blank=True, required=False)
    series = fields.ListField(fields.ReferenceField(Serial, on_delete=fields.ReferenceField.PULL), blank=True)
    requests = fields.ListField(fields.ReferenceField(ContentRequest, on_delete=fields.ReferenceField.PULL), blank=True)

    def __init__(self, *args, **kwargs):
        super(Subscriber, self).__init__(*args, **kwargs)

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def expiration_date_utc_msec(self):
        return date_to_utc_msec(self.exp_date)

    def find_server_by_stream_id(self, sid: ObjectId) -> ServiceSettings:
        if not sid:
            return None

        for server in self.servers:
            stream = server.find_stream_by_id(sid)
            if stream:
                return server

        return None

    def find_server_by_id(self, sid: ObjectId) -> ServiceSettings:
        if not sid:
            return None

        for server in self.servers:
            if server.id == sid:
                return server

        return None

    def add_server(self, server: ServiceSettings):
        if not server:
            return

        if server not in self.servers:
            self.servers.append(server)

    def remove_server(self, server: ServiceSettings):
        if not server:
            return

        try:
            self.servers.remove(server)
        except ValueError:
            pass

    def add_device(self, device: Device):
        if device:
            if len(self.devices) < self.max_devices_count:
                self.devices.append(device)

    def remove_device(self, did: ObjectId):
        for dev in list(self.devices):
            if dev.id == did:
                self.devices.remove(dev)

    def find_device(self, did: ObjectId) -> Device:
        for dev in self.devices:
            if dev.id == did:
                return dev

        return None

    def generate_playlist(self, did: str, lb_server_host_and_port: str) -> str:
        result = '#EXTM3U\n'
        sid = str(self.id)
        for stream in self.streams:
            if stream.locked:  # FIXME should play stab video
                continue

            if stream.private:
                result += stream.sid.generate_playlist(False)
            else:
                result += stream.sid.generate_device_playlist(sid, self.password, did, lb_server_host_and_port, False)

        for vod in self.vods:
            if vod.locked:  # FIXME should play stab video
                continue

            if vod.private:
                result += vod.sid.generate_playlist(False)
            else:
                result += vod.sid.generate_device_playlist(sid, self.password, did, lb_server_host_and_port, False)

        for cat in self.catchups:
            if cat.locked:  # FIXME should play stab video
                continue

            if cat.private:
                result += cat.sid.generate_playlist(False)
            else:
                result += cat.sid.generate_device_playlist(sid, self.password, did, lb_server_host_and_port, False)

        return result

    def generate_playlist_dict(self, did: str, lb_server_host_and_port: str) -> [dict]:
        result = []
        sid = str(self.id)
        for stream in self.streams:
            if stream.locked:  # FIXME should play stab video
                continue

            if stream.private:
                result += stream.sid.generate_playlist_dict()
            else:
                result += stream.sid.generate_device_playlist_dict(sid, self.password, did, lb_server_host_and_port)

        for vod in self.vods:
            if vod.locked:  # FIXME should play stab video
                continue

            if vod.private:
                result += vod.sid.generate_playlist_dict()
            else:
                result += vod.sid.generate_device_playlist_dict(sid, self.password, did, lb_server_host_and_port)

        for cat in self.catchups:
            if cat.locked:  # FIXME should play stab video
                continue

            if cat.private:
                result += cat.sid.generate_playlist_dict()
            else:
                result += cat.sid.generate_device_playlist_dict(sid, self.password, did, lb_server_host_and_port)

        return result

    def all_streams(self):
        return self.streams

    # official streams
    def add_official_stream_by_id(self, oid: ObjectId):
        stream = IStream.get_by_id(oid)
        user_stream = UserStream.make_from_stream(stream)
        self.add_official_stream(user_stream)

    def add_official_stream(self, user_stream: UserStream):
        if not user_stream:
            return

        for stream in self.streams:
            if not stream.private and stream.sid == user_stream.sid:
                return

        self.streams.append(user_stream)

    def remove_official_stream(self, ostream: IStream):
        if not ostream:
            return

        for stream in self.streams:
            if not stream.private and stream.sid == ostream:
                self.streams.remove(stream)

    def remove_official_stream_by_id(self, sid: ObjectId):
        original_stream = IStream.get_by_id(sid)
        self.remove_official_stream(original_stream)

    # official vods
    def add_official_vod_by_id(self, oid: ObjectId):
        stream = IStream.get_by_id(oid)
        user_stream = UserStream.make_from_stream(stream)
        self.add_official_vod(user_stream)

    def add_official_vod(self, user_stream: UserStream):
        if not user_stream:
            return

        for vod in self.vods:
            if not vod.private and vod.sid == user_stream.sid:
                return

        self.vods.append(user_stream)

    def remove_official_vod(self, ostream: IStream):
        if not ostream:
            return

        for vod in self.vods:
            if not vod.private and vod.sid == ostream:
                self.vods.remove(vod)

    def remove_official_vod_by_id(self, sid: ObjectId):
        original_stream = IStream.get_by_id(sid)
        self.remove_official_vod(original_stream)

    # official series
    def add_official_serial_by_id(self, sid: ObjectId):
        serial = Serial.get_by_id(sid)
        self.add_official_serial(serial)

    def add_official_serial(self, serial: Serial):
        if not serial:
            return

        if serial in self.series:
            return

        self.series.append(serial)

    def remove_official_serial(self, serial: Serial):
        if not serial:
            return

        try:
            self.series.remove(serial)
        except ValueError:
            pass

    def remove_official_serial_by_id(self, sid: ObjectId):
        serial = Serial.get_by_id(sid)
        self.remove_official_serial(serial)

    # official catchups
    def add_official_catchup_by_id(self, oid: ObjectId):
        stream = IStream.get_by_id(oid)
        user_stream = UserStream.make_from_stream(stream)
        self.add_official_catchup(user_stream)

    def add_official_catchup(self, user_stream: UserStream):
        if not user_stream:
            return

        for catchup in self.catchups:
            if not catchup.private and catchup.sid == user_stream.sid:
                return

        self.catchups.append(user_stream)

    def remove_official_catchup(self, ostream: IStream):
        if not ostream:
            return

        for catchup in self.catchups:
            if not catchup.private and catchup.sid == ostream:
                self.catchups.remove(catchup)

    def remove_official_catchup_by_id(self, sid: ObjectId):
        original_stream = IStream.get_by_id(sid)
        self.remove_official_catchup(original_stream)

    # own
    def add_own_stream(self, user_stream: UserStream):
        for stream in self.streams:
            if stream.private and stream.sid == user_stream:
                return

        user_stream.private = True
        self.streams.append(user_stream)

    def remove_own_stream_by_id(self, sid: ObjectId):
        istream = IStream.get_by_id(sid)
        if istream:
            for stream in self.streams:
                if stream.private and stream.sid == sid:
                    self.stream.remove(stream)
            istream.delete()

    def remove_all_own_streams(self):
        for stream in self.streams:
            if stream.private:
                self.streams.remove(stream)

    def add_own_vod(self, user_stream: UserStream):
        for vod in self.vod:
            if vod.private and vod.sid == user_stream.sid:
                return

        user_stream.private = True
        self.vod.append(user_stream)

    def remove_own_vod_by_id(self, sid: ObjectId):
        vod = IStream.get_by_id(sid)
        if vod:
            for vod in self.vod:
                if vod.private and vod.sid == sid:
                    self.vod.remove(vod)
            vod.delete()

    def remove_all_own_vods(self):
        for stream in self.vods:
            if stream.private:
                self.vods.remove(stream)

    # available
    def official_streams(self) -> [UserStream]:
        streams = []
        for stream in self.streams:
            if not stream.private:
                streams.append(stream)

        return streams

    def official_vods(self) -> [UserStream]:
        streams = []
        for stream in self.vods:
            if not stream.private:
                streams.append(stream)

        return streams

    def official_series(self) -> [Serial]:
        return self.series

    def official_catchups(self) -> [UserStream]:
        streams = []
        for stream in self.catchups:
            if not stream.private:
                streams.append(stream)

        return streams

    def own_streams(self):
        streams = []
        for stream in self.streams:
            if stream.private:
                streams.append(stream)

        return streams

    def own_vods(self):
        vods = []
        for vod in self.vods:
            if vod.private:
                vods.append(vod)

        return vods

    def all_available_servers(self):
        return self.servers

    def all_available_official_streams(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            streams += filtered_streams_in_server(serv, is_live_stream)

        return streams

    def all_available_official_vods(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            streams += filtered_streams_in_server(serv, is_vod_stream)

        return streams

    def all_available_official_catchups(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            streams += filtered_streams_in_server(serv, is_catchup)

        return streams

    def all_available_official_series(self) -> [Serial]:
        series = []
        for serv in self.servers:
            for serial in serv.series:
                if serial.visible:
                    series.append(serial)

        return series

    def find_user_stream_by_id(self, sid: ObjectId) -> UserStream:
        for _stream in self.streams:
            if _stream.sid.id == sid:
                return _stream

        return None

    def find_user_vods_by_id(self, sid: ObjectId) -> UserStream:
        for _stream in self.vods:
            if _stream.sid.id == sid:
                return _stream

        return None

    def find_user_catchups_by_id(self, sid: ObjectId) -> UserStream:
        for _stream in self.catchups:
            if _stream.sid.id == sid:
                return _stream

        return None

    def sync_content(self):
        self.select_all_streams(True)
        self.select_all_vods(True)

    # select
    def select_server(self, server: ServiceSettings, select: bool):
        if not server:
            return
        for stream in server.streams:
            if select:
                self.add_official_stream_by_id(stream.id)
            else:
                self.remove_official_stream(stream)

        self.select_all_series(self)

    def select_all_streams(self, select: bool):
        ustreams = self.own_streams()
        if not select:
            self.streams = ustreams
            return

        for stream in self.all_available_official_streams():
            user_stream = UserStream.make_from_stream(stream)
            cached = self.find_user_stream_by_id(stream.id)
            if cached:
                user_stream = cached
            ustreams.append(user_stream)

        self.streams = ustreams

    def select_all_vods(self, select: bool):
        vods = self.own_vods()
        if not select:
            self.vods = vods
            return

        for ovod in self.all_available_official_vods():
            user_vod = UserStream.make_from_stream(ovod)
            cached = self.find_user_vods_by_id(ovod.id)
            if cached:
                user_vod = cached
            vods.append(user_vod)

        self.vods = vods

    def select_all_catchups(self, select: bool):
        if not select:
            self.catchups = []
            return

        ustreams = []
        for ocatchup in self.all_available_official_catchups():
            user_catchup = UserStream.make_from_stream(ocatchup)
            cached = self.find_user_catchups_by_id(user_catchup.id)
            if cached:
                user_catchup = cached
            ustreams.append(user_catchup)

        self.catchups = ustreams

    def select_all_series(self, select: bool):
        if not select:
            self.series = []
            return

        self.series = self.all_available_official_series()

    def delete(self, *args, **kwargs):
        self.remove_all_own_streams()
        self.remove_all_own_vods()
        return super(Subscriber, self).delete(*args, **kwargs)

    def delete_fake(self, *args, **kwargs):
        self.remove_all_own_streams()
        self.remove_all_own_vods()
        self.status = Subscriber.Status.DELETED
        # return Document.delete(self, *args, **kwargs)

    @staticmethod
    def generate_password_hash(password: str) -> str:
        m = md5()
        m.update(password.encode())
        return m.hexdigest()

    @staticmethod
    def check_password_hash(hash_str: str, password: str) -> bool:
        return hash_str == Subscriber.generate_password_hash(password)

    @classmethod
    def make_subscriber(cls, email: str, first_name: str, last_name: str, password: str, country: str, language: str,
                        exp_date=MAX_DATE):
        return cls(email=email, first_name=first_name, last_name=last_name,
                   password=Subscriber.generate_password_hash(password), country=country,
                   language=language, exp_date=exp_date)

    @classmethod
    def make_entry(cls, json: dict) -> 'Subscriber':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, email_field = self.check_required_type(Subscriber.EMAIL_FIELD, str, json)
        if res:
            email = email_field.lower()
            if not is_valid_email(email):
                raise ValueError('Invalid email')
            self.email = email

        res, password = self.check_required_type(Subscriber.PASSWORD_FIELD, str, json)
        if res:
            self.password = Subscriber.generate_password_hash(password)

        res, first_name = Subscriber.check_required_type(Subscriber.FIRST_NAME_FIELD, str, json)
        if res:
            self.first_name = first_name

        res, last_name = Subscriber.check_required_type(Subscriber.LAST_NAME_FIELD, str, json)
        if res:
            self.last_name = last_name

        res, created_date_msec = self.check_optional_type(Subscriber.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, exp_date_msec = self.check_required_type(Subscriber.EXP_DATE_FIELD, int, json)
        if res:
            self.exp_date = datetime.utcfromtimestamp(exp_date_msec / 1000)

        res, status = self.check_required_type(Subscriber.STATUS_FIELD, int, json)
        if res:
            self.status = status

        res, max_dev = self.check_required_type(Subscriber.MAX_DEVICE_COUNT_FIELD, int, json)
        if res:
            self.max_devices_count = max_dev

        res, country = self.check_required_type(Subscriber.COUNTRY_FIELD, str, json)
        if res:
            if not constants.is_valid_country_code(country):
                raise ValueError('Invalid {0}'.format(Subscriber.COUNTRY_FIELD))
            self.country = country

        res, language = self.check_required_type(Subscriber.LANGUAGE_FIELD, str, json)
        if res:
            if not constants.is_valid_locale_code(language):
                raise ValueError('Invalid {0}'.format(Subscriber.LANGUAGE_FIELD))
            self.language = language

        res, servers = self.check_optional_type(Subscriber.SERVERS_FIELD, list, json)
        if res:
            object_servers = []
            for server in servers:
                object_servers.append(ObjectId(server))
            self.servers = object_servers

    def to_front_dict(self) -> dict:
        servers = []
        for server in self.servers:
            servers.append(server.get_id())
        return {Subscriber.FIRST_NAME_FIELD: self.first_name, Subscriber.LAST_NAME_FIELD: self.last_name,
                Subscriber.EMAIL_FIELD: self.email, Subscriber.ID_FIELD: self.get_id(),
                Subscriber.PASSWORD_FIELD: self.password,
                Subscriber.CREATED_DATE_FIELD: self.created_date_utc_msec(),
                Subscriber.EXP_DATE_FIELD: self.expiration_date_utc_msec(), Subscriber.STATUS_FIELD: self.status,
                Subscriber.MAX_DEVICE_COUNT_FIELD: self.max_devices_count,
                Subscriber.LANGUAGE_FIELD: self.language, Subscriber.COUNTRY_FIELD: self.country,
                Subscriber.SERVERS_FIELD: servers, Subscriber.DEVICES_COUNT_FIELD: len(self.devices)}
