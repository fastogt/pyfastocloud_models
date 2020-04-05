from pymodm import MongoModel, fields

import pyfastocloud_models.constants as constants


class Epg(MongoModel):
    class Meta:
        collection_name = 'epg'

    def get_id(self) -> str:
        return str(self.pk)

    @property
    def id(self):
        return self.pk

    uri = fields.CharField(default='http://0.0.0.0/epg.xml', max_length=constants.MAX_URI_LENGTH, required=True)
    extension = fields.CharField(max_length=5, required=False)
