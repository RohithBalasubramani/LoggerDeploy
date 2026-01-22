import React, { useState } from 'react';
import { X, Plus, Search, ChevronDown, ArrowLeft } from 'lucide-react';
import { Device } from '../../types';
import { MfmIcon, EdgeDeviceIcon, RouterIcon } from '../icons/DeviceIcons';

interface AddTableModalProps {
  isOpen: boolean;
  onClose: () => void;
  devices: Device[];
  schemas: string[];
}

export const AddTableModal: React.FC<AddTableModalProps> = ({ isOpen, onClose, devices, schemas }) => {
  const [view, setView] = useState<'main' | 'selectDevice'>('main');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl w-[480px] shadow-2xl border border-gray-200 flex flex-col">
        {view === 'main' ? (
          <>
            <div className="p-5 border-b border-gray-100 flex justify-between items-center">
              <h2 className="font-bold text-gray-800 text-xl">Add New Table</h2>
              <X className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600" onClick={onClose} />
            </div>
            <div className="p-5 space-y-5">
              <div className="space-y-2">
                <label className="font-bold text-gray-700 text-sm">Select Device</label>
                {!selectedDevice ? (
                  <button
                    onClick={() => setView('selectDevice')}
                    className="w-full border-2 border-dashed border-gray-200 rounded-lg py-4 flex items-center justify-center gap-2 text-gray-500 hover:border-gray-400 hover:bg-gray-50"
                  >
                    <Plus className="w-5 h-5" />
                    <span className="font-bold text-sm">Select Device</span>
                  </button>
                ) : (
                  <div className="w-full border border-gray-100 rounded-lg p-3 flex items-center justify-between bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className="bg-gray-100 p-2 rounded-lg">
                        {selectedDevice.type === 'mfm' && <MfmIcon />}
                        {selectedDevice.type === 'edge' && <EdgeDeviceIcon />}
                        {selectedDevice.type === 'router' && <RouterIcon />}
                      </div>
                      <span className="font-bold text-gray-800">{selectedDevice.name} ({selectedDevice.room})</span>
                    </div>
                    <button onClick={() => setView('selectDevice')} className="px-3 py-1 bg-white border rounded-lg text-sm font-bold text-gray-600 hover:bg-gray-50">
                      Change
                    </button>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <label className="font-bold text-gray-700 text-sm">Select Schema</label>
                <div className="relative">
                  <select className="w-full px-4 py-3 border border-gray-200 rounded-lg font-bold text-gray-800 appearance-none bg-white">
                    <option value="">Select Schema</option>
                    {schemas.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                </div>
              </div>
              <div className="space-y-2">
                <label className="font-bold text-gray-700 text-sm">Select Database</label>
                <div className="relative">
                  <select className="w-full px-4 py-3 border border-gray-200 rounded-lg font-bold text-gray-800 appearance-none bg-white">
                    <option value="">Select database path</option>
                    <option value="path1">Sqlite:C:\new\test.db</option>
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                </div>
              </div>
            </div>
            <div className="p-5 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
              <button onClick={onClose} className="px-5 py-2 border border-gray-200 rounded-lg font-bold text-gray-700 hover:bg-white">Cancel</button>
              <button className="px-5 py-2 bg-gray-700 text-white rounded-lg font-bold hover:bg-black">Add Table</button>
            </div>
          </>
        ) : (
          <>
            <div className="p-5 border-b border-gray-100 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <ArrowLeft className="w-5 h-5 text-gray-500 cursor-pointer hover:text-gray-800" onClick={() => setView('main')} />
                <h2 className="font-bold text-gray-800 text-xl">Select Device</h2>
              </div>
              <X className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600" onClick={onClose} />
            </div>
            <div className="p-5 flex flex-col gap-4 max-h-[400px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" placeholder="Search devices..." className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg" />
              </div>
              <div className="flex-1 overflow-y-auto space-y-2">
                {devices.map((device) => (
                  <div
                    key={device.id}
                    onClick={() => setSelectedDevice(device)}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all
                      ${selectedDevice?.id === device.id ? 'border-gray-400 bg-gray-50' : 'border-gray-100 hover:border-gray-200'}`}
                  >
                    <div className="flex items-center gap-3">
                      <input type="radio" checked={selectedDevice?.id === device.id} onChange={() => setSelectedDevice(device)} className="w-4 h-4 accent-gray-600" />
                      <div className="bg-gray-100 p-2 rounded-lg">
                        {device.type === 'mfm' && <MfmIcon />}
                        {device.type === 'edge' && <EdgeDeviceIcon />}
                        {device.type === 'router' && <RouterIcon />}
                      </div>
                      <span className="font-bold text-gray-800">{device.name} ({device.room})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-5 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
              <button onClick={() => setView('main')} className="px-5 py-2 border border-gray-200 rounded-lg font-bold text-gray-700 hover:bg-white">Cancel</button>
              <button onClick={() => setView('main')} className="px-5 py-2 bg-gray-700 text-white rounded-lg font-bold hover:bg-black">Done</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
