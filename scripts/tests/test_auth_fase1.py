#!/usr/bin/env python3
"""
Script de teste para validar os endpoints de autenticação da FASE 1.
"""

import json
import requests
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"
TENANT_HOST = "umc.localhost"
HEADERS = {
    "Host": TENANT_HOST,
    "Content-Type": "application/json"
}

def print_section(title):
    """Print section divider."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test health check endpoint."""
    print_section("1. Health Check")
    
    response = requests.get(
        f"{BASE_URL}/api/health/",
        headers={"Host": TENANT_HOST}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_register():
    """Test user registration."""
    print_section("2. User Registration")
    
    data = {
        "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%H%M%S')}@umc.com",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register/",
        headers=HEADERS,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ User created: {result['user']['email']}")
        print(f"✅ Access token received: {result['access'][:50]}...")
        print(f"✅ Refresh token received: {result['refresh'][:50]}...")
        return result
    else:
        print(f"❌ Error response text: {response.text[:500]}")
        try:
            print(f"❌ Error JSON: {response.json()}")
        except:
            pass
        return None

def test_login(email, password):
    """Test user login."""
    print_section("3. User Login")
    
    data = {
        "username_or_email": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        headers=HEADERS,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Login successful: {result['user']['full_name']}")
        print(f"✅ Access token: {result['access'][:50]}...")
        return result
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_profile(access_token):
    """Test get profile endpoint."""
    print_section("4. Get Profile")
    
    headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/users/me/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Profile retrieved:")
        print(f"   Name: {user['full_name']}")
        print(f"   Email: {user['email']}")
        print(f"   Username: {user['username']}")
        print(f"   Initials: {user['initials']}")
        return user
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_update_profile(access_token):
    """Test update profile endpoint."""
    print_section("5. Update Profile")
    
    headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "phone": "+55 11 98765-4321",
        "bio": "Desenvolvedor Full Stack apaixonado por IoT",
        "timezone": "America/Sao_Paulo"
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/users/me/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Profile updated:")
        print(f"   Phone: {result['user']['phone']}")
        print(f"   Bio: {result['user']['bio']}")
        return True
    else:
        print(f"❌ Error: {response.json()}")
        return False

def test_token_refresh(refresh_token):
    """Test token refresh endpoint."""
    print_section("6. Token Refresh")
    
    data = {
        "refresh": refresh_token
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/token/refresh/",
        headers=HEADERS,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ New access token: {result['access'][:50]}...")
        # Note: Without token rotation, refresh token is not rotated
        if 'refresh' in result:
            print(f"✅ New refresh token: {result['refresh'][:50]}...")
        else:
            print(f"ℹ️ Refresh token not rotated (ROTATE_REFRESH_TOKENS=False)")
            result['refresh'] = refresh_token  # Keep the same
        return result
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_logout(access_token, refresh_token):
    """Test logout endpoint."""
    print_section("7. Logout")
    
    headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "refresh_token": refresh_token
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/logout/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        return True
    else:
        print(f"❌ Error: {response.json()}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  🧪 FASE 1 - AUTENTICAÇÃO - TESTES DE VALIDAÇÃO")
    print("="*60)
    
    try:
        # 1. Health Check
        if not test_health_check():
            print("❌ Health check failed!")
            return
        
        # 2. Register
        register_result = test_register()
        if not register_result:
            print("❌ Registration failed!")
            return
        
        email = register_result['user']['email']
        password = "TestPass123!"
        access_token = register_result['access']
        refresh_token = register_result['refresh']
        
        # 3. Login
        login_result = test_login(email, password)
        if not login_result:
            print("❌ Login failed!")
            return
        
        access_token = login_result['access']
        
        # 4. Get Profile
        if not test_profile(access_token):
            print("❌ Get profile failed!")
            return
        
        # 5. Update Profile
        if not test_update_profile(access_token):
            print("❌ Update profile failed!")
            return
        
        # 6. Token Refresh
        refresh_result = test_token_refresh(refresh_token)
        if not refresh_result:
            print("❌ Token refresh failed!")
            return
        
        # Use new tokens
        access_token = refresh_result['access']
        refresh_token = refresh_result['refresh']
        
        # 7. Logout
        if not test_logout(access_token, refresh_token):
            print("❌ Logout failed!")
            return
        
        # Final summary
        print_section("✅ TODOS OS TESTES PASSARAM!")
        print("📊 Resultados:")
        print("   ✅ Health Check")
        print("   ✅ User Registration")
        print("   ✅ User Login")
        print("   ✅ Get Profile")
        print("   ✅ Update Profile")
        print("   ✅ Token Refresh")
        print("   ✅ Logout")
        print("\n🎉 FASE 1 VALIDADA COM SUCESSO!\n")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
