import React from 'react';
import { Outlet } from 'react-router-dom';

const CustomerPortalLayout = () => {
  return (
    <div>
      <header style={styles.header}>
        <nav style={styles.nav}>
          <h1 style={styles.title}>Customer Portal</h1>
          {/* Add customer portal specific navigation here */}
        </nav>
      </header>
      <main style={styles.mainContent}>
        <Outlet /> {/* This is where child routes will be rendered */}
      </main>
      <footer style={styles.footer}>
        <p>&copy; {new Date().getFullYear()} ISP Project Customer Portal</p>
      </footer>
    </div>
  );
};

const styles = {
  header: {
    backgroundColor: '#333',
    color: '#fff',
    padding: '15px 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  title: {
    margin: 0,
    fontSize: '24px',
  },
  mainContent: {
    maxWidth: '1200px',
    margin: '20px auto',
    padding: '0 20px',
    minHeight: 'calc(100vh - 120px)', // Adjust based on header/footer height
  },
  footer: {
    backgroundColor: '#333',
    color: '#fff',
    textAlign: 'center',
    padding: '15px 20px',
    marginTop: '20px',
  },
};

export default CustomerPortalLayout;
