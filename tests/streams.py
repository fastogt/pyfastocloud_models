#!/usr/bin/env python3
import datetime
import unittest

from pyfastocloud_models.stream.entry import ProxyStream, OutputUrl


class StreamsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StreamsTest, self).__init__(*args, **kwargs)

    def test_proxy(self):
        now = datetime.datetime.utcnow()
        stable = int(now.microsecond / 1000) * 1000
        now = now.replace(microsecond=stable)
        msec = int(now.timestamp() * 1000)
        output_url = OutputUrl(uri='test')
        proxy_data = {ProxyStream.NAME_FIELD: 'Test', ProxyStream.GROUP_FIELD: 'Movies;USA',
                      ProxyStream.CREATED_DATE_FIELD: msec, ProxyStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        proxy = ProxyStream.make_entry(proxy_data)
        self.assertEqual(proxy.name, proxy_data[ProxyStream.NAME_FIELD])
        self.assertEqual(proxy.group, proxy_data[ProxyStream.GROUP_FIELD])
        self.assertEqual(proxy.created_date_utc_msec(), msec)
        arr = [output_url]
        self.assertEqual(proxy.output, arr)
        self.assertTrue(proxy.is_valid())


if __name__ == '__main__':
    unittest.main()
