#!/usr/bin/env python3
import datetime
import unittest

from pyfastocloud_models.stream.entry import ProxyStream, RelayStream, EncodeStream, OutputUrl, InputUrl


class StreamsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StreamsTest, self).__init__(*args, **kwargs)

    def test_proxy(self):
        now = datetime.datetime.utcnow()
        stable = int(now.microsecond / 1000) * 1000
        now = now.replace(microsecond=stable)
        msec = int(now.timestamp() * 1000)
        output_url = OutputUrl(id=OutputUrl.generate_id(), uri='test')  # required
        name = 'Test'  # required
        proxy_data = {ProxyStream.NAME_FIELD: name, ProxyStream.GROUPS_FIELD: 'Movies;USA', ProxyStream.PRICE_FIELD: 1.1,
                      ProxyStream.CREATED_DATE_FIELD: msec, ProxyStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        proxy = ProxyStream.make_entry(proxy_data)
        self.assertEqual(proxy.name, proxy_data[ProxyStream.NAME_FIELD])
        self.assertEqual(proxy.groups, proxy_data[ProxyStream.GROUPS_FIELD])
        self.assertEqual(proxy.created_date_utc_msec(), msec)
        self.assertEqual(proxy.output, [output_url])
        self.assertTrue(proxy.is_valid())

    def test_relay(self):
        input_url = InputUrl(id=InputUrl.generate_id(), uri='test')  # required
        output_url = OutputUrl(id=OutputUrl.generate_id(), uri='test')  # required
        name = 'Relay'  # required
        relay_data = {RelayStream.NAME_FIELD: name, RelayStream.INPUT_FIELD: [input_url.to_front_dict()],
                      RelayStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        relay = RelayStream.make_entry(relay_data)
        self.assertEqual(relay.name, relay_data[ProxyStream.NAME_FIELD])
        self.assertEqual(relay.input, [input_url])
        self.assertEqual(relay.output, [output_url])
        self.assertTrue(relay.is_valid())

    def test_encode(self):
        input_url = InputUrl(id=InputUrl.generate_id(), uri='test')  # required
        output_url = OutputUrl(id=OutputUrl.generate_id(), uri='test')  # required
        name = 'Encode'  # required
        encode_data = {EncodeStream.NAME_FIELD: name, EncodeStream.INPUT_FIELD: [input_url.to_front_dict()],
                       EncodeStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        encode = EncodeStream.make_entry(encode_data)
        self.assertEqual(encode.name, encode_data[EncodeStream.NAME_FIELD])
        self.assertEqual(encode.input, [input_url])
        self.assertEqual(encode.output, [output_url])
        self.assertTrue(encode.is_valid())


if __name__ == '__main__':
    unittest.main()
