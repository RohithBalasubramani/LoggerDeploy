import React from 'react';
import { Device } from '../../types';
import { EdgeDeviceIcon, RouterIcon, MfmIcon } from '../icons/DeviceIcons';

interface DeviceCardProps {
  device: Device;
  isSelected?: boolean;
  onSelect: (id: string) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, isSelected, onSelect }) => {
  const style: React.CSSProperties = {
    position: 'absolute',
    left: `${device.x}%`,
    top: `${device.y}%`,
    transform: 'translate(-50%, -50%)',
  };

  return (
    <div
      style={style}
      className={`bg-white rounded-lg p-2 shadow-sm border ${
        isSelected ? 'border-blue-500 ring-2 ring-blue-100 scale-105 z-20' : 'border-gray-200'
      } w-24 flex flex-col items-center justify-center relative hover:shadow-md transition-all cursor-pointer z-10`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(device.id);
      }}
    >
      <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-green-500"></div>
      <div className="mb-1">
        {device.type === 'edge' && <EdgeDeviceIcon />}
        {device.type === 'router' && <RouterIcon />}
        {device.type === 'mfm' && <MfmIcon />}
      </div>
      <div className="font-bold text-gray-700 text-center leading-tight text-xs truncate w-full px-1">
        {device.name}
      </div>
      <div className="text-gray-400 font-medium truncate w-full text-center text-[10px]">
        {device.ip}
      </div>
    </div>
  );
};
