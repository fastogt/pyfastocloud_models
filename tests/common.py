#!/usr/bin/env python3
import unittest

from pyfastocloud_models.common_entries import OutputUrl, InputUrl, Point, Size, Logo, RSVGLogo, HostAndPort, \
    Rational, StreamLink


class CommonTest(unittest.TestCase):
    def test_rational(self):
        num = 1
        den = 25
        invalid_rational = Rational()
        self.assertFalse(invalid_rational.is_valid())
        invalid_rational.num = num
        self.assertFalse(invalid_rational.is_valid())
        invalid_rational.den = den
        self.assertTrue(invalid_rational.is_valid())

        self.assertFalse(Rational(num=0, den=25).is_valid())
        self.assertFalse(Rational(num=21, den=0).is_valid())

        host = Rational(num=num, den=den)
        origin = {Rational.NUM_FIELD: num, Rational.DEN_FIELD: den}
        self.assertTrue(host.is_valid())
        self.assertEqual(host.to_front_dict(), origin)
        self.assertEqual(host, Rational.make_entry(origin))

    def test_host_and_port(self):
        host_str = 'localhost'
        port = 1235
        invalid_host = HostAndPort()
        self.assertFalse(invalid_host.is_valid())
        invalid_host.host = host_str
        self.assertFalse(invalid_host.is_valid())
        invalid_host.port = port
        self.assertTrue(invalid_host.is_valid())

        host = HostAndPort(host=host_str, port=port)
        origin = {HostAndPort.HOST_FIELD: host_str, HostAndPort.PORT_FIELD: port}
        self.assertTrue(host.is_valid())
        self.assertEqual(host.to_front_dict(), origin)
        self.assertEqual(host, HostAndPort.make_entry(origin))

    def test_size(self):
        width = 640
        height = 480
        invalid_size = Size()
        self.assertFalse(invalid_size.is_valid())
        invalid_size.width = width
        self.assertFalse(invalid_size.is_valid())
        invalid_size.height = height
        self.assertTrue(invalid_size.is_valid())

        point = Size(width=width, height=height)
        origin = {Size.WIDTH_FIELD: width, Size.HEIGHT_FIELD: height}
        self.assertTrue(point.is_valid())
        self.assertEqual(point.to_front_dict(), origin)
        self.assertEqual(point, Size.make_entry(origin))

    def test_point(self):
        x = 0
        y = 1
        invalid_point = Point()
        self.assertFalse(invalid_point.is_valid())
        invalid_point.x = x
        self.assertFalse(invalid_point.is_valid())
        invalid_point.y = y
        self.assertTrue(invalid_point.is_valid())

        point = Point(x=x, y=y)
        origin = {Point.X_FIELD: x, Point.Y_FIELD: y}
        self.assertTrue(point.is_valid())
        self.assertEqual(point.to_front_dict(), origin)
        self.assertEqual(point, Point.make_entry(origin))

    def test_streamlink_proxy(self):
        valid = StreamLink()
        self.assertTrue(valid.is_valid())
        self.assertEqual(valid.to_front_dict(), {})

        valid2 = StreamLink.make_entry({})
        self.assertTrue(valid2.is_valid())
        self.assertEqual(valid2.to_front_dict(), {})

    def test_logo(self):
        invalid_url_str = str()
        uri = 'test'
        size = Size(width=640, height=480)
        position = Point(x=0, y=0)
        alpha = 0.1

        invalid_logo = Logo()
        self.assertFalse(invalid_logo.is_valid())
        invalid_logo.uri = invalid_url_str
        self.assertFalse(invalid_logo.is_valid())
        invalid_logo.path = uri
        invalid_logo.position = position
        invalid_logo.size = size
        invalid_logo.alpha = alpha
        self.assertTrue(invalid_logo.is_valid())

        logo = Logo(path=uri, size=size, position=position, alpha=alpha)
        origin = {Logo.PATH_FIELD: uri, Logo.SIZE_FIELD: size.to_front_dict(),
                  Logo.POSITION_FIELD: position.to_front_dict(), Logo.ALPHA_FIELD: alpha}
        self.assertTrue(logo.is_valid())
        # self.assertEqual(logo.to_front_dict(), origin)
        self.assertEqual(logo, Logo.make_entry(origin))

    def test_rsvg_logo(self):
        invalid_url_str = str()
        uri = 'test'
        size = Size(width=640, height=480)
        position = Point(x=2, y=1)

        invalid_logo = RSVGLogo()
        self.assertFalse(invalid_logo.is_valid())
        invalid_logo.uri = invalid_url_str
        self.assertFalse(invalid_logo.is_valid())
        invalid_logo.path = uri
        invalid_logo.position = position
        invalid_logo.size = size
        self.assertTrue(invalid_logo.is_valid())

        logo = RSVGLogo(path=uri, size=size, position=position)
        origin = {RSVGLogo.PATH_FIELD: uri, RSVGLogo.SIZE_FIELD: size.to_front_dict(),
                  RSVGLogo.POSITION_FIELD: position.to_front_dict()}
        self.assertTrue(logo.is_valid())
        # self.assertEqual(logo.to_front_dict(), origin)
        self.assertEqual(logo, RSVGLogo.make_entry(origin))

    def test_input_url(self):
        invalid_input_url_str = str()
        uri = 'test'
        uid = 1

        invalid_input_url = InputUrl()
        self.assertFalse(invalid_input_url.is_valid())
        invalid_input_url.uri = invalid_input_url_str
        self.assertFalse(invalid_input_url.is_valid())
        invalid_input_url.uri = uri
        self.assertTrue(invalid_input_url.is_valid())
        invalid_input_url.id = None
        self.assertFalse(invalid_input_url.is_valid())

        invalid = {InputUrl.URI_FIELD: '0.0.0.0:8888', InputUrl.ID_FIELD: uid}
        self.assertRaises(ValueError, InputUrl.make_entry, invalid)

        valid = {InputUrl.URI_FIELD: 'http://localhost', InputUrl.ID_FIELD: uid}
        valid_url = InputUrl.make_entry(valid)
        self.assertTrue(valid_url.is_valid())

        input_url = InputUrl(id=uid, uri=uri)
        origin = {InputUrl.URI_FIELD: uri, InputUrl.ID_FIELD: uid}
        self.assertTrue(input_url.is_valid())
        self.assertEqual(input_url.to_front_dict(), origin)
        self.assertEqual(input_url, InputUrl.make_entry(origin))

        multicast_iface = 'eth1'
        input_url.multicast_iface = multicast_iface
        origin = {InputUrl.URI_FIELD: uri, InputUrl.ID_FIELD: uid,
                  InputUrl.MULTICAST_IFACE_FIELD: multicast_iface}
        self.assertTrue(input_url.is_valid())
        self.assertEqual(input_url.to_front_dict(), origin)
        self.assertEqual(input_url, InputUrl.make_entry(origin))

        input_url.proxy = 'http://localhost:8080'
        origin = {InputUrl.URI_FIELD: uri, InputUrl.ID_FIELD: uid,
                  InputUrl.MULTICAST_IFACE_FIELD: multicast_iface, InputUrl.PROXY_FIELD: 'http://localhost:8080'}
        self.assertTrue(input_url.is_valid())
        # self.assertEqual(input_url.to_front_dict(), origin)
        self.assertEqual(input_url, InputUrl.make_entry(origin))

    def test_output_url(self):
        invalid_output_url_str = str()
        uri = 'test'
        uid = 1

        invalid_output_url = OutputUrl()
        self.assertFalse(invalid_output_url.is_valid())
        invalid_output_url.uri = invalid_output_url_str
        self.assertFalse(invalid_output_url.is_valid())
        invalid_output_url.uri = uri
        self.assertTrue(invalid_output_url.is_valid())
        invalid_output_url.id = None
        self.assertFalse(invalid_output_url.is_valid())

        output_url = OutputUrl(id=uid, uri=uri)
        self.assertTrue(output_url.is_valid())
        self.assertEqual(output_url.to_front_dict(), {OutputUrl.URI_FIELD: uri, OutputUrl.ID_FIELD: uid})


if __name__ == '__main__':
    unittest.main()
