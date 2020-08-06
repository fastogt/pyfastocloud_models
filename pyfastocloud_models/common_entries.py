from pymodm import EmbeddedMongoModel, fields
from pymodm.errors import ValidationError

import pyfastocloud_models.constants as constants
from pyfastocloud_models.utils.utils import is_valid_url


class BlankStringOK(fields.CharField):
    def __init__(self, *args, **kwargs):
        super(BlankStringOK, self).__init__(*args, **kwargs, blank=True)

    def value_from_object(self, instance):
        result = getattr(instance, self.attname)
        if result is None:
            setattr(instance, self.attname, '')
        return super(BlankStringOK, self).value_from_object(instance)


class Maker:
    @classmethod
    def make_entry(cls, json: dict) -> 'Maker':
        cl = cls()
        cl.update_entry(json)
        return cl

    def update_entry(self, json: dict):
        if json is None:
            raise ValueError('Invalid input')

    @staticmethod
    def check_required_type(field: str, expected, json: dict):
        if json is None:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is None:
            raise ValueError('Invalid input({0} required)'.format(field))

        actual = type(value_field)
        if not Maker._check_is_same_types(actual, expected):
            raise ValueError('Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

        return True, value_field

    @staticmethod
    def check_optional_type(field: str, expected, json: dict):
        if json is None:
            raise ValueError('Invalid input')

        value_field = json.get(field, None)
        if value_field is not None:  # optional field
            actual = type(value_field)
            if not Maker._check_is_same_types(actual, expected):
                raise ValueError(
                    'Invalid input field({0}) actual type: {1}, expected: {2}'.format(field, actual, expected))

            return True, value_field

        return False, None

    @staticmethod
    def _check_is_same_types(actual, expected) -> bool:
        if actual is expected:
            return True

        if (int == actual or int == expected) and (float == actual or float == expected):
            return True

        return False


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
            if uri != 'test' and not is_valid_url(uri):
                raise ValueError('Invalid url: {0}'.format(uri))
            self.uri = uri


class StreamLink(EmbeddedMongoModel, Maker):
    HTTP_PROXY_FIELD = 'http_proxy'
    HTTPS_PROXY_FIELD = 'https_proxy'

    http_proxy = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH,
                                  required=False)
    https_proxy = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH,
                                   required=False)

    def __init__(self, *args, **kwargs):
        super(StreamLink, self).__init__(*args, **kwargs)

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

        res, http = self.check_optional_type(StreamLink.HTTP_PROXY_FIELD, str, json)
        if res:
            self.http_proxy = http

        res, https = self.check_optional_type(StreamLink.HTTPS_PROXY_FIELD, str, json)
        if res:
            self.https_proxy = https


class InputUrl(Url):
    USER_AGENT_FIELD = 'user_agent'
    STREAM_LINK_FIELD = 'stream_link'
    PROXY_FIELD = 'proxy'
    PROGRAM_NUMBER_FIELD = 'program_number'
    MULTICAST_IFACE_FIELD = 'multicast_iface'

    MIN_PROGRAM_NUMBER = 0
    MAX_PROGRAM_NUMBER = constants.MAX_INTEGER_NUMBER

    user_agent = fields.IntegerField(choices=constants.UserAgent.choices(), required=False)
    stream_link = fields.EmbeddedModelField(StreamLink, required=False)
    proxy = fields.CharField(required=False)
    program_number = fields.IntegerField(min_value=MIN_PROGRAM_NUMBER, max_value=MAX_PROGRAM_NUMBER, required=False)
    multicast_iface = fields.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(InputUrl, self).__init__(*args, **kwargs)

    @classmethod
    def make_stub(cls):
        return cls(id=Url.generate_id())

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        res, user_agent = self.check_optional_type(InputUrl.USER_AGENT_FIELD, int, json)
        if res:  # optional field
            self.user_agent = user_agent

        res, stream_link = self.check_optional_type(InputUrl.STREAM_LINK_FIELD, dict, json)
        if res:  # optional field
            self.stream_link = StreamLink.make_entry(stream_link)

        res, proxy = self.check_optional_type(InputUrl.PROXY_FIELD, str, json)
        if res:  # optional field
            self.proxy = proxy

        res, program_number = self.check_optional_type(InputUrl.PROGRAM_NUMBER_FIELD, int, json)
        if res:  # optional field
            self.program_number = program_number

        res, multicast_iface = self.check_optional_type(InputUrl.MULTICAST_IFACE_FIELD, str, json)
        if res:  # optional field
            self.multicast_iface = multicast_iface


