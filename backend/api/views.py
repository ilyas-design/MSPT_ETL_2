from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Avg, Count, Sum, Q
from .models import Patient, Sante, Nutrition, ActivitePhysique, GymSession
from .serializers import PatientSerializer, SanteSerializer, NutritionSerializer, ActivitePhysiqueSerializer, GymSessionSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class SanteViewSet(viewsets.ModelViewSet):
    queryset = Sante.objects.all()
    serializer_class = SanteSerializer

class NutritionViewSet(viewsets.ModelViewSet):
    queryset = Nutrition.objects.all()
    serializer_class = NutritionSerializer

class ActivitePhysiqueViewSet(viewsets.ModelViewSet):
    queryset = ActivitePhysique.objects.all()
    serializer_class = ActivitePhysiqueSerializer

class GymSessionViewSet(viewsets.ModelViewSet):
    queryset = GymSession.objects.all()
    serializer_class = GymSessionSerializer

class KPIView(APIView):
    """Endpoint principal pour tous les KPIs"""
    def get(self, request):
        diseases = Sante.objects.values('disease_type').annotate(count=Count('disease_type'))
        avg_cholesterol = Sante.objects.aggregate(Avg('cholesterol'))['cholesterol__avg']
        severity_dist = Sante.objects.values('severity').annotate(count=Count('severity'))

        avg_calories = Nutrition.objects.aggregate(Avg('daily_caloric_intake'))['daily_caloric_intake__avg']

        avg_exercise_hours = ActivitePhysique.objects.aggregate(Avg('weekly_exercice_hours'))['weekly_exercice_hours__avg']
        activity_levels = ActivitePhysique.objects.values('physical_activity_level').annotate(count=Count('physical_activity_level'))
        
        avg_calories_burned = GymSession.objects.aggregate(Avg('gym_calories_burned'))['gym_calories_burned__avg']
        workout_types = GymSession.objects.values('gym_workout_type').annotate(count=Count('gym_workout_type'))
        
        total_patients = Patient.objects.count()
        avg_age = Patient.objects.aggregate(Avg('age'))['age__avg']
        avg_bmi = Patient.objects.aggregate(Avg('bmi_calculated'))['bmi_calculated__avg']

        return Response({
            'total_patients': total_patients,
            'avg_age': round(avg_age, 2) if avg_age else 0,
            'avg_bmi': round(avg_bmi, 2) if avg_bmi else 0,
            'sante' : {
                'diseases': list(diseases),
                'avg_cholesterol': round(avg_cholesterol, 2) if avg_cholesterol else 0,
                'severity_distribution': list(severity_dist),
            },
            'nutrition': {
                'avg_calories': round(avg_calories, 2) if avg_calories else 0,
            },
            'activite_physique': {
                'avg_exercise_hours': round(float(avg_exercise_hours), 2) if avg_exercise_hours else 0,
                'activity_levels': list(activity_levels), 
            },
            'gym':{
                'avg_calories_burned': round(avg_calories_burned, 2) if avg_calories_burned else 0,
                'workout_types': list(workout_types),
            },
        })


class EngagementKPIView(APIView):
    """KPI Engagement - participation et fréquence"""
    def get(self, request):
        total_patients = Patient.objects.count()
        active_patients = GymSession.objects.values('patient').distinct().count()
        total_sessions = GymSession.objects.count()
        avg_sessions_per_patient = total_sessions / active_patients if active_patients > 0 else 0
        
        # Engagement rate (patients avec au moins une session)
        engagement_rate = (active_patients / total_patients * 100) if total_patients > 0 else 0
        
        return Response({
            'total_patients': total_patients,
            'active_patients': active_patients,
            'engagement_rate': round(engagement_rate, 2),
            'total_sessions': total_sessions,
            'avg_sessions_per_patient': round(avg_sessions_per_patient, 2),
        })


