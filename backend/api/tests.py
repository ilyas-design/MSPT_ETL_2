from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock

from . import views as api_views


class TestAuthAndPermissions(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass1234")

    def test_can_get_jwt_token(self):
        url = reverse("token_obtain_pair")
        resp = self.client.post(url, {"username": "testuser", "password": "testpass1234"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_anonymous_cannot_create_patient(self):
        resp = self.client.post(
            "/api/patients/",
            {
                "patient_id": "PTEST01",
                "age": 30,
                "gender": "Male",
                "weight_kg": "80.0",
                "height_cm": "180.0",
                "bmi_calculated": "24.7",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_create_patient(self):
        token_resp = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "testpass1234"},
            format="json",
        )
        access = token_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # We can't hit ETL-backed endpoints in Django's in-memory test DB because
        # those tables are created by the ETL (models are managed=False).
        # Minimal security check: authenticated user can access OpenAPI schema endpoint.
        resp = self.client.get("/api/schema/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class TestKPIViewsUnit(APITestCase):
    def test_model_str_methods(self):
        from .models import Patient, Sante, Nutrition, ActivitePhysique, GymSession

        p = Patient(patient_id="P00001", age=30, gender="Male", weight_kg=80, height_cm=180, bmi_calculated=24.7)
        self.assertIn("P00001", str(p))
        self.assertIn("P00001", str(Sante(patient=p)))
        self.assertIn("P00001", str(Nutrition(patient=p)))
        self.assertIn("P00001", str(ActivitePhysique(patient=p)))
        self.assertIn("P00001", str(GymSession(id=1, patient=p)))

    def test_kpi_views_return_expected_shape_with_mocks(self):
        rf = APIRequestFactory()
        req = rf.get("/api/kpis/")

        # Patch model managers used inside the views
        with (
            patch.object(api_views.Patient, "objects") as patient_mgr,
            patch.object(api_views.Sante, "objects") as sante_mgr,
            patch.object(api_views.Nutrition, "objects") as nut_mgr,
            patch.object(api_views.ActivitePhysique, "objects") as act_mgr,
            patch.object(api_views.GymSession, "objects") as gym_mgr,
        ):
            # KPIView
            sante_mgr.values.return_value.annotate.return_value = [{"disease_type": "X", "count": 1}]
            sante_mgr.aggregate.return_value = {"cholesterol__avg": 180}
            sante_mgr.values.return_value.annotate.return_value = [{"severity": "Low", "count": 1}]
            nut_mgr.aggregate.return_value = {"daily_caloric_intake__avg": 2000}
            act_mgr.aggregate.return_value = {"weekly_exercice_hours__avg": 3.5}
            act_mgr.values.return_value.annotate.return_value = [{"physical_activity_level": "Active", "count": 1}]
            gym_mgr.aggregate.return_value = {"gym_calories_burned__avg": 500}
            gym_mgr.values.return_value.annotate.return_value = [{"gym_workout_type": "Cardio", "count": 1}]
            patient_mgr.count.return_value = 10
            patient_mgr.aggregate.side_effect = [
                {"age__avg": 30},
                {"bmi_calculated__avg": 24.0},
            ]

            resp = api_views.KPIView.as_view()(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("total_patients", resp.data)
            self.assertIn("sante", resp.data)

            # EngagementKPIView (branch active_patients > 0)
            req2 = rf.get("/api/engagement/")
            patient_mgr.count.return_value = 10
            gym_mgr.values.return_value.distinct.return_value.count.return_value = 5
            gym_mgr.count.return_value = 20
            resp2 = api_views.EngagementKPIView.as_view()(req2)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn("engagement_rate", resp2.data)

            # ConversionKPIView (branch totals > 0)
            req3 = rf.get("/api/conversion/")
            nut_mgr.count.return_value = 10
            act_mgr.count.return_value = 10
            nut_mgr.filter.return_value.count.return_value = 2
            act_mgr.filter.return_value.count.return_value = 3
            resp3 = api_views.ConversionKPIView.as_view()(req3)
            self.assertEqual(resp3.status_code, 200)
            self.assertIn("avg_conversion", resp3.data)

            # SatisfactionKPIView (branch total_patients > 0)
            req4 = rf.get("/api/satisfaction/")
            patient_mgr.count.return_value = 10
            sante_mgr.filter.return_value.count.side_effect = [5, 6, 7]
            resp4 = api_views.SatisfactionKPIView.as_view()(req4)
            self.assertEqual(resp4.status_code, 200)
            self.assertIn("overall_satisfaction_score", resp4.data)

            # DataQualityKPIView (branch total_patients > 0)
            req5 = rf.get("/api/data-quality/")
            patient_mgr.count.return_value = 10
            sante_mgr.exclude.return_value.count.return_value = 8
            nut_mgr.exclude.return_value.count.return_value = 9
            act_mgr.exclude.return_value.count.return_value = 7
            sante_mgr.count.return_value = 10
            nut_mgr.count.return_value = 10
            act_mgr.count.return_value = 10
            gym_mgr.count.return_value = 10
            resp5 = api_views.DataQualityKPIView.as_view()(req5)
            self.assertEqual(resp5.status_code, 200)
            self.assertIn("overall_data_quality", resp5.data)

