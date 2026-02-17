from django.test import TestCase

#empty file unitl finishing views 
class SmokeTest(TestCase):
    def test_exp(self):
        self.assertEqual(1 + 1, 2)
