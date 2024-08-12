import React, { useState } from 'react';
import './UserProfile.css';

function UserProfile({ user, onUpdateProfile }) {
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email);
  const [avatar, setAvatar] = useState(user.avatar);
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = () => {
    const updatedUser = { username, email, avatar };
    onUpdateProfile(updatedUser);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setUsername(user.username);
    setEmail(user.email);
    setAvatar(user.avatar);
    setIsEditing(false);
  };

  return (
    <div className="user-profile">
      <h2>User Profile</h2>
      <div className="avatar-container">
        <img src={avatar} alt="User Avatar" className="avatar" />
        {isEditing && (
          <input
            type="url"
            value={avatar}
            onChange={(e) => setAvatar(e.target.value)}
            placeholder="Avatar URL"
          />
        )}
      </div>
      <div className="info-container">
        <div className="info-item">
          <label>Username:</label>
          {isEditing ? (
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          ) : (
            <span>{username}</span>
          )}
        </div>
        <div className="info-item">
          <label>Email:</label>
          {isEditing ? (
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          ) : (
            <span>{email}</span>
          )}
        </div>
      </div>
      <div className="actions">
        {isEditing ? (
          <>
            <button onClick={handleSave}>Save</button>
            <button onClick={handleCancel}>Cancel</button>
          </>
        ) : (
          <button onClick={() => setIsEditing(true)}>Edit Profile</button>
        )}
      </div>
    </div>
  );
}

export default UserProfile;
