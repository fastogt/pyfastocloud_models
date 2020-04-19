#!/usr/bin/env python3
import unittest

from pyfastocloud_models.common_entries import HttpProxy, OutputUrl, InputUrl, Point, Size, Logo


class CommonTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CommonTest, self).__init__(*args, **kwargs)

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
        self.assertEqual(point, InputUrl.make_entry(origin))

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
        self.assertEqual(point, InputUrl.make_entry(origin))

    def test_http_proxy(self):
        invalid_proxy_url_str = str()
        uri = 'test'

        invalid_proxy = HttpProxy()
        self.assertFalse(invalid_proxy.is_valid())
        invalid_proxy.uri = invalid_proxy_url_str
        self.assertFalse(invalid_proxy.is_valid())
        invalid_proxy.uri = 'test'
        self.assertTrue(invalid_proxy.is_valid())

        proxy = HttpProxy(uri=uri)
        origin = {HttpProxy.URI_FIELD: uri}
        self.assertTrue(proxy.is_valid())
        self.assertEqual(proxy.to_front_dict(), origin)
        self.assertEqual(proxy, InputUrl.make_entry(origin))

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
        invalid_logo.uri = uri
        invalid_logo.position = position
        invalid_logo.size = size
        invalid_logo.alpha = alpha
        self.assertTrue(invalid_logo.is_valid())

        logo = Logo(path=uri, size=size, position=position, alpha=alpha)
        origin = {Logo.PATH_FIELD: uri, Logo.SIZE_FIELD: size.to_front_dict(),
                  Logo.POSITION_FIELD: position.to_front_dict(), Logo.ALPHA_FIELD: alpha}
        self.assertTrue(logo.is_valid())
        self.assertEqual(logo.to_front_dict(), origin)
        self.assertEqual(logo, InputUrl.make_entry(origin))

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

        proxy = HttpProxy(uri='test')
        input_url.proxy = proxy
        origin = {InputUrl.URI_FIELD: uri, InputUrl.ID_FIELD: uid,
                  InputUrl.MULTICAST_IFACE_FIELD: multicast_iface, InputUrl.PROXY_FIELD: proxy.to_front_dict()}
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
