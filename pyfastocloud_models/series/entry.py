from datetime import datetime

from bson.objectid import ObjectId
from pymodm import MongoModel, fields

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import Maker, BlankStringOK
from pyfastocloud_models.stream.entry import IStream
from pyfastocloud_models.utils.utils import date_to_utc_msec


class Serial(MongoModel, Maker):
    ID_FIELD = 'id'
    NAME_FIELD = 'name'
    ICON_FIELD = 'icon'
    PRICE_FIELD = 'price'
    GROUPS_FIELD = 'groups'
    VISIBLE_FIELD = 'visible'
    DESCRIPTION_FIELD = 'description'
    CREATED_DATE_FIELD = 'created_date'
    SEASON_FIELD = 'season'
    EPISODES_FIELD = 'episodes'
    VIEW_COUNT_FIELD = 'view_count'

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

    name = fields.CharField(max_length=MAX_SERIES_NAME_LENGTH, min_length=MIN_SERIES_NAME_LENGTH, required=True)
    icon = BlankStringOK(max_length=constants.MAX_URI_LENGTH,
                         min_length=constants.MIN_URI_LENGTH, required=True)
    groups = fields.ListField(fields.CharField(), default=[], required=True, blank=True)
    description = BlankStringOK(min_length=constants.MIN_STREAM_DESCRIPTION_LENGTH,
                                max_length=constants.MAX_STREAM_DESCRIPTION_LENGTH,
                                required=True)
    created_date = fields.DateTimeField(default=datetime.now, required=True)
    price = fields.FloatField(default=constants.DEFAULT_PRICE, min_value=constants.MIN_PRICE,
                              max_value=constants.MAX_PRICE, required=True)
    season = fields.IntegerField(default=1, min_value=0, required=True)
    visible = fields.BooleanField(default=True, required=True)
    episodes = fields.ListField(fields.ReferenceField(IStream, on_delete=fields.ReferenceField.PULL), default=[],
                                blank=True)

    def add_episode(self, episode: IStream):
        if not episode:
            return

        if episode not in self.episodes:
            self.episodes.append(episode)

    def remove_episode(self, episode: IStream):
        if not episode:
            return

        try:
            self.episodes.remove(episode)
        except ValueError:
            pass

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        result.pop('_id')
        result[Serial.CREATED_DATE_FIELD] = self.created_date_utc_msec()
        result[Serial.ID_FIELD] = self.get_id()
        episodes = []
        views = 0
        for episode in self.episodes:
            views += episode.view_count
            episodes.append(episode.get_id())
        result[Serial.VIEW_COUNT_FIELD] = views
        result[Serial.EPISODES_FIELD] = episodes
        return result.to_dict()

    def created_date_utc_msec(self):
        return date_to_utc_msec(self.created_date)

    @classmethod
    def make_entry(cls, json: dict) -> 'Serial':
        cl = cls()
        cl.update_entry(json)
        return cl

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

        res, icon = self.check_optional_type(Serial.ICON_FIELD, str, json)
        if res:  # optional field
            self.icon = icon

        res, price = self.check_optional_type(Serial.PRICE_FIELD, float, json)
        if res:  # optional field
            self.price = price

        res, description = Maker.check_optional_type(Serial.DESCRIPTION_FIELD, str, json)
        if res:
            self.description = description

        res, season = Maker.check_optional_type(Serial.SEASON_FIELD, int, json)
        if res:
            self.season = season

        res, visible = self.check_optional_type(Serial.VISIBLE_FIELD, bool, json)
        if res:  # optional field
            self.visible = visible

        res, episodes = self.check_optional_type(Serial.EPISODES_FIELD, list, json)
        if res:  # optional field
            stabled = []
            for episode in episodes:
                stabled.append(ObjectId(episode))
            self.episodes = stabled
