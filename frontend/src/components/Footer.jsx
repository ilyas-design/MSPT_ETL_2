function Footer() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="footer">
      <div className="footer-content">
        <p>&copy; {currentYear} MSPR Dashboard. Tous droits réservés.</p>
        <div className="footer-links">
          <a href="#privacy">Confidentialité</a>
          <a href="#terms">Conditions</a>
          <a href="#contact">Contact</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;