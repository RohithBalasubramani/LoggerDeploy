import React, { useRef, useState } from 'react';
import { Search, SlidersHorizontal, Map as MapIcon, Table as TableIcon, MoreHorizontal, X, Monitor, Wifi, Cpu, Database, Activity, Check, Loader2, AlertCircle } from 'lucide-react';
import { Device } from '../../types';
import { DeviceCard } from '../devices/DeviceCard';

interface DeviceMapViewProps {
  devices: Device[];
  selectedDeviceId: string | null;
  setSelectedDeviceId: (id: string | null) => void;
}

type ViewMode = 'map' | 'table';

interface FilterState {
  status: string[];
  room: string[];
  protocol: string[];
  type: string[];
}

export const DeviceMapView: React.FC<DeviceMapViewProps> = ({
  devices,
  selectedDeviceId,
  setSelectedDeviceId
}) => {
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('map');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [filters, setFilters] = useState<FilterState>({ status: [], room: [], protocol: [], type: [] });
  const [isQuickTesting, setIsQuickTesting] = useState(false);
  const [quickTestResults, setQuickTestResults] = useState<{ success: boolean; message: string } | null>(null);
  const panStartRef = useRef({ x: 0, y: 0, tx: 0, ty: 0 });

  const selectedDevice = devices.find(d => d.id === selectedDeviceId);

  // Filter logic
  const filteredDevices = devices.filter(d => {
    const matchesSearch = searchQuery === '' ||
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.ip.includes(searchQuery);

    const matchesStatus = filters.status.length === 0 || filters.status.includes(d.status);
    const matchesRoom = filters.room.length === 0 || filters.room.includes(d.room);
    const matchesType = filters.type.length === 0 || filters.type.includes(d.type);
    const matchesProtocol = filters.protocol.length === 0 ||
      d.protocols.some(p => filters.protocol.includes(p.type));

    return matchesSearch && matchesStatus && matchesRoom && matchesType && matchesProtocol;
  });

  const toggleFilter = (category: keyof FilterState, value: string) => {
    setFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }));
  };

  const clearFilters = () => {
    setFilters({ status: [], room: [], protocol: [], type: [] });
  };

  const activeFilterCount = Object.values(filters).flat().length;

  const onMouseDown = (e: React.MouseEvent) => {
    setIsPanning(true);
    panStartRef.current = { x: e.clientX, y: e.clientY, tx: transform.x, ty: transform.y };
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setTransform(prev => ({
      ...prev,
      x: panStartRef.current.tx + (e.clientX - panStartRef.current.x),
      y: panStartRef.current.ty + (e.clientY - panStartRef.current.y)
    }));
  };

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setTransform(prev => ({ ...prev, scale: Math.min(Math.max(prev.scale - e.deltaY * 0.001, 0.4), 3) }));
  };

  // Quick Test functionality - simulates reading registers
  const handleQuickTest = () => {
    if (!selectedDevice) return;
    setIsQuickTesting(true);
    setQuickTestResults(null);

    // Simulate connection test
    setTimeout(() => {
      const success = selectedDevice.status !== 'offline';
      setQuickTestResults({
        success,
        message: success
          ? `Successfully connected to ${selectedDevice.name} via ${selectedDevice.protocols[0]?.type.toUpperCase() || 'Modbus'}. Read ${selectedDevice.registers?.length || 0} registers.`
          : `Failed to connect to ${selectedDevice.name}. Device appears to be offline.`
      });
      setIsQuickTesting(false);
    }, 1500);
  };

  const rooms = ['Control Room', 'Electrical Panel', 'Production Floor', 'Server Room'];

  return (
    <div className="flex-1 flex gap-3 overflow-hidden h-full">
      {/* Map/Table Area */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col overflow-hidden shadow-sm">
        <div className="p-4 flex justify-between items-center border-b border-gray-100">
          <div className="flex gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search devices..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-48 bg-gray-50 focus:outline-none text-sm"
              />
            </div>
            <div className="relative">
              <button
                onClick={() => setShowFilter(!showFilter)}
                className={`flex items-center gap-2 px-4 py-2 border rounded-lg font-medium hover:bg-gray-50 text-sm ${activeFilterCount > 0 ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-gray-200 text-gray-600'}`}
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filter
                {activeFilterCount > 0 && (
                  <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">{activeFilterCount}</span>
                )}
              </button>

              {/* Filter Dropdown */}
              {showFilter && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-4">
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-bold text-gray-800">Filters</span>
                    {activeFilterCount > 0 && (
                      <button onClick={clearFilters} className="text-xs text-blue-600 hover:underline">Clear all</button>
                    )}
                  </div>

                  {/* Status Filter */}
                  <div className="mb-3">
                    <span className="text-xs font-bold text-gray-500 uppercase">Status</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {['online', 'offline', 'warning'].map(status => (
                        <button
                          key={status}
                          onClick={() => toggleFilter('status', status)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${filters.status.includes(status) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                        >
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Room Filter */}
                  <div className="mb-3">
                    <span className="text-xs font-bold text-gray-500 uppercase">Room</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {rooms.map(room => (
                        <button
                          key={room}
                          onClick={() => toggleFilter('room', room)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${filters.room.includes(room) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                        >
                          {room}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Protocol Filter */}
                  <div className="mb-3">
                    <span className="text-xs font-bold text-gray-500 uppercase">Protocol</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {['modbus', 'opcua'].map(protocol => (
                        <button
                          key={protocol}
                          onClick={() => toggleFilter('protocol', protocol)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${filters.protocol.includes(protocol) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                        >
                          {protocol.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Type Filter */}
                  <div>
                    <span className="text-xs font-bold text-gray-500 uppercase">Device Type</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {['edge', 'router', 'mfm'].map(type => (
                        <button
                          key={type}
                          onClick={() => toggleFilter('type', type)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${filters.type.includes(type) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                        >
                          {type === 'mfm' ? 'Energy Meter' : type === 'edge' ? 'Edge Device' : 'Router'}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <span className="text-sm text-gray-400 self-center">
              {filteredDevices.length} of {devices.length} devices
            </span>
          </div>
          <div className="flex bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs ${viewMode === 'map' ? 'bg-white shadow-sm font-bold text-gray-800' : 'font-medium text-gray-500'}`}
            >
              <MapIcon className="w-4 h-4" /> Map
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs ${viewMode === 'table' ? 'bg-white shadow-sm font-bold text-gray-800' : 'font-medium text-gray-500'}`}
            >
              <TableIcon className="w-4 h-4" /> Table
            </button>
          </div>
        </div>

        {/* Map View */}
        {viewMode === 'map' && (
          <div
            className={`flex-1 overflow-hidden relative select-none bg-gray-50 ${isPanning ? 'cursor-grabbing' : 'cursor-grab'}`}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={() => setIsPanning(false)}
            onMouseLeave={() => setIsPanning(false)}
            onWheel={onWheel}
            onClick={() => setSelectedDeviceId(null)}
          >
            <div className="w-full h-full origin-center relative" style={{ transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})` }}>
              <div className="absolute inset-0 p-6 grid grid-cols-2 grid-rows-2 gap-4">
                {rooms.map((room) => (
                  <div key={room} className="bg-gray-100 rounded-xl relative flex items-center justify-center border border-gray-200/50 overflow-hidden">
                    <span className="text-gray-300 font-bold text-3xl uppercase tracking-widest opacity-40">{room}</span>
                    {filteredDevices.filter(d => d.room === room).map(d => (
                      <DeviceCard key={d.id} device={d} isSelected={selectedDeviceId === d.id} onSelect={setSelectedDeviceId} />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Table View */}
        {viewMode === 'table' && (
          <div className="flex-1 overflow-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b border-gray-100 sticky top-0">
                <tr className="text-gray-400 font-bold text-xs uppercase">
                  <th className="px-4 py-3">Device Name</th>
                  <th className="px-4 py-3">IP Address</th>
                  <th className="px-4 py-3">Room</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Protocols</th>
                  <th className="px-4 py-3">Manufacturer</th>
                  <th className="px-4 py-3">Model</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredDevices.map(device => (
                  <tr
                    key={device.id}
                    onClick={() => setSelectedDeviceId(device.id)}
                    className={`hover:bg-gray-50 cursor-pointer ${selectedDeviceId === device.id ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-4 py-3 font-bold text-gray-800 text-sm">{device.name}</td>
                    <td className="px-4 py-3 font-mono text-gray-600 text-sm">{device.ip}</td>
                    <td className="px-4 py-3 text-gray-600 text-sm">{device.room}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${device.status === 'online' ? 'bg-green-100 text-green-700' : device.status === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${device.status === 'online' ? 'bg-green-500' : device.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                        {device.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {device.protocols.map((p, i) => (
                          <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-medium">
                            {p.type.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">{device.manufacturer || '-'}</td>
                    <td className="px-4 py-3 text-gray-600 text-sm">{device.model || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Device Detail Panel */}
      {selectedDevice && (
        <div className="w-96 bg-white rounded-xl border border-gray-200 flex flex-col overflow-hidden shadow-sm">
          <div className="p-4 border-b border-gray-100 flex justify-between items-center">
            <h2 className="font-bold text-gray-800 text-lg">{selectedDevice.name}</h2>
            <div className="flex items-center gap-2 text-gray-400">
              <MoreHorizontal className="w-5 h-5 cursor-pointer hover:text-gray-600" />
              <X className="w-5 h-5 cursor-pointer hover:text-gray-600" onClick={() => setSelectedDeviceId(null)} />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {/* Device Image */}
            <div className="flex justify-center items-center py-6 bg-gray-50">
              <div className="w-4/5 h-28 bg-gray-400 rounded-lg flex items-center justify-center">
                {selectedDevice.type === 'edge' ? <Monitor className="w-10 h-10 text-white/80" /> :
                  selectedDevice.type === 'router' ? <Wifi className="w-10 h-10 text-white/80" /> :
                    <Cpu className="w-10 h-10 text-white/80" />}
              </div>
            </div>

            {/* Device Info */}
            <div className="p-4 space-y-4">
              {/* Connection Info */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <SlidersHorizontal className="w-4 h-4 text-gray-500" />
                  <h3 className="font-bold text-gray-700 text-sm">Connection Details</h3>
                </div>
                <div className="space-y-1.5 bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">IP Address</span>
                    <span className="font-mono text-gray-700">{selectedDevice.ip}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">MAC Address</span>
                    <span className="font-mono text-gray-700">{selectedDevice.mac}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Status</span>
                    <span className={`font-medium ${selectedDevice.status === 'online' ? 'text-green-600' : selectedDevice.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>
                      {selectedDevice.status.charAt(0).toUpperCase() + selectedDevice.status.slice(1)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Protocols */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-gray-500" />
                  <h3 className="font-bold text-gray-700 text-sm">Protocols</h3>
                </div>
                <div className="space-y-2">
                  {selectedDevice.protocols.map((protocol, i) => (
                    <div key={i} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${protocol.type === 'modbus' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                          {protocol.type.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-400">Port {protocol.port}</span>
                      </div>
                      {protocol.unitId !== undefined && (
                        <div className="text-xs text-gray-500">Unit ID: {protocol.unitId}</div>
                      )}
                      {protocol.endpoint && (
                        <div className="text-xs text-gray-500 font-mono truncate">{protocol.endpoint}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Device Info */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-gray-500" />
                  <h3 className="font-bold text-gray-700 text-sm">Device Info</h3>
                </div>
                <div className="space-y-1.5 bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Manufacturer</span>
                    <span className="text-gray-700">{selectedDevice.manufacturer || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Model</span>
                    <span className="text-gray-700">{selectedDevice.model || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Firmware</span>
                    <span className="font-mono text-gray-700">{selectedDevice.firmware || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Registers</span>
                    <span className="text-gray-700">{selectedDevice.registers?.length || 0}</span>
                  </div>
                </div>
              </div>

              {/* Live Register Values */}
              {selectedDevice.registers && selectedDevice.registers.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-4 h-4 text-gray-500" />
                    <h3 className="font-bold text-gray-700 text-sm">Live Values</h3>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 max-h-48 overflow-y-auto">
                    {selectedDevice.registers.slice(0, 6).map((reg, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-gray-500 truncate flex-1">{reg.name}</span>
                        <span className="font-mono text-gray-700 ml-2">
                          {typeof reg.value === 'number' ? reg.value.toFixed(reg.dataType === 'float' ? 2 : 0) : reg.value}
                          {reg.unit && <span className="text-gray-400 ml-1">{reg.unit}</span>}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Quick Test */}
          <div className="p-4 border-t border-gray-100 space-y-3">
            {quickTestResults && (
              <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${quickTestResults.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {quickTestResults.success ? <Check className="w-4 h-4 mt-0.5 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
                <span>{quickTestResults.message}</span>
              </div>
            )}
            <button
              onClick={handleQuickTest}
              disabled={isQuickTesting}
              className="w-full bg-gray-700 text-white font-bold py-3 rounded-lg hover:bg-black transition-all flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {isQuickTesting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Testing Connection...
                </>
              ) : (
                'Quick Test'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Click outside to close filter */}
      {showFilter && (
        <div className="fixed inset-0 z-40" onClick={() => setShowFilter(false)} />
      )}
    </div>
  );
};
