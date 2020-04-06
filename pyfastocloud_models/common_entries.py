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


class Url(EmbeddedMongoModel, Maker):
    ID_FIELD = 'id'
    URI_FIELD = 'uri'

    class Meta:
        allow_inheritance = True

    _next_url_id = 0

    id = fields.IntegerField(default=lambda: Url.generate_id(), required=True)
    uri = fields.CharField(min_length=constants.MIN_URI_LENGTH, max_length=constants.MAX_URI_LENGTH, required=True)

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

    uri = fields.CharField(required=True, blank=True)
    user = fields.CharField(default=DEFAULT_USER, required=False, blank=True)
    password = fields.CharField(default=DEFAULT_PASSWORD, required=False, blank=True)

    def to_front_dict(self) -> dict:
        return {HttpProxy.URI_FIELD: self.uri, HttpProxy.USER_FIELD: self.user, HttpProxy.PASSWORD_FIELD: self.password}

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        uri_field = json.get(HttpProxy.URI_FIELD, None)
        if not uri_field:
            raise ValueError('Invalid input({0} required)'.format(HttpProxy.URI_FIELD))

        self.uri = uri_field

        user_field = json.get(HttpProxy.USER_FIELD, None)
        if user_field is not None:  # optional field
            self.user = user_field

        password_field = json.get(HttpProxy.PASSWORD_FIELD, None)
        if password_field is not None:  # optional field
            self.password = password_field


class InputUrl(Url):
    USER_AGENT_FIELD = 'user_agent'
    STREAM_LINK_FIELD = 'stream_link'
    PROXY_FIELD = 'proxy'

    user_agent = fields.IntegerField(default=constants.UserAgent.GSTREAMER, required=True)
    stream_link = fields.BooleanField(default=False, required=True)
    proxy = fields.EmbeddedDocumentField(HttpProxy, blank=True)

    def to_front_dict(self) -> dict:
        base = super(InputUrl, self).to_front_dict()
        base[InputUrl.USER_AGENT_FIELD] = self.user_agent
        base[InputUrl.STREAM_LINK_FIELD] = self.stream_link
        if self.proxy:
            base[InputUrl.PROXY_FIELD] = self.proxy.to_front_dict()
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


class OutputUrl(Url):
    HTTP_ROOT_FIELD = 'http_root'
    HLS_TYPE_FIELD = 'hls_type'

    http_root = fields.CharField(default='/', max_length=constants.MAX_PATH_LENGTH, required=False)
    hls_type = fields.IntegerField(default=constants.HlsType.HLS_PULL, required=False)

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


class Size(EmbeddedMongoModel):
    width = fields.IntegerField(default=constants.INVALID_WIDTH, required=True)
    height = fields.IntegerField(default=constants.INVALID_HEIGHT, required=True)

    def is_valid(self):
        return self.width != constants.INVALID_WIDTH and self.height != constants.INVALID_HEIGHT

    @classmethod
    def make_entry(cls, size: str):
        if not size:
            raise ValueError('Size invalid input({0})'.format(size))
        parts = size.split('x')
        if len(parts) != 2:
            raise ValueError('Size invalid input({0})'.format(size))

        return cls(width=int(parts[0]), height=int(parts[1]))

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Logo(EmbeddedMongoModel, Maker):
    PATH_FIELD = 'path'
    X_FIELD = 'x'
    Y_FIELD = 'y'
    ALPHA_FIELD = 'alpha'
    SIZE_FIELD = 'size'

    path = fields.CharField(default=constants.INVALID_LOGO_PATH, blank=True)
    x = fields.IntegerField(default=constants.DEFAULT_LOGO_X, required=True)
    y = fields.IntegerField(default=constants.DEFAULT_LOGO_Y, required=True)
    alpha = fields.FloatField(default=constants.DEFAULT_LOGO_ALPHA, required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        path_field = json.get(Logo.PATH_FIELD, None)
        if not path_field:
            raise ValueError('Invalid input({0} required)'.format(HttpProxy.PATH_FIELD))

        x_field = json.get(Logo.X_FIELD, None)
        if x_field is not None:  # optional field
            self.x = x_field

        y_field = json.get(Logo.X_FIELD, None)
        if y_field is not None:  # optional field
            self.x = y_field

        alpha_field = json.get(Logo.ALPHA_FIELD, None)
        if alpha_field is not None:  # optional field
            self.alpha = alpha_field

        size_field = json.get(Logo.SIZE_FIELD, None)
        if size_field is not None:  # optional field
            self.size = Size.make_entry(size_field)

    def to_front_dict(self) -> dict:
        return {Logo.PATH_FIELD: self.path, 'position': '{0},{1}'.format(self.x, self.y), Logo.ALPHA_FIELD: self.alpha,
                Logo.SIZE_FIELD: str(self.size)}


class RSVGLogo(EmbeddedMongoModel):
    PATH_FIELD = 'path'
    X_FIELD = 'x'
    Y_FIELD = 'y'
    SIZE_FIELD = 'size'

    path = fields.CharField(default=constants.INVALID_LOGO_PATH, blank=True)
    x = fields.IntegerField(default=constants.DEFAULT_LOGO_X, required=True)
    y = fields.IntegerField(default=constants.DEFAULT_LOGO_Y, required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def update_entry(self, json: dict):
        Maker.update_entry(self, json)

        path_field = json.get(RSVGLogo.PATH_FIELD, None)
        if not path_field:
            raise ValueError('Invalid input({0} required)'.format(HttpProxy.PATH_FIELD))

        x_field = json.get(RSVGLogo.X_FIELD, None)
        if x_field is not None:  # optional field
            self.x = x_field

        y_field = json.get(RSVGLogo.X_FIELD, None)
        if y_field is not None:  # optional field
            self.x = y_field

        size_field = json.get(RSVGLogo.SIZE_FIELD, None)
        if size_field is not None:  # optional field
            self.size = Size.make_entry(size_field)

    def to_front_dict(self) -> dict:
        return {RSVGLogo.PATH_FIELD: self.path, 'position': '{0},{1}'.format(self.x, self.y),
                RSVGLogo.SIZE_FIELD: str(self.size)}


class Rational(EmbeddedMongoModel):
    num = fields.IntegerField(default=constants.INVALID_RATIO_NUM, required=True)
    den = fields.IntegerField(default=constants.INVALID_RATIO_DEN, required=True)

    def is_valid(self):
        return self.num != constants.INVALID_RATIO_NUM and self.den != constants.INVALID_RATIO_DEN

    @classmethod
    def make_entry(cls, ratio: str):
        if not ratio:
            raise ValueError('Rational invalid input({0})'.format(ratio))
        parts = ratio.split(':')
        if len(parts) != 2:
            raise ValueError('Rational invalid input({0})'.format(ratio))

        return cls(num=int(parts[0]), den=int(parts[1]))

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)


class HostAndPort(EmbeddedMongoModel):
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 6317
    host = fields.CharField(default=DEFAULT_HOST, required=True)
    port = fields.IntegerField(default=DEFAULT_PORT, required=True)

    @classmethod
    def make_entry(cls, host: str):
        if not host:
            raise ValueError('HostAndPort invalid input({0})'.format(host))
        parts = host.split(':')
        if len(parts) != 2:
            raise ValueError('HostAndPort invalid input({0})'.format(host))

        return cls(host=parts[0], port=int(parts[1]))

    def __str__(self):
        return '{0}:{1}'.format(self.host, self.port)
