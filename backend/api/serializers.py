from rest_framework import serializers
from .models import Patient, Sante, Nutrition, ActivitePhysique, GymSession

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model=Patient
        fields='__all__'

class SanteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Sante
        fields='__all__'

class NutritionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Nutrition
        fields='__all__'

class ActivitePhysiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model=ActivitePhysique
        fields='__all__'

class GymSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model=GymSession
        fields='__all__'


