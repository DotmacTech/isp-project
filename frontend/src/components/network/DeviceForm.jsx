import React, { useState, useEffect } from 'react';

const DeviceForm = ({ device, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    ip: '',
    is_active: true,
  });

  useEffect(() => {
    if (device) {
      setFormData({
        title: device.title || '',
        ip: device.ip || '',
        is_active: device.is_active !== undefined ? device.is_active : true,
      });
    }
  }, [device]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Title</label>
        <input type="text" name="title" value={formData.title} onChange={handleChange} required />
      </div>
      <div>
        <label>IP Address</label>
        <input type="text" name="ip" value={formData.ip} onChange={handleChange} required />
      </div>
      <div>
        <label>
          <input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} />
          Active
        </label>
      </div>
      <div>
        <button type="submit">Save</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
};

export default DeviceForm;
