#!/usr/bin/env python3
import datetime
import unittest

import pyfastocloud_models.constants as constants
from pyfastocloud_models.series.entry import Serial
from pyfastocloud_models.stream.entry import ProxyVodStream, OutputUrl


class SeriesTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SeriesTest, self).__init__(*args, **kwargs)

    def test_workflow(self):
        now = datetime.datetime.utcnow()
        stable = int(now.microsecond / 1000) * 1000
        now = now.replace(microsecond=stable)
        msec = int(now.timestamp() * 1000)
        output_url = OutputUrl(id=OutputUrl.generate_id(), uri='test')  # required
        name = 'Test'  # required
        proxy_data = {ProxyVodStream.NAME_FIELD: name, ProxyVodStream.GROUPS_FIELD: ['Movies', 'USA'],
                      ProxyVodStream.PRICE_FIELD: 1.1,
                      ProxyVodStream.CREATED_DATE_FIELD: msec,
                      ProxyVodStream.VOD_TYPE_FIELD: int(constants.VodType.SERIES),
                      ProxyVodStream.PRIME_DATE_FIELD: msec,
                      ProxyVodStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        proxy = ProxyVodStream.make_entry(proxy_data)
        proxy2 = ProxyVodStream.make_entry(proxy_data)

        ser = Serial()
        self.assertTrue(ser.is_valid())
        ser.add_episode(proxy)
        self.assertEqual(len(ser.episodes), 1)
        ser.add_episode(proxy)
        self.assertEqual(len(ser.episodes), 1)
        ser.remove_episode(proxy2)
        self.assertEqual(len(ser.episodes), 1)
        ser.remove_episode(proxy)
        self.assertEqual(len(ser.episodes), 0)


if __name__ == '__main__':
    unittest.main()
