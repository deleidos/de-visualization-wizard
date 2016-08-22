import unittest

from pyramid import testing


class TLPViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from .views import home

        request = testing.DummyRequest()
        response = home(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Visit', response.body)

    def test_hello(self):
        from .views import hello

        request = testing.DummyRequest()
        response = hello(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Go back', response.body)
    # def test_setmodel(self):
    #     pass