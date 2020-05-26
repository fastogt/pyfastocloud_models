from datetime import datetime

from bson.objectid import ObjectId
from pymodm import MongoModel, fields

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Maker, BlankStringOK
from pyfastocloud_models.utils.utils import date_to_utc_msec


class Serial(MongoModel, Maker):
    NAME_FIELD = 'name'
    GROUPS_FIELD = 'groups'
    VISIBLE_FIELD = 'visible'
    DESCRIPTION_FIELD = 'description'
    CREATED_DATE_FIELD = 'created_date'
    SEASON_FIELD = 'season'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            stream = Serial.objects.get({'_id': sid})
        except Serial.DoesNotExist:
            return None
        else:
            return stream

    class Meta:
        collection_name = 'series'

    MIN_SERIES_NAME_LENGTH = 3
    MAX_SERIES_NAME_LENGTH = 30

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    created_date = fields.DateTimeField(default=datetime.now, required=True)
    name = fields.CharField(max_length=MAX_SERIES_NAME_LENGTH, min_length=MIN_SERIES_NAME_LENGTH, required=True)
    groups = fields.ListField(fields.CharField(), default=[], required=True, blank=True)
    description = BlankStringOK(min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                                max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH,
                                required=True)
    season = fields.IntegerField(default=1, min_value=0, required=True)
    visible = fields.BooleanField(default=True, required=True)

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        result.pop('_id')
        result[Serial.CREATED_DATE_FIELD] = self.created_date_utc_msec()
        result[Serial.ID_FIELD] = self.get_id()
        return result.to_dict()

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, name = self.check_required_type(Serial.NAME_FIELD, str, json)
        if res:  # required field
            self.name = name

        res, created_date_msec = self.check_optional_type(Serial.CREATED_DATE_FIELD, int, json)
        if res:  # optional field
            self.created_date = datetime.utcfromtimestamp(created_date_msec / 1000)

        res, groups = self.check_optional_type(Serial.GROUPS_FIELD, list, json)
        if res:  # optional field
            self.groups = groups

        res, description = Maker.check_optional_type(Serial.DESCRIPTION_FIELD, str, json)
        if res:
            self.description = description

        res, season = Maker.check_optional_type(Serial.SEASON_FIELD, int, json)
        if res:
            self.season = season

        res, visible = self.check_optional_type(Serial.VISIBLE_FIELD, bool, json)
        if res:  # optional field
            self.visible = visible
