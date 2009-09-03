from django.test import TestCase
from django.test.client import Client

class TestStandardUrlConf(TestCase):
    def test_index(self):
        '''
        We're using the standard ROOT_URLCONF, so we need to
        pass in /zoo/, just the empty string
        '''
        c = Client()
        resp = c.get('')
        assert resp.status_code == 404, "Got status %s - expecting 404" % resp.status_code

        c = Client()
        resp = c.get('/zoo/')
        assert "Just a title" in resp.content
        assert "foobar" in resp.content

class TestCustomUrlConf(TestCase):
    urls = 'zoo.urls'

    def test_index(self):
        '''
        We're customizing the ROOT_URLCONF with zoo.urls,
        so we do *not* need to pass in /zoo/, just the empty string
        '''
        c = Client()
        resp = c.get('')
        assert "Just a title" in resp.content
        assert "foobar" in resp.content

        c = Client()
        resp = c.get('/zoo/')
        assert resp.status_code == 404, "Got status %s - expecting 404" % resp.status_code




