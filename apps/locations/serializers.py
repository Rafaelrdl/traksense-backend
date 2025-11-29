"""
Serializers para Locations
"""

from rest_framework import serializers

from .models import Company, Sector, Subsection, LocationContact


class LocationContactSerializer(serializers.ModelSerializer):
    """Serializer para contatos."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = LocationContact
        fields = [
            'id', 'type', 'type_display', 'name', 
            'phone', 'email', 'note', 'created_at'
        ]


class SubsectionSerializer(serializers.ModelSerializer):
    """Serializer completo para subseções."""
    
    company_id = serializers.IntegerField(source='sector.company_id', read_only=True)
    company_name = serializers.CharField(source='sector.company.name', read_only=True)
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    full_path = serializers.CharField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    contacts = LocationContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subsection
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'sector', 'sector_name', 'company_id', 'company_name',
            'position', 'reference', 'full_path', 'asset_count',
            'contacts', 'created_at', 'updated_at'
        ]


class SubsectionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de subseções."""
    
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    company_name = serializers.CharField(source='sector.company.name', read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Subsection
        fields = [
            'id', 'name', 'code', 'is_active',
            'sector', 'sector_name', 'company_name', 'asset_count'
        ]


class SectorSerializer(serializers.ModelSerializer):
    """Serializer completo para setores."""
    
    # Campos explícitos opcionais
    code = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    floor = serializers.CharField(required=False, allow_blank=True, max_length=20)
    building = serializers.CharField(required=False, allow_blank=True, max_length=100)
    area = serializers.CharField(required=False, allow_blank=True, max_length=100)
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    full_path = serializers.CharField(read_only=True)
    subsection_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    subsections = SubsectionListSerializer(many=True, read_only=True)
    contacts = LocationContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sector
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'company', 'company_name', 'supervisor', 'supervisor_name',
            'floor', 'building', 'area', 'full_path',
            'subsection_count', 'asset_count', 'subsections',
            'contacts', 'created_at', 'updated_at'
        ]


class SectorListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de setores."""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    subsection_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Sector
        fields = [
            'id', 'name', 'code', 'is_active',
            'company', 'company_name', 'subsection_count', 'asset_count'
        ]


class SectorNestedSerializer(serializers.ModelSerializer):
    """Serializer de setor com subseções aninhadas para árvore."""
    
    subsections = SubsectionListSerializer(many=True, read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Sector
        fields = [
            'id', 'name', 'code', 'is_active',
            'asset_count', 'subsections'
        ]


class CompanySerializer(serializers.ModelSerializer):
    """Serializer completo para empresas."""
    
    # Campos explícitos opcionais
    code = serializers.CharField(required=False, allow_blank=True, max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    cnpj = serializers.CharField(required=False, allow_blank=True, max_length=18)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    state = serializers.CharField(required=False, allow_blank=True, max_length=50)  # Aumentado para suportar nome completo
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    sector_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    sectors = SectorListSerializer(many=True, read_only=True)
    contacts = LocationContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'cnpj', 'address', 'city', 'state', 'phone', 'email',
            'logo', 'timezone', 'manager', 'manager_name',
            'sector_count', 'asset_count', 'sectors',
            'contacts', 'created_at', 'updated_at'
        ]


class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de empresas."""
    
    sector_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'code', 'city', 'state', 'is_active',
            'sector_count', 'asset_count'
        ]


class CompanyTreeSerializer(serializers.ModelSerializer):
    """Serializer para árvore hierárquica completa."""
    
    sectors = SectorNestedSerializer(many=True, read_only=True)
    sector_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'code', 'is_active',
            'sector_count', 'asset_count', 'sectors'
        ]


class LocationTreeResponseSerializer(serializers.Serializer):
    """Serializer para resposta da árvore de localizações."""
    
    companies = CompanyTreeSerializer(many=True)
    total_companies = serializers.IntegerField()
    total_sectors = serializers.IntegerField()
    total_subsections = serializers.IntegerField()
    total_assets = serializers.IntegerField()
