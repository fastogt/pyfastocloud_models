from datetime import datetime
from hashlib import md5
from bson.objectid import ObjectId
from enum import IntEnum

from pymodm import MongoModel, fields, EmbeddedMongoModel

from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.stream.entry import IStream
import pyfastocloud_models.constants as constants
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


class Device(EmbeddedMongoModel):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    STATUS_FIELD = 'status'
    CREATED_DATE_FIELD = 'created_date'

    DEFAULT_DEVICE_NAME = 'Device'
    MIN_DEVICE_NAME_LENGTH = 2
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

    def to_dict(self) -> dict:
        return {Device.ID_FIELD: self.get_id(), Device.NAME_FIELD: self.name, Device.STATUS_FIELD: self.status,
                Device.CREATED_DATE_FIELD: date_to_utc_msec(self.created_date)}


class UserStream(EmbeddedMongoModel):
    FAVORITE_FIELD = 'favorite'
    PRIVATE_FIELD = 'private'
    RECENT_FIELD = 'recent'

    sid = fields.ReferenceField(IStream, required=True)
    favorite = fields.BooleanField(default=False)
    private = fields.BooleanField(default=False)
    recent = fields.DateTimeField(default=datetime.utcfromtimestamp(0))
    interruption_time = fields.IntegerField(default=0, min_value=0, max_value=constants.MAX_VIDEO_DURATION_MSEC,
                                            required=True)

    def get_id(self) -> str:
        return str(self.pk)

    def to_front_dict(self):
        res = self.sid.to_front_dict()
        res[UserStream.FAVORITE_FIELD] = self.favorite
        res[UserStream.PRIVATE_FIELD] = self.private
        res[UserStream.RECENT_FIELD] = date_to_utc_msec(self.recent)
        return res


