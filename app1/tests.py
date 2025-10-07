# app1/tests.py

from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Party

class PartyCRUDTests(TestCase):
    
    def setUp(self):
        # Har test se pehle ek user banayein
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_party_creation_successful(self):
        """
        Test that a logged-in user can successfully create a new party.
        """
        # Party create page ko access karein (GET request)
        response = self.client.get(reverse('parties:create'))
        self.assertEqual(response.status_code, 200) # Check page loads successfully

        # Nayi party ke liye data post karein (POST request)
        party_data = {
            'name': 'Test Party A',
            'city': 'Ahmedabad',
            'state': 'Gujarat'
        }
        response = self.client.post(reverse('parties:create'), data=party_data)

        # Check ki party create hone ke baad list page par redirect hua
        self.assertEqual(response.status_code, 302) # 302 is the status code for redirect
        self.assertRedirects(response, reverse('parties:list'))

        # Check ki database mein party astitva mein hai
        self.assertTrue(Party.objects.filter(name='Test Party A').exists())
        
        # Check ki kul parties ki sankhya 1 hai
        self.assertEqual(Party.objects.count(), 1)