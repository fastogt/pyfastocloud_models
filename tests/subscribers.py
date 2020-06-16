#!/usr/bin/env python3
import datetime
import unittest

from pyfastocloud_models.stream.entry import ProxyStream, OutputUrl
from pyfastocloud_models.subscriber.entry import Subscriber, UserStream


class Subscribers(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Subscribers, self).__init__(*args, **kwargs)

    def test_subscribers_streams(self):
        now = datetime.datetime.utcnow()
        stable = int(now.microsecond / 1000) * 1000
        now = now.replace(microsecond=stable)
        msec = int(now.timestamp() * 1000)
        output_url = OutputUrl(id=OutputUrl.generate_id(), uri='test')  # required
        name = 'Test'  # required
        proxy_data = {ProxyStream.NAME_FIELD: name, ProxyStream.GROUPS_FIELD: ['Movies', 'USA'],
                      ProxyStream.PRICE_FIELD: 1.1,
                      ProxyStream.CREATED_DATE_FIELD: msec, ProxyStream.OUTPUT_FIELD: [output_url.to_front_dict()]}
        proxy = ProxyStream.make_entry(proxy_data)
        email = 'test@test.com'
        password = '1234'
        first_name = 'Alex'
        last_name = 'Palec'
        exp_date = stable + 1000000
        status = int(Subscriber.Status.ACTIVE)
        max_dev_count = 11
        country = 'EN'
        language = 'ru'
        sub = Subscriber.make_entry({Subscriber.EMAIL_FIELD: email, Subscriber.PASSWORD_FIELD: password,
                                     Subscriber.FIRST_NAME_FIELD: first_name, Subscriber.LAST_NAME_FIELD: last_name,
                                     Subscriber.EXP_DATE_FIELD: exp_date, Subscriber.STATUS_FIELD: status,
                                     Subscriber.MAX_DEVICE_COUNT_FIELD: max_dev_count,
                                     Subscriber.COUNTRY_FIELD: country, Subscriber.LANGUAGE_FIELD: language})
        ustream = UserStream(sid=proxy)
        self.assertEqual(sub.official_streams(), [])
        sub.add_official_stream(ustream)
        self.assertEqual(sub.official_streams(), [ustream])
        sub.remove_official_stream(proxy)
        self.assertEqual(sub.official_streams(), [])
        self.assertEqual(sub.email, email)
        self.assertEqual(sub.first_name, first_name)
        self.assertEqual(sub.last_name, last_name)
        self.assertEqual(sub.expiration_date_utc_msec(), exp_date)
        self.assertEqual(sub.status, status)
        self.assertEqual(sub.max_devices_count, max_dev_count)
        self.assertEqual(sub.country, country)
        self.assertEqual(sub.language, language)
        self.assertTrue(sub.is_valid())


if __name__ == '__main__':
    unittest.main()
