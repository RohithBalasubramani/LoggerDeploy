import React from 'react';

interface DeviceDetailRowProps {
  label: string;
  value: string;
  isStatus?: boolean;
}

export const DeviceDetailRow: React.FC<DeviceDetailRowProps> = ({ label, value, isStatus }) => (
  <div className="flex justify-between items-center py-2 px-1">
    <span className="text-gray-400 font-medium text-sm">
      {label}
    </span>
    <div className="flex items-center gap-2">
      {isStatus && <div className="w-2 h-2 rounded-full bg-green-600" />}
      <span className="text-gray-700 font-semibold text-sm">
        {value}
      </span>
    </div>
  </div>
);
