from pprint import pprint

from django.test import TestCase
from django.test import TransactionTestCase
from django.test import Client
from django.urls import reverse
from django.shortcuts import get_object_or_404

from accounts.models import CustomUser
from apps.folders.models import Folder
from apps.contacts.models import Contact


class ModelTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            'john', 'lennon@thebeatles.com', 'johnpassword'
        )
        self.client.login(username='john', password='johnpassword')

        folder1 = Folder.objects.create(
            user=self.user,
            page='contacts',
            name='mahatmas',
        )

        Contact.objects.create(
            user=self.user,
            folder=folder1,
            selected=1,
            name='Mohandas Gandhi',
            company='Gandhi, PC',
            address='225 Paper Street, Porbandar, India',
            phone1='123.456.7890',
            phone1_label='Work',
            phone2='123.456.2222',
            phone2_label='Mobile',
            phone3='123.456.5555',
            phone3_label='Other',
            email='gandhi@gandhi.com',
            website='gandhi.com',
            notes='The Mahatma',
        )

    def testContactContent(self):
        contact = Contact.objects.get(name='Mohandas Gandhi')
        expectedValues = {
            'name': 'Mohandas Gandhi',
            'company': 'Gandhi, PC',
            'address': '225 Paper Street, Porbandar, India',
            'phone1': '123.456.7890',
            'phone1_label': 'Work',
            'phone2': '123.456.2222',
            'phone2_label': 'Mobile',
            'phone3': '123.456.5555',
            'phone3_label': 'Other',
            'email': 'gandhi@gandhi.com',
            'website': 'gandhi.com',
            'notes': 'The Mahatma',
        }
        for key, val in expectedValues.items():
            with self.subTest(key=key, val=val):
                self.assertEqual(getattr(contact, key), val)

    def testContactString(self):
        contact = Contact.objects.get(name='Mohandas Gandhi')
        self.assertEqual(str(contact), f'{contact.name} : {contact.id}')


class ViewTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            'john', 'lennon@thebeatles.com', 'johnpassword'
        )
        self.client.login(username='john', password='johnpassword')

        folders = [
            'Friends',
            'Family',
            'Medical',
            'Work',
        ]

        for name in folders:
            user_id = self.user.id
            Folder.objects.create(
                user_id=user_id,
                page='contacts',
                name=name,
            )

        self.first_folder = Folder.objects.all().first()
        self.first_folder.selected = 1
        self.first_folder.save()

        contacts = [
            {'name': 'Socrates', 'phone1': '406.363.5555', 'email': 'u@me.com'},
            {'name': 'Nietzsche', 'phone1': '406.363.5555', 'email': 'u@me.com'},
            {'name': 'Schopenhauer', 'phone1': '406.363.5555', 'email': 'u@me.com'},
        ]

        for contact in contacts:
            Contact.objects.create(
                user_id=1,
                folder=self.first_folder,
                selected=0,
                name=contact['name'],
                phone1=contact['phone1'],
                email=contact['email'],
            )

        Contact.objects.filter(name='Socrates').update(selected=1)

    def testIndex(self):
        response = self.client.get('/contacts/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('contacts'))
        self.assertTemplateUsed(response, 'contacts/content.html')

    def testSelect(self):
        response = self.client.get('/contacts/2')
        self.assertEqual(response.status_code, 302)
        selected_contact = get_object_or_404(Contact, pk=2)
        self.assertEqual(selected_contact.selected, 1)

    def testAdd(self):
        response = self.client.get('/contacts/add')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts/form.html')

    def testAddData(self):
        data = {
            'user_id': self.user.id,
            'folder': 4,
            'name': 'Plato',
            'phone1': '440.500.6000',
        }
        response = self.client.post('/contacts/add', data)
        self.assertEqual(response.status_code, 302)
        found = Contact.objects.filter(name='Plato').exists()
        self.assertTrue(found)

    def testEdit(self):
        response = self.client.get('/contacts/2/edit')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contacts/form.html')

    def testEditData(self):
        data = {
            'user_id': self.user.id,
            'folder': 4,
            'name': 'Descartes',
            'phone1': '440.500.6000',
        }

        response = self.client.post('/contacts/2/edit', data)
        self.assertEqual(response.status_code, 302)
        found = Contact.objects.filter(name='Descartes').exists()
        self.assertTrue(found)

    def testDelete(self):
        response = self.client.get('/contacts/3/delete')
        self.assertEqual(response.status_code, 302)
        found = Contact.objects.filter(name='Schopenhauer').exists()
        self.assertFalse(found)