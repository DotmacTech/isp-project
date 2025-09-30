import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../../services/api';
import Modal from '../../components/Modal';
import ThresholdEditForm from '../performance_management/ThresholdEditForm';
import styles from './SettingsPage.module.css';

const SettingsPage = () => {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentMetric, setCurrentMetric] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/v1/network/performance/metrics/', { params: { limit: 1000 } });
      const data = response.data;
      setMetrics(data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const handleOpenModal = (metric) => {
    setCurrentMetric(metric);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentMetric(null);
  };

  const handleSaveThresholds = async (thresholdData) => {
    if (!currentMetric) return;
    try {
      await apiClient.put(`/v1/network/performance/metrics/${currentMetric.id}`, thresholdData);
      fetchMetrics(); // Refresh the list
      handleCloseModal();
    } catch (err) {
      setError(`Failed to save thresholds: ${err.message}`);
    }
  };

  return (
    <div className={styles.container}>
      <h1>Settings & Configuration</h1>

      {error && <div className={styles.errorBanner}>{error}</div>}

      <div className={styles.section}>
        <h2>Performance Thresholds</h2>
        <p>Configure warning and critical thresholds for performance metrics.</p>
        {loading ? (
          <p>Loading metrics...</p>
        ) : (
          <table className={styles.settingsTable}>
            <thead>
              <tr>
                <th>Metric Name</th>
                <th>Unit</th>
                <th>Warning Threshold</th>
                <th>Critical Threshold</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => (
                <tr key={metric.id}>
                  <td>{metric.metric_name}</td>
                  <td>{metric.unit}</td>
                  <td>{metric.thresholds?.warning ?? 'Not set'}</td>
                  <td>{metric.thresholds?.critical ?? 'Not set'}</td>
                  <td className={styles.actions}>
                    <button onClick={() => handleOpenModal(metric)} className={styles.editButton}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className={styles.section}>
        <h2>SNMP Configuration</h2>
        <p>
          SNMP settings are managed on a per-profile basis. You can create, edit, and assign
          SNMP profiles to devices on the SNMP Profile Management page.
        </p>
        <Link to="/dashboard/network/snmp-profiles" className={styles.linkButton}>
          Go to SNMP Profile Management
        </Link>
      </div>

      <div className={styles.section}>
        <h2>Notification Rules</h2>
        <div className={styles.placeholder}>
          <p>
            <strong>Feature Coming Soon</strong>
          </p>
          <p>
            This section will allow you to configure rules for sending notifications.
            For example, you could create a rule to email the 'Network Ops' team for any
            'critical' alert, or send a Slack message for 'high' severity incidents.
          </p>
          <p>
            This requires backend API support for creating and managing notification rules.
          </p>
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title="Edit Thresholds"
      >
        <ThresholdEditForm
          metric={currentMetric}
          onSave={handleSaveThresholds}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  );
};

export default SettingsPage;