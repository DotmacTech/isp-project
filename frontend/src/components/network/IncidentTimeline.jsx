import React from 'react';

const IncidentTimeline = ({ updates }) => {
  if (!updates || updates.length === 0) {
    return <p>No updates for this incident yet.</p>;
  }

  return (
    <div>
      {updates.map(update => (
        <div key={update.id} style={{ borderBottom: '1px solid #ccc', padding: '10px 0' }}>
          <p>{update.content}</p>
          <small>Posted at: {new Date(update.created_at).toLocaleString()}</small>
        </div>
      ))}
    </div>
  );
};

export default IncidentTimeline;