class Subscriber(MongoModel):
    class Meta:
        collection_name = 'subscribers'
        allow_inheritance = True

    MAX_DATE = datetime(2100, 1, 1)
    ID_FIELD = 'id'
    EMAIL_FIELD = 'login'
    PASSWORD_FIELD = 'password'

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
    created_date = fields.DateTimeField(default=datetime.now)
    exp_date = fields.DateTimeField(default=MAX_DATE)
    status = fields.IntegerField(default=Status.NOT_ACTIVE)
    country = fields.CharField(min_length=2, max_length=3, required=True)
    language = fields.CharField(default=constants.DEFAULT_LOCALE, required=True)

    servers = fields.ListField(fields.ReferenceField(ServiceSettings, on_delete=fields.ReferenceField.PULL), default=[],
                               blank=True)
    devices = fields.EmbeddedDocumentListField(Device, default=[], blank=True)
    max_devices_count = fields.IntegerField(default=constants.DEFAULT_DEVICES_COUNT)
    # content
    streams = fields.EmbeddedDocumentListField(UserStream, default=[], blank=True)
    vods = fields.EmbeddedDocumentListField(UserStream, default=[], blank=True)
    catchups = fields.EmbeddedDocumentListField(UserStream, default=[], blank=True)

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def expiration_date_utc_msec(self):
        return date_to_utc_msec(self.exp_date)

    def add_server(self, server: ServiceSettings):
        self.servers.append(server)
        self.save()

    def add_device(self, device: Device):
        if len(self.devices) < self.max_devices_count:
            self.devices.append(device)
            self.save()

    def remove_device(self, did: ObjectId):
        for dev in self.devices:
            if dev.id == did:
                self.devices.remove(dev)
                break
        self.save()

        # devices = self.devices.get({'id': sid})
        # if devices:
        #    devices.delete()

    def find_device(self, did: ObjectId):
        for dev in self.devices:
            if dev.id == did:
                return dev

        return None

    def generate_playlist(self, did: str, lb_server_host_and_port: str) -> str:
        result = '#EXTM3U\n'
        sid = str(self.id)
        for stream in self.streams:
            if stream.private:
                result += stream.sid.generate_playlist(False)
            else:
                result += stream.sid.generate_device_playlist(sid, self.password, did, lb_server_host_and_port, False)

        return result

    def all_streams(self):
        return self.streams

    # official streams
    def add_official_stream_by_id(self, oid: ObjectId):
        user_stream = UserStream(sid=oid)
        self.add_official_stream(user_stream)

    def add_official_stream(self, user_stream: UserStream):
        if not user_stream:
            return

        for stream in self.streams:
            if not stream.private and stream.sid == user_stream.sid:
                return

        self.streams.append(user_stream)
        self.save()

    def remove_official_stream(self, ostream: IStream):
        if not ostream:
            return

        for stream in self.streams:
            if not stream.private and stream.sid == ostream:
                self.streams.remove(stream)
        self.save()

    def remove_official_stream_by_id(self, sid: ObjectId):
        original_stream = IStream.get_stream_by_id(sid)
        self.remove_official_stream(original_stream)

    # official vods
    def add_official_vod_by_id(self, oid: ObjectId):
        user_stream = UserStream(sid=oid)
        self.add_official_vod(user_stream)

    def add_official_vod(self, user_stream: UserStream):
        if not user_stream:
            return

        for vod in self.vods:
            if not vod.private and vod.sid == user_stream.sid:
                return

        self.vods.append(user_stream)
        self.save()

    def remove_official_vod(self, ostream: IStream):
        if not ostream:
            return

        for vod in self.vods:
            if not vod.private and vod.sid == ostream:
                self.vods.remove(vod)
        self.save()

    def remove_official_vod_by_id(self, sid: ObjectId):
        original_stream = IStream.get_stream_by_id(sid)
        self.remove_official_vod(original_stream)

    # official catchups
    def add_official_catchup_by_id(self, oid: ObjectId):
        user_stream = UserStream(sid=oid)
        self.add_official_catchup(user_stream)

    def add_official_catchup(self, user_stream: UserStream):
        if not user_stream:
            return

        for catchup in self.catchups:
            if not catchup.private and catchup.sid == user_stream.sid:
                return

        self.catchups.append(user_stream)
        self.save()

    def remove_official_catchup(self, ostream: IStream):
        if not ostream:
            return

        for catchup in self.catchups:
            if not catchup.private and catchup.sid == ostream:
                self.catchups.remove(catchup)
        self.save()

    def remove_official_catchup_by_id(self, sid: ObjectId):
        original_stream = IStream.get_stream_by_id(sid)
        self.remove_official_catchup(original_stream)

    # own
    def add_own_stream(self, user_stream: UserStream):
        for stream in self.streams:
            if stream.private and stream.sid == user_stream:
                return

        user_stream.private = True
        self.streams.append(user_stream)
        self.save()

    def remove_own_stream_by_id(self, sid: ObjectId):
        stream = IStream.get_stream_by_id(sid)
        if stream:
            for stream in self.streams:
                if stream.sid == sid:
                    self.stream.remove(stream)
            stream.delete()
            self.save()

    def remove_all_own_streams(self):
        for stream in self.streams:
            if stream.private:
                self.streams.remove(stream)
        self.save()

    def add_own_vod(self, user_stream: UserStream):
        for vod in self.vod:
            if vod.private and vod.sid == user_stream.sid:
                return

        user_stream.private = True
        self.vod.append(user_stream)
        self.save()

    def remove_own_vod_by_id(self, sid: ObjectId):
        vod = IStream.get_stream_by_id(sid)
        if vod:
            for vod in self.vod:
                if vod.private and vod.sid == sid:
                    self.vod.remove(vod)
            vod.delete()
            self.save()

    def remove_all_own_vods(self):
        for stream in self.vods:
            if stream.private:
                self.vods.remove(stream)
        self.save()

    # available
    def official_streams(self):
        streams = []
        for stream in self.streams:
            if not stream.private:
                streams.append(stream)

        return streams

    def official_vods(self):
        streams = []
        for stream in self.vods:
            if not stream.private:
                streams.append(stream)

        return streams

    def official_catchups(self):
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

    def all_available_servers(self):
        return self.servers

    def all_available_official_streams(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            for stream in serv.streams:
                if is_live_stream(stream):
                    streams.append(stream)

        return streams

    def all_available_official_vods(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            for stream in serv.streams:
                if is_vod_stream(stream):
                    streams.append(stream)

        return streams

    def all_available_official_catchups(self) -> [IStream]:
        streams = []
        for serv in self.servers:
            for stream in serv.streams:
                if is_catchup(stream):
                    streams.append(stream)

        return streams

    # select
    def select_all_streams(self, select: bool):
        if not select:
            self.streams = []
            self.save()
            return

        ustreams = []
        for stream in self.all_available_official_streams():
            user_stream = UserStream(sid=stream.id)
            for stream in self.streams:
                if not stream.private and stream.sid == user_stream.sid:
                    user_stream = stream
                    break
            ustreams.append(user_stream)

        self.streams = ustreams
        self.save()

    def select_all_vods(self, select: bool):
        if not select:
            self.vods = []
            self.save()
            return

        ustreams = []
        for ovod in self.all_available_official_vods():
            user_vod = UserStream(sid=ovod.id)
            for vod in self.vods:
                if not vod.private and vod.sid == user_vod.sid:
                    user_vod = vod
                    break
            ustreams.append(user_vod)

        self.vods = ustreams
        self.save()

    def select_all_catchups(self, select: bool):
        if not select:
            self.catchups = []
            self.save()
            return

        ustreams = []
        for ocatchup in self.all_available_official_catchups():
            user_catchup = UserStream(sid=ocatchup.id)
            for catchup in self.catchups:
                if not catchup.private and catchup.sid == user_catchup.sid:
                    user_catchup = catchup
                    break
            ustreams.append(user_catchup)

        self.catchups = ustreams
        self.save()

    def delete(self, *args, **kwargs):
        self.remove_all_own_streams()
        self.remove_all_own_vods()
        return super(Subscriber, self).delete(*args, **kwargs)

    def delete_fake(self, *args, **kwargs):
        self.remove_all_own_streams()
        self.remove_all_own_vods()
        self.status = Subscriber.Status.DELETED
        self.save()
        # return Document.delete(self, *args, **kwargs)

    @staticmethod
    def make_md5_hash_from_password(password: str) -> str:
        m = md5()
        m.update(password.encode())
        return m.hexdigest()

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return Subscriber.make_md5_hash_from_password(password)

    @staticmethod
    def check_password_hash(hash_str: str, password: str) -> bool:
        return hash_str == Subscriber.generate_password_hash(password)

    @classmethod
    def make_subscriber(cls, email: str, first_name: str, last_name: str, password: str, country: str, language: str,
                        exp_date=MAX_DATE):
        return cls(email=email, first_name=first_name, last_name=last_name,
                   password=Subscriber.make_md5_hash_from_password(password), country=country,
                   language=language, exp_date=exp_date)
