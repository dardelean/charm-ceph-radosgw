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

from mock import patch, call

import ceph_rgw as ceph  # noqa
import utils  # noqa

from test_utils import CharmTestCase  # noqa

TO_PATCH = [
    'config',
    'os',
    'subprocess',
    'mkdir',
    'service_name',
]


class CephRadosGWCephTests(CharmTestCase):
    def setUp(self):
        super(CephRadosGWCephTests, self).setUp(ceph, TO_PATCH)
        self.config.side_effect = self.test_config.get
        self.service_name.return_value = 'ceph-radosgw'

    def test_import_radosgw_key(self):
        self.os.path.exists.return_value = False
        self.os.path.join.return_value = '/etc/ceph/keyring.rados.gateway'
        ceph.import_radosgw_key('mykey')
        cmd = [
            'ceph-authtool',
            '/etc/ceph/keyring.rados.gateway',
            '--create-keyring',
            '--name=client.radosgw.gateway',
            '--add-key=mykey'
        ]
        self.subprocess.check_call.assert_has_calls([
            call(cmd),
            call(['chown', 'root:root',
                  '/etc/ceph/keyring.rados.gateway'])
        ])

    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_create_pool')
    def test_create_rgw_pools_rq_with_prefix(self, mock_broker):
        self.test_config.set('rgw-lightweight-pool-pg-num', 10)
        self.test_config.set('ceph-osd-replication-count', 3)
        self.test_config.set('rgw-buckets-pool-weight', 19)
        ceph.get_create_rgw_pools_rq(prefix='us-east')
        mock_broker.assert_has_calls([
            call(replica_count=3, weight=19, name='us-east.rgw.buckets.data',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.control',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.data.root',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.gc',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.log',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.intent-log',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.meta',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.usage',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.users.keys',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.users.email',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.users.swift',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.users.uid',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.buckets.extra',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='us-east.rgw.buckets.index',
                 group='objects', app_name='rgw'),
            call(pg_num=10, replica_count=3, name='.rgw.root',
                 group='objects', app_name='rgw')],
        )

    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_request_access_to_group')
    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_create_pool')
    def test_create_rgw_pools_rq_no_prefix_post_jewel(self, mock_broker,
                                                      mock_request_access):
        self.test_config.set('rgw-lightweight-pool-pg-num', -1)
        self.test_config.set('ceph-osd-replication-count', 3)
        self.test_config.set('rgw-buckets-pool-weight', 19)
        self.test_config.set('restrict-ceph-pools', True)
        ceph.get_create_rgw_pools_rq(prefix=None)
        mock_broker.assert_has_calls([
            call(replica_count=3, weight=19, name='default.rgw.buckets.data',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.control',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.data.root',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.gc',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.log',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.intent-log',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.meta',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.usage',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.keys',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.email',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.swift',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.uid',
                 group='objects', app_name='rgw'),
            call(weight=1.00, replica_count=3,
                 name='default.rgw.buckets.extra',
                 group='objects', app_name='rgw'),
            call(weight=3.00, replica_count=3,
                 name='default.rgw.buckets.index',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='.rgw.root',
                 group='objects', app_name='rgw')],
        )
        mock_request_access.assert_called_with(key_name='radosgw.gateway',
                                               name='objects',
                                               permission='rwx')

    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_create_erasure_profile')
    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_create_erasure_pool')
    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_request_access_to_group')
    @patch('charmhelpers.contrib.storage.linux.ceph.CephBrokerRq'
           '.add_op_create_pool')
    def test_create_rgw_pools_rq_no_prefix_ec(self, mock_broker,
                                              mock_request_access,
                                              mock_request_create_ec_pool,
                                              mock_request_create_ec_profile):
        self.test_config.set('rgw-lightweight-pool-pg-num', -1)
        self.test_config.set('ceph-osd-replication-count', 3)
        self.test_config.set('rgw-buckets-pool-weight', 19)
        self.test_config.set('restrict-ceph-pools', True)
        self.test_config.set('pool-type', 'erasure-coded')
        self.test_config.set('ec-profile-k', 3)
        self.test_config.set('ec-profile-m', 9)
        self.test_config.set('ec-profile-technique', 'cauchy_good')
        ceph.get_create_rgw_pools_rq(prefix=None)
        mock_request_create_ec_profile.assert_called_once_with(
            name='ceph-radosgw-profile',
            k=3, m=9,
            lrc_locality=None,
            lrc_crush_locality=None,
            shec_durability_estimator=None,
            clay_helper_chunks=None,
            clay_scalar_mds=None,
            device_class=None,
            erasure_type='jerasure',
            erasure_technique='cauchy_good'
        )
        mock_request_create_ec_pool.assert_has_calls([
            call(name='default.rgw.buckets.data',
                 erasure_profile='ceph-radosgw-profile',
                 weight=19,
                 group="objects",
                 app_name='rgw')
        ])
        mock_broker.assert_has_calls([
            call(weight=0.10, replica_count=3, name='default.rgw.control',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.data.root',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.gc',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.log',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.intent-log',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.meta',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.usage',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.keys',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.email',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.swift',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='default.rgw.users.uid',
                 group='objects', app_name='rgw'),
            call(weight=1.00, replica_count=3,
                 name='default.rgw.buckets.extra',
                 group='objects', app_name='rgw'),
            call(weight=3.00, replica_count=3,
                 name='default.rgw.buckets.index',
                 group='objects', app_name='rgw'),
            call(weight=0.10, replica_count=3, name='.rgw.root',
                 group='objects', app_name='rgw')],
        )
        mock_request_access.assert_called_with(key_name='radosgw.gateway',
                                               name='objects',
                                               permission='rwx')

    @patch.object(utils.apt_pkg, 'version_compare', lambda *args: -1)
    @patch.object(utils, 'lsb_release',
                  lambda: {'DISTRIB_CODENAME': 'trusty'})
    @patch.object(utils, 'add_source')
    @patch.object(utils, 'apt_update')
    @patch.object(utils, 'apt_install')
    def test_setup_ipv6_install_backports(self, mock_add_source,
                                          mock_apt_update,
                                          mock_apt_install):
        utils.setup_ipv6()
        self.assertTrue(mock_apt_update.called)
        self.assertTrue(mock_apt_install.called)

    @patch.object(utils.apt_pkg, 'version_compare', lambda *args: 0)
    @patch.object(utils, 'lsb_release',
                  lambda: {'DISTRIB_CODENAME': 'trusty'})
    @patch.object(utils, 'add_source')
    @patch.object(utils, 'apt_update')
    @patch.object(utils, 'apt_install')
    def test_setup_ipv6_not_install_backports(self, mock_add_source,
                                              mock_apt_update,
                                              mock_apt_install):
        utils.setup_ipv6()
        self.assertFalse(mock_apt_update.called)
        self.assertFalse(mock_apt_install.called)
