from pymodm import EmbeddedMongoModel, fields
from pymodm.errors import ValidationError

import pyfastocloud_models.constants as constants


class Maker:
    @classmethod
    def make_entry(cls, json: dict) -> 'Maker':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        if not json:
            raise ValueError('Invalid input')

    @staticmethod
    def check_required_type(field: str, expected, json: dict):
        if not json:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is None:
            raise ValueError('Invalid input({0} required)'.format(field))

        actual = type(value_field)
        if actual is not expected:
            raise ValueError('Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

        return True, value_field

    @staticmethod
    def check_optional_type(field: str, expected, json: dict):
        if not json:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is not None:  # optional field
            actual = type(value_field)
            if actual is not expected:
                raise ValueError(
                    'Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

            return True, value_field

        return False, None


class Url(EmbeddedMongoModel, Maker):
    ID_FIELD = 'id'
    URI_FIELD = 'uri'

    class Meta:
        allow_inheritance = True

    _next_url_id = 0

    id = fields.IntegerField(default=lambda: Url.generate_id(), required=True)
    uri = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH, required=True)

    def __init__(self, *args, **kwargs):
        super(Url, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    @staticmethod
    def generate_id():
        current_value = Url._next_url_id
        Url._next_url_id += 1
        return current_value

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, id_field = self.check_required_type(Url.ID_FIELD, int, json)
        if res:
            self.id = id_field

        res, uri = self.check_required_type(Url.URI_FIELD, str, json)
        if res:
            self.uri = uri


class HttpProxy(EmbeddedMongoModel, Maker):
    URI_FIELD = 'uri'
    USER_FIELD = 'user'
    PASSWORD_FIELD = 'password'

    uri = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH, required=True)
    user = fields.CharField(required=False)
    password = fields.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(HttpProxy, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, uri = self.check_required_type(HttpProxy.URI_FIELD, str, json)
        if res:
            self.uri = uri

        res_user, user = self.check_optional_type(HttpProxy.USER_FIELD, str, json)
        res_password, password = self.check_optional_type(HttpProxy.PASSWORD_FIELD, str, json)

        if res_user and res_password:  # optional field
            self.user = user
            self.password = password


class InputUrl(Url):
    USER_AGENT_FIELD = 'user_agent'
    STREAM_LINK_FIELD = 'stream_link'
    PROXY_FIELD = 'proxy'
    PROGRAM_NUMBER_FIELD = 'program_number'
    MULTICAST_IFACE_FIELD = 'multicast_iface'

    MIN_PROGRAM_NUMBER = 0
    MAX_PROGRAM_NUMBER = constants.MAX_INTEGER_NUMBER

    user_agent = fields.IntegerField(choices=constants.UserAgent.choices(), required=False)
    stream_link = fields.BooleanField(required=False)
    proxy = fields.EmbeddedDocumentField(HttpProxy, blank=True)
    program_number = fields.IntegerField(min_value=MIN_PROGRAM_NUMBER,
                                         max_value=MAX_PROGRAM_NUMBER, required=False)
    multicast_iface = fields.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(InputUrl, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        res, user_agent = self.check_optional_type(InputUrl.USER_AGENT_FIELD, int, json)
        if res:  # optional field
            self.user_agent = user_agent

        res, stream_link = self.check_optional_type(InputUrl.STREAM_LINK_FIELD, bool, json)
        if res:  # optional field
            self.stream_link = stream_link

        res, proxy = self.check_optional_type(InputUrl.PROXY_FIELD, dict, json)
        if res:  # optional field
            self.proxy = HttpProxy.make_entry(proxy)

        res, program_number = self.check_optional_type(InputUrl.PROGRAM_NUMBER_FIELD, int, json)
        if res:  # optional field
            self.program_number = program_number

        res, multicast_iface = self.check_optional_type(InputUrl.MULTICAST_IFACE_FIELD, str, json)
        if res:  # optional field
            self.multicast_iface = multicast_iface


class OutputUrl(Url):
    HTTP_ROOT_FIELD = 'http_root'
    HLS_TYPE_FIELD = 'hls_type'

    http_root = fields.CharField(min_length=constants.MIN_PATH_LENGTH, max_length=constants.MAX_PATH_LENGTH,
                                 required=False)
    hls_type = fields.IntegerField(choices=constants.HlsType.choices(), required=False)

    def __init__(self, *args, **kwargs):
        super(OutputUrl, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        res_root, http_root = self.check_optional_type(OutputUrl.HTTP_ROOT_FIELD, str, json)
        res_type, hls_type = self.check_optional_type(OutputUrl.HLS_TYPE_FIELD, int, json)
        if res_root and res_type:  # optional field
            self.http_root = http_root
            self.hls_type = hls_type


class Point(EmbeddedMongoModel, Maker):
    X_FIELD = 'x'
    Y_FIELD = 'y'

    x = fields.IntegerField(required=True)
    y = fields.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(Point, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, x = self.check_required_type(Point.X_FIELD, int, json)
        if res:
            self.x = x

        res, y = self.check_required_type(Point.Y_FIELD, int, json)
        if res:
            self.y = y

    def __str__(self):
        return '{0},{1}'.format(self.x, self.y)


class Size(EmbeddedMongoModel, Maker):
    WIDTH_FIELD = 'width'
    HEIGHT_FIELD = 'height'

    INVALID_WIDTH = 0
    INVALID_HEIGHT = 0

    width = fields.IntegerField(required=True)
    height = fields.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(Size, self).__init__(*args, **kwargs)

    def clean(self):
        if self.width <= Size.INVALID_WIDTH:
            raise ValidationError('{0} should be bigger than'.format(Size.WIDTH_FIELD, Size.INVALID_WIDTH))

        if self.height <= Size.INVALID_HEIGHT:
            raise ValidationError('{0} should be bigger than'.format(Size.HEIGHT_FIELD, Size.INVALID_HEIGHT))

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, width = self.check_required_type(Size.WIDTH_FIELD, int, json)
        if res:
            self.width = width

        res, height = self.check_required_type(Size.HEIGHT_FIELD, int, json)
        if res:
            self.height = height

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Logo(EmbeddedMongoModel, Maker):
    PATH_FIELD = 'path'
    POSITION_FIELD = 'position'
    ALPHA_FIELD = 'alpha'
    SIZE_FIELD = 'size'

    MIN_LOGO_ALPHA = 0.0
    MAX_LOGO_ALPHA = 1.0
    DEFAULT_LOGO_ALPHA = MAX_LOGO_ALPHA

    path = fields.CharField(required=True)
    position = fields.EmbeddedDocumentField(Point, required=True)
    alpha = fields.FloatField(min_value=MIN_LOGO_ALPHA, max_value=MAX_LOGO_ALPHA,
                              required=True)
    size = fields.EmbeddedDocumentField(Size, required=True)

    def __init__(self, *args, **kwargs):
        super(Logo, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, path = self.check_required_type(Logo.PATH_FIELD, str, json)
        if res:
            self.path = path

        res, point = self.check_required_type(Logo.POSITION_FIELD, dict, json)
        if res:  # optional field
            self.position = Point.make_entry(point)

        res, alpha = self.check_required_type(Logo.ALPHA_FIELD, float, json)
        if res:  # optional field
            self.alpha = alpha

        res, size = self.check_required_type(Logo.SIZE_FIELD, dict, json)
        if res:  # optional field
            self.size = Size.make_entry(size)

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()


class RSVGLogo(EmbeddedMongoModel, Maker):
    PATH_FIELD = 'path'
    POSITION_FIELD = 'position'
    ALPHA_FIELD = 'alpha'
    SIZE_FIELD = 'size'

    path = fields.CharField(required=True)
    position = fields.EmbeddedDocumentField(Point, required=True)
    size = fields.EmbeddedDocumentField(Size, required=True)

    def __init__(self, *args, **kwargs):
        super(RSVGLogo, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        res, path = self.check_required_type(Logo.PATH_FIELD, str, json)
        if res:
            self.path = path

        res, point = self.check_required_type(Logo.POSITION_FIELD, dict, json)
        if res:  # optional field
            self.position = Point.make_entry(point)

        res, size = self.check_required_type(Logo.SIZE_FIELD, dict, json)
        if res:  # optional field
            self.size = Size.make_entry(size)

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()


class Rational(EmbeddedMongoModel, Maker):
    NUM_FIELD = 'num'
    DEN_FIELD = 'den'

    INVALID_RATIO_NUM = 0
    INVALID_RATIO_DEN = 0

    num = fields.IntegerField(required=True)
    den = fields.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(Rational, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def clean(self):
        if self.num <= Rational.INVALID_RATIO_NUM:
            raise ValidationError('{0} should be bigger than'.format(Rational.NUM_FIELD, Rational.INVALID_RATIO_NUM))

        if self.den <= Rational.INVALID_RATIO_NUM:
            raise ValidationError('{0} should be bigger than'.format(Rational.DEN_FIELD, Rational.INVALID_RATIO_DEN))

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, num = self.check_required_type(Rational.NUM_FIELD, int, json)
        if res:
            self.num = num

        res, den = self.check_required_type(Rational.DEN_FIELD, int, json)
        if res:
            self.den = den

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)


class HostAndPort(EmbeddedMongoModel, Maker):
    HOST_FIELD = 'host'
    PORT_FIELD = 'port'

    host = fields.CharField(required=True)
    port = fields.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(HostAndPort, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, host = self.check_required_type(HostAndPort.HOST_FIELD, str, json)
        if res:
            self.host = host

        res, port = self.check_required_type(HostAndPort.PORT_FIELD, int, json)
        if res:
            self.port = port

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()

    def __str__(self):
        return '{0}:{1}'.format(self.host, self.port)
