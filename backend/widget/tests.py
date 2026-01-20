from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import WidgetConfig, APIKey, EmailToken
from users.models import Company, User
from leads.models import Lead

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WidgetAPITest(TestCase):
    def setUp(self):
        # Create company first
        self.company = Company.objects.create(name='Test Company')
        # Create user linked to company
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password', company=self.company)
        
        # Create Widget Config
        self.widget_config = WidgetConfig.objects.create(
            company=self.company,
            allowed_domains=['testserver', 'localhost'],
            is_active=True
        )
        
        # Generate API Keys
        self.public_key, self.secret_key = APIKey.generate_keys()
        self.api_key = APIKey.objects.create(
            company=self.company,
            name='Test Key',
            public_key=self.public_key,
            secret_key_hash=APIKey.hash_secret(self.secret_key)
        )
        
        self.client = Client()
        self.headers = {
            'HTTP_X_WIDGET_PUBLIC_KEY': self.public_key,
            'HTTP_X_WIDGET_SECRET_KEY': self.secret_key,
            'HTTP_ORIGIN': 'http://testserver' 
        }

    def test_config_view(self):
        """Test fetching widget config."""
        url = reverse('widget:config')
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['primary_color'], self.widget_config.primary_color)

    def test_auth_invalid_keys(self):
        """Test authentication with invalid keys."""
        headers = self.headers.copy()
        headers['HTTP_X_WIDGET_SECRET_KEY'] = 'wrong'
        response = self.client.get(reverse('widget:config'), **headers)
        self.assertEqual(response.status_code, 403)

    def test_origin_check(self):
        """Test origin validation."""
        headers = self.headers.copy()
        headers['HTTP_ORIGIN'] = 'http://evil.com'
        response = self.client.get(reverse('widget:config'), **headers)
        self.assertEqual(response.status_code, 403)

    @patch('leads.tasks.process_lead_task.delay')
    def test_submission_flow(self, mock_task):
        """Test full submission flow."""
        mock_task.return_value.id = 'fake-task-id'
        url = reverse('widget:submit')
        file = SimpleUploadedFile("roof.jpg", b"file_content", content_type="image/jpeg")
        
        data = {
            'email': 'customer@example.com',
            'phone': '123456789',
            'file': file
        }
        
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, 201)
        
        # Verify Lead Created
        lead = Lead.objects.get(email='customer@example.com')
        self.assertEqual(lead.source, 'widget')
        self.assertEqual(lead.widget_config, self.widget_config)
        
        # Verify Task Called
        mock_task.assert_called_once()
        
        # Verify Email Token Created
        token = EmailToken.objects.get(lead=lead)
        self.assertFalse(token.is_used)
        
        # Verify Status View
        status_url = reverse('widget:status', args=[token.token])
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'pending')
