from pymodm import EmbeddedMongoModel, fields

import pyfastocloud_models.constants as constants


class Url(EmbeddedMongoModel):
    class Meta:
        allow_inheritance = True

    _next_url_id = 0

    id = fields.IntegerField(default=lambda: Url.generate_id(), required=True)
    uri = fields.CharField(default='test', max_length=constants.MAX_URL_LENGTH, required=True)

    @staticmethod
    def generate_id():
        current_value = Url._next_url_id
        Url._next_url_id += 1
        return current_value


class HttpProxy(EmbeddedMongoModel):
    INVALID_URL = str()
    DEFAULT_USER = str()
    DEFAULT_PASSWORD = str()

    url = fields.CharField(default=INVALID_URL, required=True, blank=True)
    user = fields.CharField(default=DEFAULT_USER, required=False, blank=True)
    password = fields.CharField(default=DEFAULT_PASSWORD, required=False, blank=True)

    def is_valid(self):
        return self.url != HttpProxy.INVALID_URL

    def to_dict(self) -> dict:
        return {'url': self.url}


class InputUrl(Url):
    user_agent = fields.IntegerField(default=constants.UserAgent.GSTREAMER, required=True)
    stream_link = fields.BooleanField(default=False, required=True)
    proxy = fields.EmbeddedDocumentField(HttpProxy)


class OutputUrl(Url):
    http_root = fields.CharField(default='/', max_length=constants.MAX_PATH_LENGTH, required=False)
    hls_type = fields.IntegerField(default=constants.HlsType.HLS_PULL, required=False)


class Size(EmbeddedMongoModel):
    width = fields.IntegerField(default=constants.INVALID_WIDTH, required=True)
    height = fields.IntegerField(default=constants.INVALID_HEIGHT, required=True)

    def is_valid(self):
        return self.width != constants.INVALID_WIDTH and self.height != constants.INVALID_HEIGHT

    def __str__(self):
        return '{0}x{1}'.format(self.width, self.height)


class Logo(EmbeddedMongoModel):
    path = fields.CharField(default=constants.INVALID_LOGO_PATH, required=True, blank=True)
    x = fields.IntegerField(default=constants.DEFAULT_LOGO_X, required=True)
    y = fields.IntegerField(default=constants.DEFAULT_LOGO_Y, required=True)
    alpha = fields.FloatField(default=constants.DEFAULT_LOGO_ALPHA, required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def to_dict(self) -> dict:
        return {'path': self.path, 'position': '{0},{1}'.format(self.x, self.y), 'alpha': self.alpha,
                'size': str(self.size)}


class RSVGLogo(EmbeddedMongoModel):
    path = fields.CharField(default=constants.INVALID_LOGO_PATH, required=True, blank=True)
    x = fields.IntegerField(default=constants.DEFAULT_LOGO_X, required=True)
    y = fields.IntegerField(default=constants.DEFAULT_LOGO_Y, required=True)
    size = fields.EmbeddedDocumentField(Size, default=Size())

    def is_valid(self):
        return self.path != constants.INVALID_LOGO_PATH

    def to_dict(self) -> dict:
        return {'path': self.path, 'position': '{0},{1}'.format(self.x, self.y), 'size': str(self.size)}


class Rational(EmbeddedMongoModel):
    num = fields.IntegerField(default=constants.INVALID_RATIO_NUM, required=True)
    den = fields.IntegerField(default=constants.INVALID_RATIO_DEN, required=True)

    def is_valid(self):
        return self.num != constants.INVALID_RATIO_NUM and self.den != constants.INVALID_RATIO_DEN

    def __str__(self):
        return '{0}:{1}'.format(self.num, self.den)


class HostAndPort(EmbeddedMongoModel):
    DEFAULT_HOST = 'localhost'
    DEFAULT_PORT = 6317
    host = fields.CharField(default=DEFAULT_HOST, required=True)
    port = fields.IntegerField(default=DEFAULT_PORT, required=True)

    def __str__(self):
        return '{0}:{1}'.format(self.host, self.port)
