import React, { useState } from 'react';

const AddIncidentUpdateForm = ({ onAddUpdate }) => {
  const [content, setContent] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    onAddUpdate(content);
    setContent('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Add an update..."
        rows={4}
        style={{ width: '100%', marginBottom: '10px' }}
        required
      />
      <button type="submit">Add Update</button>
    </form>
  );
};

export default AddIncidentUpdateForm;
