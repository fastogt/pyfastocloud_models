#!/usr/bin/env python3
import datetime
import unittest

from mongoengine import connect

from pyfastocloud_models.service.entry import ServiceSettings, HostAndPort
from pyfastocloud_models.stream.entry import ProxyStream, OutputUrl


class StreamsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StreamsTest, self).__init__(*args, **kwargs)
        connect(db='iptv')

    def test_proxy(self):
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
        proxy.save()

        name_server = 'Server'
        host = HostAndPort(host='localhost', port=1234)
        http_host = HostAndPort(host='localhost1', port=1235)
        vods_host = HostAndPort(host='localhost2', port=1236)
        cods_host = HostAndPort(host='localhost3', port=1237)
        nginx_host = HostAndPort(host='localhost', port=1344)
        rtmp_host = HostAndPort(host='localhost', port=1935)
        feed = '/home/fead'
        timeshift_dir = '/home/time'
        hls_dir = '/home/tss'
        vods_dir = '/home/vods'
        cods_dir = '/home/cods'
        proxy_dir = '/hone/proxy'
        data_dir = '/home/data'
        monitoring = True
        auto_start = True
        price = 0.1

        server = ServiceSettings.make_entry({ServiceSettings.NAME_FIELD: name_server,
                                             ServiceSettings.HOST_FIELD: host.to_front_dict(),
                                             ServiceSettings.HTTP_HOST_FIELD: http_host.to_front_dict(),
                                             ServiceSettings.VODS_HOST_FIELD: vods_host.to_front_dict(),
                                             ServiceSettings.CODS_HOST_FIELD: cods_host.to_front_dict(),
                                             ServiceSettings.NGINX_HOST_FIELD: nginx_host.to_front_dict(),
                                             ServiceSettings.RTMP_HOST_FIELD: rtmp_host.to_front_dict(),
                                             ServiceSettings.FEEDBACK_DIRECOTRY_FIELD: feed,
                                             ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD: timeshift_dir,
                                             ServiceSettings.HLS_DIRECTORY_FIELD: hls_dir,
                                             ServiceSettings.VODS_DIRECTORY_FIELD: vods_dir,
                                             ServiceSettings.CODS_DIRECTORY_FIELD: cods_dir,
                                             ServiceSettings.PROXY_DIRECTORY_FIELD: proxy_dir,
                                             ServiceSettings.DATA_DIRECTORY_FIELD: data_dir,
                                             ServiceSettings.MONITORING_FILED: monitoring,
                                             ServiceSettings.AUTO_START_FIELD: auto_start,
                                             ServiceSettings.PRICE_PACKAGE_FIELD: price})
        server.add_stream(proxy)
        self.assertEqual(len(server.streams), 1)
        server.remove_stream(proxy)
        self.assertEqual(len(server.streams), 0)
        self.assertEqual(server.name, name_server)
        self.assertEqual(server.host, host)
        self.assertEqual(server.http_host, http_host)
        self.assertEqual(server.vods_host, vods_host)
        self.assertEqual(server.cods_host, cods_host)
        self.assertEqual(server.feedback_directory, feed)
        self.assertEqual(server.timeshifts_directory, timeshift_dir)
        self.assertEqual(server.hls_directory, hls_dir)
        self.assertEqual(server.vods_directory, vods_dir)
        self.assertEqual(server.cods_directory, cods_dir)
        self.assertEqual(server.proxy_directory, proxy_dir)
        self.assertEqual(server.monitoring, monitoring)
        self.assertEqual(server.auto_start, auto_start)
        self.assertTrue(server.is_valid())

    if __name__ == '__main__':
        unittest.main()
