function StatCard({ icon, title, value, unit, color = '#667eea' }) {
  return (
    <div className="stat-box">
      <div className="stat-icon">{icon}</div>
      <h4>{title}</h4>
      <p className="big-number" style={{ color }}>{value}</p>
      {unit && <span className="unit">{unit}</span>}
    </div>
  );
}

export default StatCard;