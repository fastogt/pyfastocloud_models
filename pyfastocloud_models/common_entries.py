from pymodm import EmbeddedMongoModel, fields

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
        if not value_field:
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

    def to_front_dict(self) -> dict:
        return {Url.ID_FIELD: self.id, Url.URI_FIELD: self.uri}

    @staticmethod
    def generate_id():
        current_value = Url._next_url_id
        Url._next_url_id += 1
        return current_value

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        id_field = json.get(Url.ID_FIELD, None)
        if id_field is not None:
            self.id = id_field

        uri_field = json.get(Url.URI_FIELD, None)
        if not uri_field:
            raise ValueError('Invalid input({0} required)'.format(Url.URI_FIELD))

        self.uri = uri_field


class HttpProxy(EmbeddedMongoModel, Maker):
    URI_FIELD = 'uri'
    USER_FIELD = 'user'
    PASSWORD_FIELD = 'password'

    DEFAULT_USER = str()
    DEFAULT_PASSWORD = str()

    uri = fields.CharField(required=True)
    user = fields.CharField(default=DEFAULT_USER, required=False, blank=True)
    password = fields.CharField(default=DEFAULT_PASSWORD, required=False, blank=True)

    def __init__(self, *args, **kwargs):
        super(HttpProxy, self).__init__(*args, **kwargs)

    def to_front_dict(self) -> dict:
        result = {HttpProxy.URI_FIELD: self.uri}
        if self.user and self.password:
            result[HttpProxy.USER_FIELD] = self.user
            result[HttpProxy.PASSWORD_FIELD] = self.password

        return result

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        uri_field = json.get(HttpProxy.URI_FIELD, None)
        if not uri_field:
            raise ValueError('Invalid input({0} required)'.format(HttpProxy.URI_FIELD))

        self.uri = uri_field

        user_field = json.get(HttpProxy.USER_FIELD, None)
        password_field = json.get(HttpProxy.PASSWORD_FIELD, None)
        if user_field is not None and password_field is not None:  # optional field
            self.user = user_field
            self.password = password_field


class InputUrl(Url):
    USER_AGENT_FIELD = 'user_agent'
    STREAM_LINK_FIELD = 'stream_link'
    PROXY_FIELD = 'proxy'
    PROGRAM_NUMBER_FIELD = 'program_number'
    MULTICAST_IFACE_FIELD = 'multicast_iface'

    user_agent = fields.IntegerField(default=constants.UserAgent.GSTREAMER, required=True)
    stream_link = fields.BooleanField(default=False, required=True)
    proxy = fields.EmbeddedDocumentField(HttpProxy, blank=True)
    program_number = fields.IntegerField(blank=True)
    multicast_iface = fields.CharField(blank=True)

    def __init__(self, *args, **kwargs):
        super(InputUrl, self).__init__(*args, **kwargs)

    def to_front_dict(self) -> dict:
        base = super(InputUrl, self).to_front_dict()
        base[InputUrl.USER_AGENT_FIELD] = self.user_agent
        base[InputUrl.STREAM_LINK_FIELD] = self.stream_link
        if self.proxy:
            base[InputUrl.PROXY_FIELD] = self.proxy.to_front_dict()
        if self.program_number:
            base[InputUrl.PROGRAM_NUMBER_FIELD] = self.program_number
        if self.multicast_iface:
            base[InputUrl.MULTICAST_IFACE_FIELD] = self.multicast_iface
        return base

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        user_agent_field = json.get(InputUrl.USER_AGENT_FIELD, None)
        if user_agent_field is not None:  # optional field
            self.user_agent = user_agent_field

        stream_link_field = json.get(InputUrl.STREAM_LINK_FIELD, None)
        if stream_link_field is not None:  # optional field
            self.stream_link = stream_link_field

        proxy_field = json.get(InputUrl.PROXY_FIELD, None)
        if proxy_field is not None:  # optional field
            self.proxy = HttpProxy.make_entry(proxy_field)

        program_number_field = json.get(InputUrl.PROGRAM_NUMBER_FIELD, None)
        if program_number_field is not None:  # optional field
            self.program_number = program_number_field

        iface_field = json.get(InputUrl.MULTICAST_IFACE_FIELD, None)
        if iface_field is not None:  # optional field
            self.multicast_iface = iface_field


