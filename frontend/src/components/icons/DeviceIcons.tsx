import React from 'react';

export const EdgeDeviceIcon: React.FC = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="6" width="13" height="10" rx="1" stroke="#525252" strokeWidth="1.5" />
    <rect x="4" y="8" width="9" height="6" rx="0.5" fill="#525252" opacity="0.1" />
    <rect x="17" y="6" width="5" height="10" rx="1" fill="#525252" />
    <line x1="5" y1="18" x2="12" y2="18" stroke="#525252" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const RouterIcon: React.FC = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="14" width="18" height="6" rx="1" stroke="#525252" strokeWidth="1.5" />
    <line x1="8" y1="14" x2="5" y2="6" stroke="#525252" strokeWidth="1.5" strokeLinecap="round" />
    <line x1="16" y1="14" x2="19" y2="6" stroke="#525252" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const MfmIcon: React.FC = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="5" width="18" height="14" rx="2" stroke="#525252" strokeWidth="1.5" />
    <rect x="6" y="8" width="12" height="6" rx="1" fill="#525252" opacity="0.2" />
    <circle cx="6" cy="16.5" r="0.8" fill="#525252" />
    <circle cx="10" cy="16.5" r="0.8" fill="#525252" />
    <circle cx="14" cy="16.5" r="0.8" fill="#525252" />
    <circle cx="18" cy="16.5" r="0.8" fill="#525252" />
  </svg>
);

export const ReferenceLogo: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 34L34 14" stroke="#525252" strokeWidth="6" strokeLinecap="round" />
    <path d="M22 34L34 22" stroke="#525252" strokeWidth="6" strokeLinecap="round" />
    <circle cx="36" cy="12" r="4.5" fill="#525252" />
    <circle cx="12" cy="36" r="4.5" fill="#525252" />
  </svg>
);

export const PlugIcon: React.FC<{ style?: React.CSSProperties }> = ({ style }) => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={style}>
    <path d="M8 5H16V8H8V5Z" fill="currentColor" />
    <path d="M6 8.5H18V13.5C18 16.5 15.5 19.5 12 21.5C8.5 19.5 6 16.5 6 13.5V8.5Z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
    <path d="M10 6.5H14" stroke="white" strokeWidth="1.2" strokeLinecap="round" />
  </svg>
);
