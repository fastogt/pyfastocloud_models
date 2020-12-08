from enum import IntEnum

from mongoengine import EmbeddedDocument, fields


class ProviderPair(EmbeddedDocument):
    ID_FIELD = 'id'
    ROLE_FIELD = 'role'

    class Roles(IntEnum):
        READ = 0
        WRITE = 1
        SUPPORT = 2
        ADMIN = 3

        @classmethod
        def choices(cls):
            return [(choice, choice.name) for choice in cls]

        @classmethod
        def coerce(cls, item):
            return cls(int(item)) if not isinstance(item, cls) else item

        def __str__(self):
            return str(self.value)

    user = fields.ReferenceField('Provider')
    role = fields.IntField(min_value=Roles.READ, max_value=Roles.ADMIN, default=Roles.ADMIN)

    def to_front_dict(self) -> dict:
        return {ProviderPair.ID_FIELD: self.user.get_id(), ProviderPair.ROLE_FIELD: self.role, 'email': self.user.email}