class OutputUrl(Url):
    HTTP_ROOT_FIELD = 'http_root'
    HLS_TYPE_FIELD = 'hls_type'

    http_root = fields.CharField(default='/', max_length=constants.MAX_PATH_LENGTH, required=False)
    hls_type = fields.IntegerField(default=constants.HlsType.HLS_PULL, required=False)

    def __init__(self, *args, **kwargs):
        super(OutputUrl, self).__init__(*args, **kwargs)

    def to_front_dict(self) -> dict:
        base = super(OutputUrl, self).to_front_dict()
        base[OutputUrl.HTTP_ROOT_FIELD] = self.http_root
        base[OutputUrl.HLS_TYPE_FIELD] = self.hls_type
        return base

    def update_entry(self, json: dict):
        Url.update_entry(self, json)

        http_root_field = json.get(OutputUrl.HTTP_ROOT_FIELD, None)
        if http_root_field:  # optional field
            self.http_root = http_root_field

        hls_type_field = json.get(OutputUrl.HLS_TYPE_FIELD, None)
        if hls_type_field is not None:  # optional field
            self.hls_type = hls_type_field


class Point(EmbeddedMongoModel, Maker):
    X_FIELD = 'x'
    Y_FIELD = 'y'

    x = fields.IntegerField(default=0, required=True)
    y = fields.IntegerField(default=0, required=True)

    def __init__(self, *args, **kwargs):
        super(Point, self).__init__(*args, **kwargs)

    def to_front_dict(self) -> dict:
        return {Point.X_FIELD: self.x, Point.Y_FIELD: self.y}

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        x_field = json.get(Point.X_FIELD, None)
        if x_field is not None:
            self.x = x_field

        y_field = json.get(Point.Y_FIELD, None)
        if y_field is not None:
            self.x = y_field

    def __str__(self):
        return '{0},{1}'.format(self.x, self.y)


