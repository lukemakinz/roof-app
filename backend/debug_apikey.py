
import os
import django
import sys

# Set up Django environment
sys.path.append('/Users/lukaszmakinia/Desktop/roof-app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from widget.models import APIKey
from users.models import User, Company

def test_api_key_creation():
    print("--- Starting API Key Creation Test ---")
    
    # 1. Get or Create User
    user, created = User.objects.get_or_create(username='debug_user', defaults={'email': 'debug@example.com'})
    print(f"User: {user} (Created: {created})")
    
    # 2. Simulate View Logic for Company
    if not user.company:
        print("User has no company, creating one...")
        company_name = f"Firma {user.first_name or user.username}"
        company = Company.objects.create(name=company_name)
        user.company = company
        user.save(update_fields=['company'])
        print(f"Created company: {company}")
    else:
        print(f"User has company: {user.company}")
        
    company = user.company
    
    # 3. Generate Keys
    try:
        public_key, secret_key = APIKey.generate_keys()
        print(f"Generated Keys: Pub={public_key}, Sec={secret_key[:5]}...")
    except Exception as e:
        print(f"ERROR generating keys: {e}")
        return

    # 4. Create API Key
    try:
        api_key = APIKey.objects.create(
            company=company,
            name="Debug Key",
            public_key=public_key,
            secret_key_hash=APIKey.hash_secret(secret_key)
        )
        print(f"SUCCESS: Created API Key ID={api_key.id}")
    except Exception as e:
        print(f"ERROR creating API Key object: {e}")

if __name__ == "__main__":
    test_api_key_creation()
