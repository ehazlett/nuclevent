import unittest
import application
import schema
import settings
import utils
import logging
import time

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        self.db = application.get_db_connection()
        salt = int(time.time())
        self._test_user = 'test_user_{0}'.format(salt)
        self._test_user_password = 'test123'
        self._test_user_email = '{0}@lumentica.com'.format(self._test_user)
        self._test_user_role = 'testrole_{0}'.format(salt)
        self._project_name = 'test_project_{0}'.format(salt)
        self._project_type = 'live'
        self._project_distro_id = 0
        self._project_version = '1'
        self._project_arch = 'i386'
        self._project_packages = ['blender', 'gimp']

    def test_index(self):
        resp = self.client.get('/')
        assert(resp.status_code == 200 or resp.status_code == 302)

    def test_create_user(self):
        assert utils.create_user(self._test_user, self._test_user_email, \
            self._test_user_password, self._test_user_role)
        user = utils.get_user(self._test_user)
        assert user != None
        assert user['username'] == self._test_user
        assert user['email'] == self._test_user_email
        assert user['role'] == self._test_user_role
        assert utils.delete_user(self._test_user)

    def test_create_role(self):
        assert utils.create_role(self._test_user_role)
        assert utils.delete_role(self._test_user_role)

    def test_toggle_user(self):
        assert utils.create_user(self._test_user, password=self._test_user_password, role=self._test_user_role)
        assert utils.toggle_user(self._test_user, False)
        user = utils.get_user(self._test_user)
        assert user != None
        assert user['enabled'] == False
        assert utils.toggle_user(self._test_user, True)
        user = utils.get_user(self._test_user)
        assert user != None
        assert user['enabled'] == True
        assert utils.delete_user(self._test_user)

    def tearDown(self):
        if utils.get_user(self._test_user):
            utils.delete_user(self._test_user)

if __name__=="__main__":
    unittest.main()