class Size(EmbeddedMongoModel, Maker):
    WIDTH_FIELD = 'width'
    HEIGHT_FIELD = 'height'

    INVALID_WIDTH = -1
    INVALID_HEIGHT = -1

    width = fields.IntegerField(default=INVALID_WIDTH, required=True)
    height = fields.IntegerField(default=INVALID_HEIGHT, required=True)

    def __init__(self, *args, **kwargs):
        super(Size, self).__init__(*args, **kwargs)

    def is_valid(self):
        return self.width >= Size.INVALID_WIDTH and self.height >= Size.INVALID_HEIGHT

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        width_field = json.get(Size.WIDTH_FIELD, None)
        if width_field is not None:
            self.width = width_field

        height_field = json.get(Size.HEIGHT_FIELD, None)
        if height_field is not None:
            self.height = height_field

    def to_front_dict(self) -> dict:
        return {Size.WIDTH_FIELD: self.width, Size.HEIGHT_FIELD: self.height}

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Logo(EmbeddedMongoModel, Maker):
    PATH_FIELD = 'path'
    POSITION_FIELD = 'position'
    ALPHA_FIELD = 'alpha'
    SIZE_FIELD = 'size'

    INVALID_LOGO_PATH = str()
    MIN_LOGO_ALPHA = 0.0
    MAX_LOGO_ALPHA = 1.0
    DEFAULT_LOGO_ALPHA = MAX_LOGO_ALPHA

    path = fields.CharField(default=INVALID_LOGO_PATH, blank=True)
    position = fields.EmbeddedDocumentField(Point, default=Point(), required=True)
    alpha = fields.FloatField(default=DEFAULT_LOGO_ALPHA, min_value=MIN_LOGO_ALPHA, max_value=MAX_LOGO_ALPHA,
                              required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def __init__(self, *args, **kwargs):
        super(Logo, self).__init__(*args, **kwargs)

    def is_valid(self):
        return self.path != Logo.INVALID_LOGO_PATH and self.size.is_valid()

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        path_field = json.get(Logo.PATH_FIELD, None)
        if path_field is None:
            raise ValueError('Invalid input({0} required)'.format(Logo.PATH_FIELD))
        self.path = path_field

        point_field = json.get(Logo.POSITION_FIELD, None)
        if point_field is not None:  # optional field
            self.position = point_field

        alpha_field = json.get(Logo.ALPHA_FIELD, None)
        if alpha_field is not None:  # optional field
            self.alpha = alpha_field

        size_field = json.get(Logo.SIZE_FIELD, None)
        if size_field is not None:  # optional field
            self.size = Size.make_entry(size_field)

    def to_front_dict(self) -> dict:
        return {Logo.PATH_FIELD: self.path, Logo.POSITION_FIELD: self.position.to_front_dict(),
                Logo.ALPHA_FIELD: self.alpha, Logo.SIZE_FIELD: self.size.to_front_dict()}


class RSVGLogo(EmbeddedMongoModel, Maker):
    PATH_FIELD = 'path'
    POSITION_FIELD = 'position'
    SIZE_FIELD = 'size'

    INVALID_LOGO_PATH = str()

    path = fields.CharField(default=INVALID_LOGO_PATH, blank=True)
    position = fields.EmbeddedDocumentField(Point, default=Point(), required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def __init__(self, *args, **kwargs):
        super(RSVGLogo, self).__init__(*args, **kwargs)

    def is_valid(self):
        return self.path != RSVGLogo.INVALID_LOGO_PATH and self.size.is_valid()

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        path_field = json.get(RSVGLogo.PATH_FIELD, None)
        if path_field is None:
            raise ValueError('Invalid input({0} required)'.format(RSVGLogo.PATH_FIELD))
        self.path = path_field

        point_field = json.get(RSVGLogo.POSITION_FIELD, None)
        if point_field is not None:  # optional field
            self.position = point_field

        size_field = json.get(RSVGLogo.SIZE_FIELD, None)
        if size_field is not None:  # optional field
            self.size = Size.make_entry(size_field)

    def to_front_dict(self) -> dict:
        return {RSVGLogo.PATH_FIELD: self.path, RSVGLogo.POSITION_FIELD: self.position.to_front_dict(),
                RSVGLogo.SIZE_FIELD: self.size.to_front_dict()}


class Rational(EmbeddedMongoModel, Maker):
    NUM_FIELD = 'num'
    DEN_FIELD = 'den'

    INVALID_RATIO_NUM = 0
    INVALID_RATIO_DEN = 0

    num = fields.IntegerField(default=INVALID_RATIO_NUM, required=True)
    den = fields.IntegerField(default=INVALID_RATIO_DEN, required=True)

    def __init__(self, *args, **kwargs):
        super(Rational, self).__init__(*args, **kwargs)

    def is_valid(self):
        return self.num != Rational.INVALID_RATIO_NUM and self.den != Rational.INVALID_RATIO_DEN

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        num_field = json.get(Rational.NUM_FIELD, None)
        if num_field is not None:
            self.num = num_field

        den_field = json.get(Rational.DEN_FIELD, None)
        if den_field is not None:
            self.den = den_field

    def to_front_dict(self) -> dict:
        return {Rational.NUM_FIELD: self.num, Rational.DEN_FIELD: self.den}

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)


class HostAndPort(EmbeddedMongoModel, Maker):
    HOST_FIELD = 'host'
    PORT_FIELD = 'port'

    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 6317

    host = fields.CharField(default=DEFAULT_HOST, required=True)
    port = fields.IntegerField(default=DEFAULT_PORT, required=True)

    def __init__(self, *args, **kwargs):
        super(HostAndPort, self).__init__(*args, **kwargs)

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)
        host_field = json.get(HostAndPort.HOST_FIELD, None)
        if host_field is not None:
            self.host = host_field

        port_field = json.get(HostAndPort.PORT_FIELD, None)
        if port_field is not None:
            self.port = port_field

    def to_front_dict(self) -> dict:
        return {HostAndPort.HOST_FIELD: self.host, HostAndPort.PORT_FIELD: self.port}

    def __str__(self):
        return '{0}:{1}'.format(self.host, self.port)