class ConversionKPIView(APIView):
    """KPI Conversion - adhérence aux plans de régime et d'exercice"""
    def get(self, request):
        total_nutrition = Nutrition.objects.count()
        total_activity = ActivitePhysique.objects.count()
        
        # Adhérence au plan nutritionnel (conversions premium)
        high_adherence_nutrition = Nutrition.objects.filter(
            adherence_to_diet_plan__gte=0.75  # >= 75% adherence
        ).count()
        
        # Patients avec activité physique élevée (conversions premium fitness)
        high_activity = ActivitePhysique.objects.filter(
            weekly_exercice_hours__gte=3  # >= 3h par semaine
        ).count()
        
        conversion_nutrition = (high_adherence_nutrition / total_nutrition * 100) if total_nutrition > 0 else 0
        conversion_activity = (high_activity / total_activity * 100) if total_activity > 0 else 0
        
        return Response({
            'nutrition_conversion_rate': round(conversion_nutrition, 2),
            'activity_conversion_rate': round(conversion_activity, 2),
            'avg_conversion': round((conversion_nutrition + conversion_activity) / 2, 2),
            'high_adherence_nutrition': high_adherence_nutrition,
            'high_activity_patients': high_activity,
        })


class SatisfactionKPIView(APIView):
    """KPI Satisfaction - basé sur la santé et les résultats"""
    def get(self, request):
        total_patients = Patient.objects.count()
        
        # Satisfaction basée sur les métriques de santé
        healthy_cholesterol = Sante.objects.filter(
            cholesterol__gte=100, cholesterol__lte=200
        ).count()
        
        healthy_glucose = Sante.objects.filter(
            glucose__gte=70, glucose__lte=100
        ).count()
        
        # Patients sans maladie grave
        low_severity = Sante.objects.filter(
            Q(severity='Low') | Q(severity__isnull=True)
        ).count()
        
        satisfaction_score = (
            (healthy_cholesterol + healthy_glucose + low_severity) / (total_patients * 3) * 100
        ) if total_patients > 0 else 0
        
        return Response({
            'overall_satisfaction_score': round(satisfaction_score, 2),
            'healthy_cholesterol_rate': round(healthy_cholesterol / total_patients * 100, 2) if total_patients > 0 else 0,
            'healthy_glucose_rate': round(healthy_glucose / total_patients * 100, 2) if total_patients > 0 else 0,
            'low_severity_rate': round(low_severity / total_patients * 100, 2) if total_patients > 0 else 0,
        })


class DataQualityKPIView(APIView):
    """KPI Qualité des données - Data profiling"""
    def get(self, request):
        total_patients = Patient.objects.count()
        
        # Complétude des données
        complete_sante = Sante.objects.exclude(
            Q(cholesterol__isnull=True) | Q(glucose__isnull=True)
        ).count()
        
        complete_nutrition = Nutrition.objects.exclude(
            daily_caloric_intake__isnull=True
        ).count()
        
        complete_activity = ActivitePhysique.objects.exclude(
            weekly_exercice_hours__isnull=True
        ).count()
        
        # Taux de complétude par table
        completeness_sante = (complete_sante / total_patients * 100) if total_patients > 0 else 0
        completeness_nutrition = (complete_nutrition / total_patients * 100) if total_patients > 0 else 0
        completeness_activity = (complete_activity / total_patients * 100) if total_patients > 0 else 0
        
        # Score global de qualité
        overall_quality = (completeness_sante + completeness_nutrition + completeness_activity) / 3
        
        return Response({
            'overall_data_quality': round(overall_quality, 2),
            'completeness_sante': round(completeness_sante, 2),
            'completeness_nutrition': round(completeness_nutrition, 2),
            'completeness_activity': round(completeness_activity, 2),
            'total_records': {
                'patients': total_patients,
                'sante': Sante.objects.count(),
                'nutrition': Nutrition.objects.count(),
                'activite_physique': ActivitePhysique.objects.count(),
                'gym_sessions': GymSession.objects.count(),
            }
        })
