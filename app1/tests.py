

from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Party

class PartyCRUDTests(TestCase):
    
    def setUp(self):
        
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_party_creation_successful(self):
        """
        Test that a logged-in user can successfully create a new party.
        """
        
        response = self.client.get(reverse('parties:create'))
        self.assertEqual(response.status_code, 200) 

    
        party_data = {
            'name': 'Test Party A',
            'city': 'Ahmedabad',
            'state': 'Gujarat'
        }
        response = self.client.post(reverse('parties:create'), data=party_data)

        
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, reverse('parties:list'))

        
        self.assertTrue(Party.objects.filter(name='Test Party A').exists())
        
        
        self.assertEqual(Party.objects.count(), 1)