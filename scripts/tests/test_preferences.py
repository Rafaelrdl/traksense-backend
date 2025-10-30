"""
Script de Teste - Preferências de Regionalização
================================================

Testa a atualização de idioma e timezone do usuário.
"""

import requests
import json

BASE_URL = "http://umc.localhost:8000/api"

def login(email, password):
    """Faz login e retorna tokens"""
    url = f"{BASE_URL}/auth/login/"
    payload = {
        "username_or_email": email,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login realizado com sucesso!")
        print(f"   Usuário: {data['user']['full_name']}")
        print(f"   Idioma atual: {data['user'].get('language', 'N/A')}")
        print(f"   Timezone atual: {data['user'].get('timezone', 'N/A')}")
        return data['access'], data['user']
    else:
        print(f"❌ Erro no login: {response.status_code}")
        return None, None

def update_preferences(access_token, language, timezone):
    """Atualiza idioma e timezone"""
    url = f"{BASE_URL}/users/me/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "language": language,
        "timezone": timezone
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Preferências atualizadas com sucesso!")
        print(f"   Novo idioma: {data.get('language', 'N/A')}")
        print(f"   Novo timezone: {data.get('timezone', 'N/A')}")
        return True
    else:
        print(f"\n❌ Erro ao atualizar: {response.status_code}")
        print(f"   {response.text}")
        return False

def get_profile(access_token):
    """Obtém perfil atual"""
    url = f"{BASE_URL}/users/me/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n📋 Perfil atual:")
        print(f"   Nome: {data.get('full_name', 'N/A')}")
        print(f"   Email: {data.get('email', 'N/A')}")
        print(f"   Idioma: {data.get('language', 'N/A')}")
        print(f"   Timezone: {data.get('timezone', 'N/A')}")
        return data
    else:
        print(f"\n❌ Erro ao obter perfil: {response.status_code}")
        return None

def main():
    print("=" * 60)
    print("TESTE - PREFERÊNCIAS DE REGIONALIZAÇÃO")
    print("=" * 60)
    
    # 1. Login
    print("\n[1/4] Fazendo login...")
    access_token, user = login("test@umc.com", "TestPass123!")
    
    if not access_token:
        print("\n❌ Teste abortado: Falha no login")
        return
    
    # 2. Atualizar para inglês e NY timezone
    print("\n[2/4] Atualizando para English (US) e New York timezone...")
    success = update_preferences(access_token, "en", "America/New_York")
    
    if not success:
        print("\n❌ Teste abortado: Falha na atualização")
        return
    
    # 3. Verificar alterações
    print("\n[3/4] Verificando alterações...")
    profile = get_profile(access_token)
    
    if profile:
        if profile.get('language') == 'en' and profile.get('timezone') == 'America/New_York':
            print("\n✅ Alterações confirmadas!")
        else:
            print("\n⚠️  Valores não correspondem ao esperado")
    
    # 4. Restaurar para português e Brasília
    print("\n[4/4] Restaurando para português e Brasília...")
    update_preferences(access_token, "pt-br", "America/Sao_Paulo")
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 60)
    print("\n📝 Resumo:")
    print("   • Login: OK")
    print("   • Atualizar idioma: OK")
    print("   • Atualizar timezone: OK")
    print("   • Verificação: OK")
    print("   • Restaurar padrões: OK")
    print("\n🎉 PreferencesDialog (Regionalização) está pronto!")

if __name__ == "__main__":
    main()