class OutputUrl(Url):
    HTTP_ROOT_FIELD = 'http_root'
    HLS_TYPE_FIELD = 'hls_type'
    SRT_MODE_FIELD = 'srt_mode'

    http_root = fields.CharField(min_length=constants.MIN_PATH_LENGTH, max_length=constants.MAX_PATH_LENGTH,
                                 required=False)
    hls_type = fields.IntegerField(choices=constants.HlsType.choices(), required=False, blank=True)
    srt_mode = fields.IntegerField(choices=constants.SrtMode.choices(), required=False, blank=True)

    def __init__(self, *args, **kwargs):
        super(OutputUrl, self).__init__(*args, **kwargs)

    @classmethod
    def make_stub(cls):
        return cls(id=Url.generate_id())

    @classmethod
    def make_default_http(cls):
        return cls(id=Url.generate_id(), http_root='/', hls_type=constants.HlsType.HLS_PULL)

    @classmethod
    def make_test(cls):
        return cls(id=Url.generate_id(), uri=constants.DEFAULT_TEST_URL)

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        res_root, http_root = self.check_optional_type(OutputUrl.HTTP_ROOT_FIELD, str, json)
        res_type, hls_type = self.check_optional_type(OutputUrl.HLS_TYPE_FIELD, int, json)
        if res_root and res_type:  # optional field
            if http_root and hls_type is not None:
                self.http_root = http_root
                self.hls_type = hls_type

        res, srt_mode = self.check_optional_type(OutputUrl.SRT_MODE_FIELD, int, json)
        if res:  # optional field
            self.srt_mode = srt_mode


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
    position = fields.EmbeddedModelField(Point, required=True)
    alpha = fields.FloatField(min_value=MIN_LOGO_ALPHA, max_value=MAX_LOGO_ALPHA, required=True)
    size = fields.EmbeddedModelField(Size, required=True)

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
    position = fields.EmbeddedModelField(Point, required=True)
    size = fields.EmbeddedModelField(Size, required=True)

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


class MachineLearning(EmbeddedMongoModel, Maker):
    BACKEND_FILED = 'backend'
    MODEL_URL_FIELD = 'model_url'
    TRACKING = 'tracking'
    OVERLAY_FIELD = 'overlay'

    backend = fields.IntegerField(choices=constants.MlBackends.choices(), required=False)
    model_url = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH,
                                 required=True)
    tracking = fields.BooleanField(required=True)
    overlay = fields.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super(MachineLearning, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, backend = self.check_required_type(MachineLearning.BACKEND_FILED, int, json)
        if res:
            self.backend = backend

        res, url = self.check_required_type(MachineLearning.MODEL_URL_FIELD, str, json)
        if res:
            self.model_url = url

        res, tracking = self.check_required_type(MachineLearning.TRACKING, bool, json)
        if res:
            self.tracking = tracking

        res, overlay = self.check_required_type(MachineLearning.OVERLAY_FIELD, bool, json)
        if res:
            self.overlay = overlay

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()


class MetaUrl(EmbeddedMongoModel, Maker):
    NAME_FIELD = 'name'
    URL_FIELD = 'url'

    name = fields.CharField(min_length=constants.MIN_STREAM_NAME_LENGTH, max_length=constants.MAX_STREAM_NAME_LENGTH,
                            required=True)
    url = fields.CharField(max_length=constants.MAX_URI_LENGTH, min_length=constants.MIN_URI_LENGTH, required=True)

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
        res, name = self.check_required_type(MetaUrl.NAME_FIELD, str, json)
        if res:
            self.name = name

        res, url = self.check_required_type(MetaUrl.URL_FIELD, str, json)
        if res:
            self.url = url


class Phone(EmbeddedMongoModel, Maker):
    DIAL_CODE_FIELD = 'dial_code'
    PHONE_NUMBER_FIELD = 'phone_number'
    ISO_CODE_FILED = 'iso_code'

    dial_code = fields.CharField(required=True)
    phone_number = fields.CharField(required=True)
    iso_code = fields.CharField(default=constants.DEFAULT_LOCALE, required=True)

    def __init__(self, *args, **kwargs):
        super(Phone, self).__init__(*args, **kwargs)

    def is_valid(self) -> bool:
        try:
            self.full_clean()
        except ValidationError:
            return False
        return True

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        res, dial_code = self.check_required_type(Phone.DIAL_CODE_FIELD, str, json)
        if res:
            self.dial_code = dial_code

        res, phone_number = self.check_required_type(Phone.PHONE_NUMBER_FIELD, str, json)
        if res:
            self.phone_number = phone_number

        res, iso_code = self.check_required_type(Phone.ISO_CODE_FILED, str, json)
        if res:
            if not constants.is_valid_country_code(iso_code):
                raise ValueError('Invalid {0}'.format(Phone.ISO_CODE_FILED))
            self.iso_code = iso_code

    def to_front_dict(self) -> dict:
        result = self.to_son()
        result.pop('_cls')
        return result.to_dict()
