#!/usr/bin/env python3
import unittest

from pyfastocloud_models.provider.entry import Provider
from pyfastocloud_models.service.entry import ServiceSettings, HostAndPort


class Providers(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Providers, self).__init__(*args, **kwargs)

    def test_provider_add_server(self):
        provider = Provider.make_provider(email='test@test.com', first_name='Alex', last_name='Top', password='123',
                                          country='USA', language='en')
        self.assertTrue(provider.is_valid())
        provider.add_server(None)
        self.assertEqual(provider.servers, [])

        name_server = 'Server'
        host = HostAndPort(host='localhost', port=1234)
        http_host = HostAndPort(host='localhost1', port=1235)
        vods_host = HostAndPort(host='localhost2', port=1236)
        cods_host = HostAndPort(host='localhost3', port=1237)
        nginx_host = HostAndPort(host='localhost', port=1344)
        feed = '/home/fead'
        timeshift_dir = '/home/time'
        hls_dir = '/home/tss'
        vods_dir = '/home/vods'
        cods_dir = '/home/cods'
        proxy_dir = '/hone/proxy'
        monitoring = True
        auto_start = True

        server = ServiceSettings.make_entry({ServiceSettings.NAME_FIELD: name_server,
                                             ServiceSettings.HOST_FIELD: host.to_front_dict(),
                                             ServiceSettings.HTTP_HOST_FIELD: http_host.to_front_dict(),
                                             ServiceSettings.VODS_HOST_FIELD: vods_host.to_front_dict(),
                                             ServiceSettings.CODS_HOST_FIELD: cods_host.to_front_dict(),
                                             ServiceSettings.NGINX_HOST_FIELD: nginx_host.to_front_dict(),
                                             ServiceSettings.FEEDBACK_DIRECOTRY_FIELD: feed,
                                             ServiceSettings.TIMESHIFTS_DIRECTORY_FIELD: timeshift_dir,
                                             ServiceSettings.HLS_DIRECTORY_FIELD: hls_dir,
                                             ServiceSettings.VODS_DIRECTORY_FIELD: vods_dir,
                                             ServiceSettings.CODS_DIRECTORY_FIELD: cods_dir,
                                             ServiceSettings.PROXY_DIRECTORY_FIELD: proxy_dir,
                                             ServiceSettings.MONITORING_FILED: monitoring,
                                             ServiceSettings.AUTO_START_FIELD: auto_start})
        self.assertTrue(server.is_valid())
        provider.add_server(server)
        self.assertTrue(provider.servers, [server])


if __name__ == '__main__':
    unittest.main()
