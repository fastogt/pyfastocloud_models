from datetime import datetime
from enum import IntEnum

from bson.objectid import ObjectId
from mongoengine import Document, fields, errors

from pyfastocloud_models.common_entries import Maker
from pyfastocloud_models.utils.utils import date_to_utc_msec


class ContentRequest(Document, Maker):
    ID_FIELD = 'id'
    TITLE_FIELD = 'title'
    TYPE_FIELD = 'type'
    STATUS_FIELD = 'status'
    CREATED_DATE_FIELD = 'created_date'

    meta = {'collection': 'requests', 'allow_inheritance': False}

    @staticmethod
    def all():
        return ContentRequest.objects.all()

    @staticmethod
    def get_by_id(sid: ObjectId):
        return ContentRequest.objects(id=sid).first()

    class Status(IntEnum):
        NEW = 0
        IN_PROGRESS = 1
        DONE = 2

    class Type(IntEnum):
        LIVE = 0,
        VODS = 1,
        SERIAL = 2

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    title = fields.StringField(required=True)
    type = fields.IntField(default=Type.LIVE, required=True)  #
    status = fields.IntField(default=Status.NEW, required=True)  #
    created_date = fields.DateTimeField(default=datetime.now, required=True)  #

    def to_front_dict(self) -> dict:
        return {ContentRequest.ID_FIELD: self.get_id(), ContentRequest.TITLE_FIELD: self.title,
                ContentRequest.TYPE_FIELD: self.type,
                ContentRequest.CREATED_DATE_FIELD: self.created_date_utc_msec(),
                ContentRequest.STATUS_FIELD: self.status}

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    @classmethod
    def make_entry(cls, json: dict) -> 'ContentRequest':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, title = self.check_required_type(ContentRequest.TITLE_FIELD, str, json)
        if res:  # required field
            self.title = title

        res, ptype = self.check_required_type(ContentRequest.TYPE_FIELD, int, json)
        if res:  # required field
            self.type = ptype

        res, status = self.check_required_type(ContentRequest.STATUS_FIELD, int, json)
        if res:  # required field
            self.status = status

        res, created_date_msec = self.check_optional_type(ContentRequest.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        try:
            self.validate()
        except errors.ValidationError as err:
            raise ValueError(err.message)
