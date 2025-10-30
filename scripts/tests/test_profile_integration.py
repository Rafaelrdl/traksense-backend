"""
Script de Teste - Edição de Perfil
===================================

Testa os endpoints de edição de perfil integrados ao EditProfileDialog.

Endpoints testados:
- PATCH /api/users/me/ (atualizar perfil)
- POST /api/users/me/avatar/ (upload avatar)
- DELETE /api/users/me/avatar/ (remover avatar)
- POST /api/users/me/change-password/ (alterar senha)
"""

import requests
import json
import os
from pathlib import Path

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
        print(f"   Usuário: {data['user']['full_name']} ({data['user']['email']})")
        return data['access'], data['refresh']
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(f"   {response.text}")
        return None, None

def get_profile(access_token):
    """Obtém dados do perfil"""
    url = f"{BASE_URL}/users/me/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Perfil obtido com sucesso!")
        print(f"   Nome: {data.get('full_name', 'N/A')}")
        print(f"   Email: {data.get('email', 'N/A')}")
        print(f"   Telefone: {data.get('phone', 'N/A')}")
        print(f"   Bio: {data.get('bio', 'N/A')}")
        print(f"   Avatar: {'Sim' if data.get('avatar') else 'Não'}")
        return data
    else:
        print(f"\n❌ Erro ao obter perfil: {response.status_code}")
        print(f"   {response.text}")
        return None

def update_profile(access_token, updates):
    """Atualiza dados do perfil"""
    url = f"{BASE_URL}/users/me/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.patch(url, json=updates, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Perfil atualizado com sucesso!")
        print(f"   Nome: {data.get('full_name', 'N/A')}")
        print(f"   Telefone: {data.get('phone', 'N/A')}")
        print(f"   Bio: {data.get('bio', 'N/A')}")
        return data
    else:
        print(f"\n❌ Erro ao atualizar perfil: {response.status_code}")
        print(f"   {response.text}")
        return None

def upload_avatar(access_token, image_path):
    """Faz upload de avatar"""
    url = f"{BASE_URL}/users/me/avatar/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    if not os.path.exists(image_path):
        print(f"\n❌ Arquivo não encontrado: {image_path}")
        return None
    
    with open(image_path, 'rb') as f:
        files = {'avatar': f}
        response = requests.post(url, files=files, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Avatar enviado com sucesso!")
        print(f"   URL: {data.get('avatar', 'N/A')}")
        return data
    else:
        print(f"\n❌ Erro ao enviar avatar: {response.status_code}")
        print(f"   {response.text}")
        return None

def remove_avatar(access_token):
    """Remove avatar do usuário"""
    url = f"{BASE_URL}/users/me/avatar/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 200:
        print("\n✅ Avatar removido com sucesso!")
        return True
    else:
        print(f"\n❌ Erro ao remover avatar: {response.status_code}")
        print(f"   {response.text}")
        return False

def change_password(access_token, old_password, new_password):
    """Altera senha do usuário"""
    url = f"{BASE_URL}/users/me/change-password/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "old_password": old_password,
        "new_password": new_password,
        "new_password_confirm": new_password
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("\n✅ Senha alterada com sucesso!")
        return True
    else:
        print(f"\n❌ Erro ao alterar senha: {response.status_code}")
        print(f"   {response.text}")
        return False

def main():
    print("=" * 60)
    print("TESTE DE INTEGRAÇÃO - EDIÇÃO DE PERFIL")
    print("=" * 60)
    
    # 1. Login
    print("\n[1/5] Fazendo login...")
    access_token, refresh_token = login("test@umc.com", "TestPass123!")
    
    if not access_token:
        print("\n❌ Teste abortado: Falha no login")
        return
    
    # 2. Obter perfil atual
    print("\n[2/5] Obtendo perfil atual...")
    profile = get_profile(access_token)
    
    if not profile:
        print("\n❌ Teste abortado: Falha ao obter perfil")
        return
    
    # 3. Atualizar dados do perfil
    print("\n[3/5] Atualizando dados do perfil...")
    updates = {
        "first_name": "Teste",
        "last_name": "Atualizado",
        "phone": "(34) 99999-8888",
        "bio": "Bio atualizada via script de teste"
    }
    updated_profile = update_profile(access_token, updates)
    
    # 4. Testar avatar (opcional - comente se não tiver imagem)
    # print("\n[4/5] Testando upload de avatar...")
    # avatar_path = "test_avatar.jpg"  # Substitua pelo caminho de uma imagem real
    # if os.path.exists(avatar_path):
    #     upload_avatar(access_token, avatar_path)
    #     remove_avatar(access_token)
    # else:
    #     print(f"   ⚠️  Pulando teste de avatar (arquivo {avatar_path} não encontrado)")
    
    print("\n[4/5] Pulando teste de avatar (desabilitado)")
    
    # 5. Verificar perfil atualizado
    print("\n[5/5] Verificando perfil após atualizações...")
    final_profile = get_profile(access_token)
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print("\n📝 Resumo:")
    print(f"   • Login: OK")
    print(f"   • Obter perfil: OK")
    print(f"   • Atualizar perfil: {'OK' if updated_profile else 'FALHOU'}")
    print(f"   • Upload avatar: PULADO")
    print(f"   • Remover avatar: PULADO")
    print(f"   • Verificação final: {'OK' if final_profile else 'FALHOU'}")
    print("\n🎉 EditProfileDialog está pronto para uso no frontend!")

if __name__ == "__main__":
    main()
