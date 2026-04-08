import { useEffect, useState } from "react";

import { apiService } from "../services/api";
import StatCard from "../components/StatCard";

function Dashboard() {
    const [kpis, setKpis] = useState(null);
    const [engagement, setEngagement] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [kpi, eng] = await Promise.all([
                apiService.getKPIs(),
                apiService.getEngagementKPIs(),
            ]);
            setKpis(kpi.data);
            setEngagement(eng.data);
            setLoading(false);
        } catch (err) {
            setError("Erreur lors du chargement des données");
            setLoading(false);
        }
    };

    if (loading) return <div className="loading">Chargement...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="dashboard">
            <h2>📊 Vue d'ensemble</h2>

            <div className="kpi-grid">
                <StatCard
                    icon="👥"
                    title="Total Patients"
                    value={kpis?.total_patients || 0}
                />
                <StatCard
                    icon="🎂"
                    title="Âge moyen"
                    value={kpis?.avg_age?.toFixed(1) || 0}
                    unit="ans"
                />
                <StatCard
                    icon="⚖️"
                    title="BMI moyen"
                    value={kpis?.avg_bmi?.toFixed(2) || 0}
                />
                <StatCard
                    icon="❤️"
                    title="Cholestérol moyen"
                    value={kpis?.sante?.avg_cholesterol?.toFixed(0) || 0}
                    unit="mg/dL"
                />
            </div>

            <h2 style={{ marginTop: "3rem" }}>📈 Engagement</h2>

            <div className="kpi-grid">
                <StatCard
                    icon="💪"
                    title="Patients actifs"
                    value={engagement?.active_patients || 0}
                    color="#48bb78"
                />
                <StatCard
                    icon="🎯"
                    title="Taux engagement"
                    value={engagement?.engagement_rate?.toFixed(1) || 0}
                    unit="%"
                    color="#48bb78"
                />
                <StatCard
                    icon="🏋️"
                    title="Sessions moyennes"
                    value={engagement?.avg_sessions_per_patient?.toFixed(1) || 0}
                    unit="par patient"
                    color="#48bb78"
                />
                <StatCard
                    icon="📊"
                    title="Total sessions"
                    value={engagement?.total_sessions || 0}
                    color="#48bb78"
                />
            </div>

            <h2 style={{ marginTop: "3rem" }}>🥗 Nutrition</h2>

            <div className="kpi-grid">
                <StatCard
                    icon="🍽️"
                    title="Calories moyennes"
                    value={kpis?.nutrition?.avg_calories?.toFixed(0) || 0}
                    unit="kcal/jour"
                    color="#4facfe"
                />
                <StatCard
                    icon="⏱️"
                    title="Exercice moyen"
                    value={kpis?.activite_physique?.avg_exercise_hours?.toFixed(1) || 0}
                    unit="heures/semaine"
                    color="#4facfe"
                />
                <StatCard
                    icon="🔥"
                    title="Calories brûlées"
                    value={kpis?.gym?.avg_calories_burned?.toFixed(0) || 0}
                    unit="kcal/session"
                    color="#4facfe"
                />
            </div>
        </div>
    );
}

export default Dashboard;