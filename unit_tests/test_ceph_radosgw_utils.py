# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mock import (
    call,
    patch,
    mock_open,
    MagicMock,
)

import utils

from test_utils import CharmTestCase

TO_PATCH = [
    'application_version_set',
    'get_upstream_version',
    'format_endpoint',
    'https',
    'relation_ids',
    'relation_get',
    'related_units',
    'socket',
    'cmp_pkgrevno',
    'init_is_systemd',
]


class CephRadosGWUtilTests(CharmTestCase):
    def setUp(self):
        super(CephRadosGWUtilTests, self).setUp(utils, TO_PATCH)
        self.get_upstream_version.return_value = '10.2.2'
        self.socket.gethostname.return_value = 'testhost'

    def test_assess_status(self):
        with patch.object(utils, 'assess_status_func') as asf:
            callee = MagicMock()
            asf.return_value = callee
            utils.assess_status('test-config')
            asf.assert_called_once_with('test-config')
            callee.assert_called_once_with()
            self.get_upstream_version.assert_called_with(
                utils.VERSION_PACKAGE
            )
            self.application_version_set.assert_called_with('10.2.2')

    @patch.object(utils, 'get_optional_interfaces')
    @patch.object(utils, 'check_optional_relations')
    @patch.object(utils, 'REQUIRED_INTERFACES')
    @patch.object(utils, 'services')
    @patch.object(utils, 'make_assess_status_func')
    def test_assess_status_func(self,
                                make_assess_status_func,
                                services,
                                REQUIRED_INTERFACES,
                                check_optional_relations,
                                get_optional_interfaces):
        services.return_value = 's1'
        REQUIRED_INTERFACES.copy.return_value = {'int': ['test 1']}
        get_optional_interfaces.return_value = {'opt': ['test 2']}
        utils.assess_status_func('test-config')
        # ports=None whilst port checks are disabled.
        make_assess_status_func.assert_called_once_with(
            'test-config',
            {'int': ['test 1'], 'opt': ['test 2']},
            charm_func=check_optional_relations,
            services='s1', ports=None)

    def test_pause_unit_helper(self):
        with patch.object(utils, '_pause_resume_helper') as prh:
            utils.pause_unit_helper('random-config')
            prh.assert_called_once_with(utils.pause_unit, 'random-config')
        with patch.object(utils, '_pause_resume_helper') as prh:
            utils.resume_unit_helper('random-config')
            prh.assert_called_once_with(utils.resume_unit, 'random-config')

    @patch.object(utils, 'services')
    def test_pause_resume_helper(self, services):
        f = MagicMock()
        services.return_value = 's1'
        with patch.object(utils, 'assess_status_func') as asf:
            asf.return_value = 'assessor'
            utils._pause_resume_helper(f, 'some-config')
            asf.assert_called_once_with('some-config')
            # ports=None whilst port checks are disabled.
            f.assert_called_once_with('assessor', services='s1', ports=None)

    @patch.object(utils, 'get_keystone_client_from_relation')
    @patch.object(utils, 'is_ipv6', lambda addr: False)
    @patch.object(utils, 'get_ks_signing_cert')
    @patch.object(utils, 'get_ks_ca_cert')
    @patch.object(utils, 'mkdir')
    def test_setup_keystone_certs(self, mock_mkdir,
                                  mock_get_ks_ca_cert,
                                  mock_get_ks_signing_cert,
                                  mock_get_keystone_client):
        auth_host = 'foo/bar'
        auth_port = 80
        auth_url = 'http://%s:%s/v2.0' % (auth_host, auth_port)
        mock_ksclient = MagicMock()
        mock_ksclient.auth_endpoint = auth_url
        mock_get_keystone_client.return_value = mock_ksclient

        configs = MagicMock()
        configs.complete_contexts.return_value = ['identity-service']

        utils.setup_keystone_certs(configs)
        mock_get_ks_signing_cert.assert_has_calls([call(mock_ksclient,
                                                        auth_url,
                                                        '/var/lib/ceph/nss')])
        mock_get_ks_ca_cert.assert_has_calls([call(mock_ksclient, auth_url,
                                                   '/var/lib/ceph/nss')])

    @patch.object(utils, 'client_v3')
    @patch.object(utils, 'client')
    @patch.object(utils, 'related_units')
    @patch.object(utils, 'relation_ids')
    @patch.object(utils, 'is_ipv6', lambda addr: False)
    @patch.object(utils, 'relation_get')
    def test_get_ks_client_from_relation(self, mock_relation_get,
                                         mock_relation_ids,
                                         mock_related_units,
                                         mock_client,
                                         mock_client_v3):
        auth_host = 'foo/bar'
        auth_port = 80
        admin_token = '666'
        auth_url = 'http://%s:%s/v2.0' % (auth_host, auth_port)
        self.format_endpoint.return_value = auth_url
        mock_relation_ids.return_value = ['identity-service:5']
        mock_related_units.return_value = ['keystone/1']
        rel_data = {'auth_host': auth_host,
                    'auth_port': auth_port,
                    'admin_token': admin_token,
                    'api_version': '2'}

        mock_relation_get.return_value = rel_data
        utils.get_keystone_client_from_relation()
        mock_client.Client.assert_called_with(endpoint=auth_url,
                                              token=admin_token)

        auth_url = 'http://%s:%s/v3' % (auth_host, auth_port)
        self.format_endpoint.return_value = auth_url
        rel_data['api_version'] = '3'
        mock_relation_get.return_value = rel_data
        utils.get_keystone_client_from_relation()
        mock_client_v3.Client.assert_called_with(endpoint=auth_url,
                                                 token=admin_token)

    @patch.object(utils, 'client_v3')
    @patch.object(utils, 'client')
    @patch.object(utils, 'related_units')
    @patch.object(utils, 'relation_ids')
    @patch.object(utils, 'is_ipv6', lambda addr: False)
    @patch.object(utils, 'relation_get')
    def test_get_ks_client_from_relation_not_available(self, mock_relation_get,
                                                       mock_relation_ids,
                                                       mock_related_units,
                                                       mock_client,
                                                       mock_client_v3):
        mock_relation_ids.return_value = ['identity-service:5']
        mock_related_units.return_value = ['keystone/1']
        rel_data = {'auth_port': '5000',
                    'admin_token': 'foo',
                    'api_version': '2'}

        mock_relation_get.return_value = rel_data
        ksclient = utils.get_keystone_client_from_relation()
        self.assertIsNone(ksclient)

    @patch.object(utils, 'get_ks_cert')
    @patch.object(utils.subprocess, 'Popen')
    @patch.object(utils.subprocess, 'check_output')
    def test_get_ks_signing_cert(self, mock_check_output, mock_Popen,
                                 mock_get_ks_cert):
        auth_host = 'foo/bar'
        auth_port = 80
        admin_token = '666'
        auth_url = 'http://%s:%s/v2.0' % (auth_host, auth_port)

        m = mock_open()
        with patch.object(utils, 'open', m, create=True):

            mock_get_ks_cert.return_value = 'signing_cert_data'
            utils.get_ks_signing_cert(admin_token, auth_url, '/foo/bar')

            mock_get_ks_cert.return_value = None
            with self.assertRaises(utils.KSCertSetupException):
                utils.get_ks_signing_cert(admin_token, auth_url, '/foo/bar')

            c = ['openssl', 'x509', '-in',
                 '/foo/bar/signing_certificate.pem',
                 '-pubkey']
            mock_check_output.assert_called_with(c)

    @patch.object(utils, 'get_ks_cert')
    @patch.object(utils.subprocess, 'Popen')
    @patch.object(utils.subprocess, 'check_output')
    def test_get_ks_ca_cert(self, mock_check_output, mock_Popen,
                            mock_get_ks_cert):
        auth_host = 'foo/bar'
        auth_port = 80
        admin_token = '666'
        auth_url = 'http://%s:%s/v2.0' % (auth_host, auth_port)

        m = mock_open()
        with patch.object(utils, 'open', m, create=True):
            mock_get_ks_cert.return_value = 'ca_cert_data'
            utils.get_ks_ca_cert(admin_token, auth_url, '/foo/bar')

            mock_get_ks_cert.return_value = None
            with self.assertRaises(utils.KSCertSetupException):
                utils.get_ks_ca_cert(admin_token, auth_url, '/foo/bar')

            c = ['openssl', 'x509', '-in', '/foo/bar/ca.pem',
                 '-pubkey']
            mock_check_output.assert_called_with(c)

    def _setup_relation_data(self, data):
        self.relation_ids.return_value = data.keys()
        self.related_units.side_effect = (
            lambda rid: data[rid].keys()
        )
        self.relation_get.side_effect = (
            lambda attr, rid, unit: data[rid][unit].get(attr)
        )

    def test_systemd_based_radosgw_old_style(self):
        _relation_data = {
            'mon:1': {
                'ceph-mon/0': {
                    'radosgw_key': 'testkey',
                },
                'ceph-mon/1': {
                    'radosgw_key': 'testkey',
                },
                'ceph-mon/2': {
                    'radosgw_key': 'testkey',
                },
            }
        }
        self._setup_relation_data(_relation_data)
        self.assertFalse(utils.systemd_based_radosgw())

    def test_systemd_based_radosgw_new_style(self):
        _relation_data = {
            'mon:1': {
                'ceph-mon/0': {
                    'rgw.testhost_key': 'testkey',
                },
                'ceph-mon/1': {
                    'rgw.testhost_key': 'testkey',
                },
                'ceph-mon/2': {
                    'rgw.testhost_key': 'testkey',
                },
            }
        }
        self._setup_relation_data(_relation_data)
        self.assertTrue(utils.systemd_based_radosgw())

    def test_request_per_unit_key(self):
        self.init_is_systemd.return_value = False
        self.cmp_pkgrevno.return_value = -1
        self.assertFalse(utils.request_per_unit_key())
        self.init_is_systemd.return_value = True
        self.cmp_pkgrevno.return_value = 1
        self.assertTrue(utils.request_per_unit_key())
        self.init_is_systemd.return_value = False
        self.cmp_pkgrevno.return_value = 1
        self.assertFalse(utils.request_per_unit_key())

        self.cmp_pkgrevno.assert_called_with('radosgw', '12.2.0')

    @patch.object(utils, 'systemd_based_radosgw')
    def test_service_name(self, mock_systemd_based_radosgw):
        mock_systemd_based_radosgw.return_value = True
        self.assertEqual(utils.service_name(),
                         'ceph-radosgw@rgw.testhost')
        mock_systemd_based_radosgw.return_value = False
        self.assertEqual(utils.service_name(),
                         'radosgw')
