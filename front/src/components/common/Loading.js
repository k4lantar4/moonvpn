import React from 'react';
import './Loading.css';

export const LoadingSpinner = ({ size = 'medium' }) => {
  return (
    <div className={`loading-spinner loading-spinner-${size}`}>
      <div className="spinner"></div>
    </div>
  );
};

export const SkeletonLoader = ({ type = 'text', count = 1 }) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return <div className="skeleton-card" />;
      case 'avatar':
        return <div className="skeleton-avatar" />;
      case 'button':
        return <div className="skeleton-button" />;
      case 'text':
      default:
        return <div className="skeleton-text" />;
    }
  };

  return (
    <div className="skeleton-wrapper">
      {[...Array(count)].map((_, index) => (
        <div key={index} className="skeleton-item">
          {renderSkeleton()}
        </div>
      ))}
    </div>
  );
};

export const PageLoader = () => {
  return (
    <div className="page-loader">
      <LoadingSpinner size="large" />
      <div className="page-loader-text">Loading...</div>
    </div>
  );
}; 