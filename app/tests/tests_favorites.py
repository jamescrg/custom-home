from pprint import pprint

from django.test import TestCase
from django.test import TransactionTestCase
from django.test import Client
from django.urls import reverse

from accounts.models import CustomUser
from app.models import Folder, Favorite


class ModelTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            'john', 'lennon@thebeatles.com', 'johnpassword'
        )
        self.client.login(username='john', password='johnpassword')

        Favorite.objects.create(
            user_id=1,
            folder_id=1,
            name='Meditation Posture',
            url='http://meditationposture.net',
            description='A website',
            login='drachma',
            root='rupee',
            passkey='ruble',
            selected=1,
        )

    def testFavorite(self):
        favorite = Favorite.objects.get(name="Meditation Posture")
        expectedValues = {
            'user_id': 1,
            'folder_id': 1,
            'name': 'Meditation Posture',
            'url': 'http://meditationposture.net',
            'description': 'A website',
            'login': 'drachma',
            'root': 'rupee',
            'passkey': 'ruble',
            'selected': 1,
        }
        for key, val in expectedValues.items():
            with self.subTest(key=key, val=val):
                self.assertEqual(getattr(favorite, key), val)

    def testFavoriteString(self):
        favorite = Favorite.objects.get(name="Meditation Posture")
        self.assertEqual(str(favorite), f'{favorite.name} : {favorite.id}')


class ViewTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            'john', 'lennon@thebeatles.com', 'johnpassword'
        )
        self.client.login(username='john', password='johnpassword')

        folders = [
            'Main',
            'Dev',
            'Fun',
            'Local',
        ]

        for name in folders:
            user_id = self.user.id
            Folder.objects.create(
                user_id=user_id,
                page='contacts',
                name=name,
            )

        favorites = [
            {
                'name': 'Google',
                'url': 'https://go.com',
            },
            {
                'name': 'Yahoo',
                'url': 'https://go.com',
            },
            {
                'name': 'Bing',
                'url': 'https://go.com',
            },
        ]

        for favorite in favorites:
            Favorite.objects.create(
                user_id=1,
                folder_id=1,
                selected=0,
                name=favorite['name'],
                url=favorite['url'],
            )

    def testIndex(self):
        response = self.client.get('/favorites/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('favorites'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('favorites'))
        self.assertTemplateUsed(response, 'favorites/content.html')

    def testAdd(self):
        response = self.client.get('/favorites/add/4')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'favorites/form.html')

    def testEdit(self):
        response = self.client.get('/favorites/edit/2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'favorites/form.html')

    def testInsert(self):
        data = {
            'user_id': 1,
            'folder_id': 4,
            'name': 'Reddit',
            'url': 'https://reddit.com',
        }

        response = self.client.post('/favorites/insert', data)
        self.assertEqual(response.status_code, 302)
        found = Favorite.objects.filter(name='Reddit').exists()
        self.assertTrue(found)

    def testUpdate(self):
        data = {
            'user_id': self.user.id,
            'folder_id': 4,
            'name': 'Reddit',
            'url': 'https://reddit.com',
        }

        response = self.client.post('/favorites/update/2', data)
        self.assertEqual(response.status_code, 302)
        found = Favorite.objects.filter(name='Reddit').exists()
        self.assertTrue(found)

    def testDelete(self):
        response = self.client.get('/favorites/delete/3')
        self.assertEqual(response.status_code, 302)
        found = Favorite.objects.filter(name='Bing').exists()
        self.assertFalse(found)

    def testHome(self):
        response = self.client.get('/favorites/home/2')
        self.assertEqual(response.status_code, 302)
        favorite = Favorite.objects.filter(pk=2).get()
        self.assertEqual(favorite.home_rank, 1)
