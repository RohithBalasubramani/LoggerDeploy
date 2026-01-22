import React, { useState } from 'react';
import {
  Header, DeviceMapView, SchemasView, TablesView,
  AIChatPanel, AddTableModal
} from './components';
import { Device, ChatMessage, Field, Schema, TableItem, TableRow } from './types';

// Helper to generate rows for a table based on schema
const generateRowsForSchema = (schemaName: string): TableRow[] => {
  const baseRows: Record<string, Omit<TableRow, 'id'>[]> = {
    'Energy Meter Basic': [
      { validated: true, key: 'Voltage L1-N', address: '40001', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L2-N', address: '40003', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L3-N', address: '40005', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Current L1', address: '40007', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Current L2', address: '40009', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: false, key: 'Current L3', address: '40011', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: false, key: 'Active Power', address: '40013', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Reactive Power', address: '40015', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Power Factor', address: '40017', dataType: 'float', scale: '0.001', deadband: '0.01' },
      { validated: false, key: 'Frequency', address: '40019', dataType: 'float', scale: '0.01', deadband: '0.1' },
    ],
    'Energy Meter Advanced': [
      { validated: true, key: 'Voltage L1-N', address: '40001', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L2-N', address: '40003', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L3-N', address: '40005', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Current L1', address: '40007', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Current L2', address: '40009', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Current L3', address: '40011', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Active Power Total', address: '40013', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: true, key: 'Reactive Power Total', address: '40015', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Apparent Power', address: '40017', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Power Factor', address: '40019', dataType: 'float', scale: '0.001', deadband: '0.01' },
      { validated: false, key: 'Frequency', address: '40021', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: false, key: 'Import kWh', address: '40023', dataType: 'float', scale: '0.01', deadband: '10' },
      { validated: false, key: 'Export kWh', address: '40027', dataType: 'float', scale: '0.01', deadband: '10' },
      { validated: false, key: 'Max Demand', address: '40031', dataType: 'float', scale: '0.01', deadband: '5' },
    ],
    'Three Phase Power': [
      { validated: true, key: 'Voltage L1-N', address: '40001', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L2-N', address: '40003', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Voltage L3-N', address: '40005', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: false, key: 'Voltage L1-L2', address: '40007', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: false, key: 'Voltage L2-L3', address: '40009', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: false, key: 'Voltage L3-L1', address: '40011', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Current L1', address: '40013', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Current L2', address: '40015', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: true, key: 'Current L3', address: '40017', dataType: 'float', scale: '0.01', deadband: '0.1' },
      { validated: false, key: 'Active Power L1', address: '40019', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Active Power L2', address: '40021', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Active Power L3', address: '40023', dataType: 'float', scale: '0.001', deadband: '1' },
      { validated: false, key: 'Active Power Total', address: '40025', dataType: 'float', scale: '0.001', deadband: '1' },
    ],
    'Environmental': [
      { validated: true, key: 'Temperature', address: '40001', dataType: 'float', scale: '0.1', deadband: '0.5' },
      { validated: true, key: 'Humidity', address: '40003', dataType: 'float', scale: '0.1', deadband: '1' },
      { validated: false, key: 'Pressure', address: '40005', dataType: 'float', scale: '0.1', deadband: '5' },
    ],
  };

  const rows = baseRows[schemaName] || baseRows['Energy Meter Basic'];
  return rows.map((row, i) => ({ ...row, id: `row-${Date.now()}-${i}` }));
};

// AI Flow Steps
const SCAN_STEPS = [
  "Detecting Network Interfaces",
  "Scanning for Modbus Gateways",
  "Gateway Validation & Authentication",
  "Scanning Devices Behind Gateway",
  "Reading Device Registers",
  "Device Type Identification",
  "Mapping Available Data Points",
  "Device Registry Complete"
];

const SCHEMA_STEPS = [
  "Analyzing available registers",
  "Grouping similar data points",
  "Creating schema definitions",
  "Schema validation complete"
];

const TABLE_STEPS = [
  "Mapping schemas to devices",
  "Creating database tables",
  "Configuring poll intervals",
  "Validation & Review"
];

// Realistic Devices - Industrial facility layout with protocols
const DEVICES: Device[] = [
  {
    id: 'gw1', name: 'Modbus Gateway', ip: '192.168.1.1', mac: 'AA:BB:CC:01:01:01',
    type: 'edge', room: 'Control Room', status: 'online', x: 25, y: 35,
    manufacturer: 'Advantech', model: 'EKI-1524', firmware: 'v2.1.3',
    protocols: [{ type: 'modbus', port: 502, unitId: 1 }],
    registers: [
      { address: '40001', name: 'Gateway Status', value: 1, unit: '', dataType: 'uint16' },
      { address: '40002', name: 'Connected Devices', value: 10, unit: '', dataType: 'uint16' },
    ]
  },
  {
    id: 'rtr1', name: 'Industrial Router', ip: '192.168.1.2', mac: 'AA:BB:CC:01:01:02',
    type: 'router', room: 'Control Room', status: 'online', x: 75, y: 35,
    manufacturer: 'Cisco', model: 'IE-4000', firmware: 'v15.2(7)',
    protocols: [{ type: 'modbus', port: 502, unitId: 1 }],
    registers: []
  },
  {
    id: 'em1', name: 'Main Incomer', ip: '192.168.1.10', mac: 'AA:BB:CC:02:01:01',
    type: 'mfm', room: 'Electrical Panel', status: 'online', x: 25, y: 30,
    manufacturer: 'Schneider Electric', model: 'PM5350', firmware: 'v3.2.1',
    protocols: [{ type: 'modbus', port: 502, unitId: 10 }],
    registers: [
      { address: '40001', name: 'Voltage L1-N', value: 231.5, unit: 'V', dataType: 'float' },
      { address: '40003', name: 'Voltage L2-N', value: 230.2, unit: 'V', dataType: 'float' },
      { address: '40005', name: 'Voltage L3-N', value: 232.1, unit: 'V', dataType: 'float' },
      { address: '40007', name: 'Current L1', value: 125.4, unit: 'A', dataType: 'float' },
      { address: '40009', name: 'Current L2', value: 118.7, unit: 'A', dataType: 'float' },
      { address: '40011', name: 'Current L3', value: 122.3, unit: 'A', dataType: 'float' },
      { address: '40013', name: 'Active Power', value: 85.2, unit: 'kW', dataType: 'float' },
      { address: '40015', name: 'Power Factor', value: 0.95, unit: '', dataType: 'float' },
    ]
  },
  {
    id: 'em2', name: 'UPS Input', ip: '192.168.1.11', mac: 'AA:BB:CC:02:01:02',
    type: 'mfm', room: 'Electrical Panel', status: 'online', x: 50, y: 30,
    manufacturer: 'ABB', model: 'M4M 20', firmware: 'v1.8.5',
    protocols: [{ type: 'modbus', port: 502, unitId: 11 }],
    registers: [
      { address: '40001', name: 'Voltage L1-N', value: 230.8, unit: 'V', dataType: 'float' },
      { address: '40003', name: 'Voltage L2-N', value: 231.1, unit: 'V', dataType: 'float' },
      { address: '40005', name: 'Voltage L3-N', value: 229.9, unit: 'V', dataType: 'float' },
      { address: '40007', name: 'Current L1', value: 45.2, unit: 'A', dataType: 'float' },
      { address: '40009', name: 'Current L2', value: 43.8, unit: 'A', dataType: 'float' },
      { address: '40011', name: 'Current L3', value: 44.5, unit: 'A', dataType: 'float' },
    ]
  },
  {
    id: 'em3', name: 'HVAC Feeder', ip: '192.168.1.12', mac: 'AA:BB:CC:02:01:03',
    type: 'mfm', room: 'Electrical Panel', status: 'online', x: 75, y: 30,
    manufacturer: 'Schneider Electric', model: 'PM5110', firmware: 'v2.5.0',
    protocols: [{ type: 'opcua', port: 4840, endpoint: '/opcua/pm5110' }],
    registers: [
      { address: 'ns=2;s=Voltage_L1N', name: 'Voltage L1-N', value: 229.5, unit: 'V', dataType: 'float' },
      { address: 'ns=2;s=Current_L1', name: 'Current L1', value: 32.1, unit: 'A', dataType: 'float' },
      { address: 'ns=2;s=Active_Power', name: 'Active Power', value: 22.4, unit: 'kW', dataType: 'float' },
      { address: 'ns=2;s=Power_Factor', name: 'Power Factor', value: 0.92, unit: '', dataType: 'float' },
    ]
  },
  {
    id: 'pm1', name: 'CNC Machine 1', ip: '192.168.1.20', mac: 'AA:BB:CC:03:01:01',
    type: 'mfm', room: 'Production Floor', status: 'online', x: 20, y: 50,
    manufacturer: 'Siemens', model: 'PAC3200', firmware: 'v2.0.3',
    protocols: [{ type: 'opcua', port: 4840, endpoint: '/opcua/pac3200' }],
    registers: [
      { address: 'ns=2;s=Voltage_L1N', name: 'Voltage L1-N', value: 228.7, unit: 'V', dataType: 'float' },
      { address: 'ns=2;s=Voltage_L2N', name: 'Voltage L2-N', value: 229.4, unit: 'V', dataType: 'float' },
      { address: 'ns=2;s=Voltage_L3N', name: 'Voltage L3-N', value: 230.1, unit: 'V', dataType: 'float' },
      { address: 'ns=2;s=Current_L1', name: 'Current L1', value: 78.5, unit: 'A', dataType: 'float' },
      { address: 'ns=2;s=Current_L2', name: 'Current L2', value: 76.2, unit: 'A', dataType: 'float' },
      { address: 'ns=2;s=Current_L3', name: 'Current L3', value: 77.8, unit: 'A', dataType: 'float' },
      { address: 'ns=2;s=Active_Power', name: 'Active Power', value: 52.3, unit: 'kW', dataType: 'float' },
    ]
  },
  {
    id: 'pm2', name: 'CNC Machine 2', ip: '192.168.1.21', mac: 'AA:BB:CC:03:01:02',
    type: 'mfm', room: 'Production Floor', status: 'warning', x: 50, y: 50,
    manufacturer: 'Siemens', model: 'PAC3200', firmware: 'v2.0.3',
    protocols: [{ type: 'modbus', port: 502, unitId: 21 }],
    registers: [
      { address: '40001', name: 'Voltage L1-N', value: 225.3, unit: 'V', dataType: 'float' },
      { address: '40007', name: 'Current L1', value: 82.1, unit: 'A', dataType: 'float' },
      { address: '40013', name: 'Active Power', value: 54.8, unit: 'kW', dataType: 'float' },
    ]
  },
  {
    id: 'pm3', name: 'Compressor', ip: '192.168.1.22', mac: 'AA:BB:CC:03:01:03',
    type: 'mfm', room: 'Production Floor', status: 'online', x: 80, y: 50,
    manufacturer: 'Lovato', model: 'DMG800', firmware: 'v1.2.0',
    protocols: [{ type: 'modbus', port: 502, unitId: 22 }],
    registers: [
      { address: '40001', name: 'Voltage L1-N', value: 230.5, unit: 'V', dataType: 'float' },
      { address: '40007', name: 'Current L1', value: 15.7, unit: 'A', dataType: 'float' },
      { address: '40013', name: 'Active Power', value: 10.8, unit: 'kW', dataType: 'float' },
      { address: '40017', name: 'Frequency', value: 50.02, unit: 'Hz', dataType: 'float' },
    ]
  },
  {
    id: 'sr1', name: 'Server Rack PDU', ip: '192.168.1.30', mac: 'AA:BB:CC:04:01:01',
    type: 'mfm', room: 'Server Room', status: 'online', x: 30, y: 40,
    manufacturer: 'APC', model: 'AP8853', firmware: 'v6.8.2',
    protocols: [{ type: 'modbus', port: 502, unitId: 30 }],
    registers: [
      { address: '40001', name: 'Voltage L1-N', value: 231.2, unit: 'V', dataType: 'float' },
      { address: '40007', name: 'Current L1', value: 28.4, unit: 'A', dataType: 'float' },
      { address: '40013', name: 'Active Power', value: 6.2, unit: 'kW', dataType: 'float' },
      { address: '40019', name: 'Energy Total', value: 15420.5, unit: 'kWh', dataType: 'float' },
    ]
  },
  {
    id: 'sr2', name: 'Cooling Unit', ip: '192.168.1.31', mac: 'AA:BB:CC:04:01:02',
    type: 'mfm', room: 'Server Room', status: 'online', x: 70, y: 40,
    manufacturer: 'Schneider Electric', model: 'InRow RC', firmware: 'v4.1.0',
    protocols: [{ type: 'opcua', port: 4840, endpoint: '/opcua/cooling' }],
    registers: [
      { address: 'ns=2;s=Temperature', name: 'Temperature', value: 22.5, unit: '°C', dataType: 'float' },
      { address: 'ns=2;s=Humidity', name: 'Humidity', value: 45.2, unit: '%RH', dataType: 'float' },
      { address: 'ns=2;s=Fan_Speed', name: 'Fan Speed', value: 1850, unit: 'RPM', dataType: 'uint16' },
      { address: 'ns=2;s=Cooling_Capacity', name: 'Cooling Capacity', value: 12.5, unit: 'kW', dataType: 'float' },
    ]
  },
];

// Initial Schemas with their fields
const INITIAL_SCHEMAS: Schema[] = [
  {
    id: 'schema-1',
    name: 'Energy Meter Basic',
    fields: [
      { id: 'f1', name: 'Voltage L1-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f2', name: 'Voltage L2-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f3', name: 'Voltage L3-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f4', name: 'Current L1', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f5', name: 'Current L2', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f6', name: 'Current L3', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f7', name: 'Active Power', type: 'float', unit: 'kW', scale: '0.001' },
      { id: 'f8', name: 'Reactive Power', type: 'float', unit: 'kVAR', scale: '0.001' },
      { id: 'f9', name: 'Power Factor', type: 'float', unit: 'PF', scale: '0.001' },
      { id: 'f10', name: 'Frequency', type: 'float', unit: 'Hz', scale: '0.01' },
    ]
  },
  {
    id: 'schema-2',
    name: 'Energy Meter Advanced',
    fields: [
      { id: 'f11', name: 'Voltage L1-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f12', name: 'Voltage L2-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f13', name: 'Voltage L3-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f14', name: 'Current L1', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f15', name: 'Current L2', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f16', name: 'Current L3', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f17', name: 'Active Power Total', type: 'float', unit: 'kW', scale: '0.001' },
      { id: 'f18', name: 'Reactive Power Total', type: 'float', unit: 'kVAR', scale: '0.001' },
      { id: 'f19', name: 'Apparent Power', type: 'float', unit: 'kVA', scale: '0.001' },
      { id: 'f20', name: 'Power Factor', type: 'float', unit: 'PF', scale: '0.001' },
      { id: 'f21', name: 'Frequency', type: 'float', unit: 'Hz', scale: '0.01' },
      { id: 'f22', name: 'Import kWh', type: 'float', unit: 'kWh', scale: '0.01' },
      { id: 'f23', name: 'Export kWh', type: 'float', unit: 'kWh', scale: '0.01' },
      { id: 'f24', name: 'Import kVARh', type: 'float', unit: 'kVARh', scale: '0.01' },
      { id: 'f25', name: 'Max Demand', type: 'float', unit: 'kW', scale: '0.01' },
      { id: 'f26', name: 'Max Demand Time', type: 'uint32', unit: 'timestamp', scale: '1' },
    ]
  },
  {
    id: 'schema-3',
    name: 'Power Quality',
    fields: [
      { id: 'f27', name: 'THD Voltage L1', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f28', name: 'THD Voltage L2', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f29', name: 'THD Voltage L3', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f30', name: 'THD Current L1', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f31', name: 'THD Current L2', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f32', name: 'THD Current L3', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f33', name: 'Voltage Unbalance', type: 'float', unit: '%', scale: '0.01' },
      { id: 'f34', name: 'Current Unbalance', type: 'float', unit: '%', scale: '0.01' },
    ]
  },
  {
    id: 'schema-4',
    name: 'Environmental',
    fields: [
      { id: 'f35', name: 'Temperature', type: 'float', unit: 'Celsius', scale: '0.1' },
      { id: 'f36', name: 'Humidity', type: 'float', unit: '%RH', scale: '0.1' },
      { id: 'f37', name: 'Pressure', type: 'float', unit: 'hPa', scale: '0.1' },
    ]
  },
  {
    id: 'schema-5',
    name: 'Three Phase Power',
    fields: [
      { id: 'f38', name: 'Voltage L1-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f39', name: 'Voltage L2-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f40', name: 'Voltage L3-N', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f41', name: 'Voltage L1-L2', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f42', name: 'Voltage L2-L3', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f43', name: 'Voltage L3-L1', type: 'float', unit: 'Volt', scale: '0.1' },
      { id: 'f44', name: 'Current L1', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f45', name: 'Current L2', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f46', name: 'Current L3', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f47', name: 'Current Neutral', type: 'float', unit: 'Ampere', scale: '0.01' },
      { id: 'f48', name: 'Active Power L1', type: 'float', unit: 'kW', scale: '0.001' },
      { id: 'f49', name: 'Active Power L2', type: 'float', unit: 'kW', scale: '0.001' },
      { id: 'f50', name: 'Active Power L3', type: 'float', unit: 'kW', scale: '0.001' },
      { id: 'f51', name: 'Active Power Total', type: 'float', unit: 'kW', scale: '0.001' },
    ]
  },
];

// Initial Tables linking devices → schemas → database (with rows)
const INITIAL_TABLES: TableItem[] = [
  { id: 'tbl-1', name: 'Main Incomer Log', validation: 'Done', device: 'Main Incomer', schema: 'Energy Meter Advanced', db: 'PostgreSQL:energy_db', type: 'map', rows: generateRowsForSchema('Energy Meter Advanced') },
  { id: 'tbl-2', name: 'Server Room Power', validation: 'Done', device: 'Server Rack PDU', schema: 'Energy Meter Basic', db: 'PostgreSQL:energy_db', type: 'map', rows: generateRowsForSchema('Energy Meter Basic') },
  { id: 'tbl-3', name: 'CNC Machine 1', validation: 'Pending', device: 'CNC Machine 1', schema: 'Three Phase Power', db: 'PostgreSQL:production_db', type: 'map', rows: generateRowsForSchema('Three Phase Power') },
  { id: 'tbl-4', name: 'CNC Machine 2', validation: 'Pending', device: 'CNC Machine 2', schema: 'Three Phase Power', db: 'PostgreSQL:production_db', type: 'unmap', rows: generateRowsForSchema('Three Phase Power') },
  { id: 'tbl-5', name: 'HVAC Monitoring', validation: 'Done', device: 'HVAC Feeder', schema: 'Energy Meter Basic', db: 'PostgreSQL:facilities_db', type: 'map', rows: generateRowsForSchema('Energy Meter Basic') },
  { id: 'tbl-6', name: 'Cooling Unit', validation: 'Pending', device: 'Cooling Unit', schema: 'Environmental', db: 'PostgreSQL:facilities_db', type: 'unmap', rows: generateRowsForSchema('Environmental') },
];

// Generate unique ID
const generateId = () => `id-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

export default function App() {
  const [activeTab, setActiveTab] = useState('connected devices');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  // Chat state
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading] = useState(false);

  // Step visibility states
  const [isSetupExpanded, setIsSetupExpanded] = useState(false);
  const [isStep2Visible] = useState(true);
  const [isSchemaExpanded, setIsSchemaExpanded] = useState(false);
  const [isStep3Visible] = useState(true);
  const [isTableExpanded, setIsTableExpanded] = useState(true);

  // Progress states
  const [currentStepIndex] = useState(SCAN_STEPS.length);
  const [mappingStepIndex] = useState(SCHEMA_STEPS.length);
  const [tableStepIndex] = useState(TABLE_STEPS.length);

  // Schemas state with full CRUD
  const [schemas, setSchemas] = useState<Schema[]>(INITIAL_SCHEMAS);

  // Tables state with full CRUD
  const [tables, setTables] = useState<TableItem[]>(INITIAL_TABLES);
  const [isAddTableModalOpen, setIsAddTableModalOpen] = useState(false);

  const tabs = ['Connected Devices', 'Schemas', 'Tables', 'Jobs'];
  const completedSteps = [true, mappingStepIndex === SCHEMA_STEPS.length, tableStepIndex === TABLE_STEPS.length, false];

  const isTabClickable = (label: string) => {
    const l = label.toLowerCase();
    if (l === 'connected devices') return true;
    if (l === 'schemas') return isStep2Visible;
    if (l === 'tables') return isStep3Visible;
    return false;
  };

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setChatHistory(prev => [...prev, { role: 'user', text: chatInput }]);
    setChatInput('');
  };

  // Schema CRUD operations
  const handleAddSchema = (name: string) => {
    const newSchema: Schema = {
      id: generateId(),
      name,
      fields: []
    };
    setSchemas(prev => [...prev, newSchema]);
  };

  const handleDeleteSchema = (schemaId: string) => {
    setSchemas(prev => prev.filter(s => s.id !== schemaId));
  };

  const handleUpdateSchema = (schemaId: string, name: string) => {
    setSchemas(prev => prev.map(s => s.id === schemaId ? { ...s, name } : s));
  };

  const handleDuplicateSchema = (schemaId: string) => {
    const schema = schemas.find(s => s.id === schemaId);
    if (schema) {
      const newSchema: Schema = {
        id: generateId(),
        name: `${schema.name} (Copy)`,
        fields: schema.fields.map(f => ({ ...f, id: generateId() }))
      };
      setSchemas(prev => [...prev, newSchema]);
    }
  };

  // Field CRUD operations
  const handleAddField = (schemaId: string, field: Omit<Field, 'id'>) => {
    const newField: Field = { ...field, id: generateId() };
    setSchemas(prev => prev.map(s =>
      s.id === schemaId ? { ...s, fields: [newField, ...s.fields] } : s
    ));
  };

  const handleDeleteField = (schemaId: string, fieldId: string) => {
    setSchemas(prev => prev.map(s =>
      s.id === schemaId ? { ...s, fields: s.fields.filter(f => f.id !== fieldId) } : s
    ));
  };

  const handleUpdateField = (schemaId: string, fieldId: string, updates: Partial<Field>) => {
    setSchemas(prev => prev.map(s =>
      s.id === schemaId ? {
        ...s,
        fields: s.fields.map(f => f.id === fieldId ? { ...f, ...updates } : f)
      } : s
    ));
  };

  // Table CRUD operations
  const handleDeleteTable = (tableId: string) => {
    setTables(prev => prev.filter(t => t.id !== tableId));
  };

  const handleUpdateTable = (tableId: string, updates: Partial<Omit<TableItem, 'id' | 'rows'>>) => {
    setTables(prev => prev.map(t => t.id === tableId ? { ...t, ...updates } : t));
  };

  const handleDuplicateTable = (tableId: string) => {
    const table = tables.find(t => t.id === tableId);
    if (table) {
      const newTable: TableItem = {
        ...table,
        id: generateId(),
        name: `${table.name} (Copy)`,
        rows: table.rows.map(r => ({ ...r, id: generateId() }))
      };
      setTables(prev => [...prev, newTable]);
    }
  };

  // Row CRUD operations
  const handleAddRow = (tableId: string, row: Omit<TableRow, 'id'>) => {
    const newRow: TableRow = { ...row, id: generateId() };
    setTables(prev => prev.map(t =>
      t.id === tableId ? { ...t, rows: [newRow, ...t.rows] } : t
    ));
  };

  const handleDeleteRow = (tableId: string, rowId: string) => {
    setTables(prev => prev.map(t =>
      t.id === tableId ? { ...t, rows: t.rows.filter(r => r.id !== rowId) } : t
    ));
  };

  const handleUpdateRow = (tableId: string, rowId: string, updates: Partial<TableRow>) => {
    setTables(prev => prev.map(t =>
      t.id === tableId ? {
        ...t,
        rows: t.rows.map(r => r.id === rowId ? { ...r, ...updates } : r)
      } : t
    ));
  };

  const handleToggleRowValidation = (tableId: string, rowId: string) => {
    setTables(prev => prev.map(t =>
      t.id === tableId ? {
        ...t,
        rows: t.rows.map(r => r.id === rowId ? { ...r, validated: !r.validated } : r)
      } : t
    ));
  };

  const handleValidateAllRows = (tableId: string) => {
    setTables(prev => prev.map(t =>
      t.id === tableId ? {
        ...t,
        rows: t.rows.map(r => ({ ...r, validated: true })),
        validation: 'Done' as const
      } : t
    ));
  };

  const stats = [
    { label: 'Devices', value: String(DEVICES.length) },
    { label: 'Online', value: String(DEVICES.filter(d => d.status === 'online').length) },
    { label: 'Offline', value: String(DEVICES.filter(d => d.status === 'offline').length) },
    { label: 'Schemas', value: String(schemas.length) }
  ];

  const stepConfigs = [
    {
      title: 'Gateway & Device Setup',
      steps: SCAN_STEPS,
      currentIndex: currentStepIndex,
      isVisible: true,
      isExpanded: isSetupExpanded,
      onToggle: () => setIsSetupExpanded(!isSetupExpanded),
      isCompleted: true,
      completionMessage: 'Gateway & Device Setup completed successfully.',
      actions: [{ label: 'Review & Modify Devices', onClick: () => setActiveTab('connected devices') }]
    },
    {
      title: 'Schema Creation',
      steps: SCHEMA_STEPS,
      currentIndex: mappingStepIndex,
      isVisible: isStep2Visible,
      isExpanded: isSchemaExpanded,
      onToggle: () => setIsSchemaExpanded(!isSchemaExpanded),
      isCompleted: mappingStepIndex === SCHEMA_STEPS.length,
      completionMessage: 'Schema Creation completed successfully.',
      actions: [{ label: 'Edit Schemas', onClick: () => setActiveTab('schemas') }]
    },
    {
      title: 'Table Creation',
      steps: TABLE_STEPS,
      currentIndex: tableStepIndex,
      isVisible: isStep3Visible,
      isExpanded: isTableExpanded,
      onToggle: () => setIsTableExpanded(!isTableExpanded),
      isCompleted: tableStepIndex === TABLE_STEPS.length,
      completionMessage: 'Table creation completed successfully.',
      actions: [{ label: 'Review Tables', onClick: () => setActiveTab('tables') }]
    }
  ];

  return (
    <div className="h-screen w-full bg-gray-50 flex flex-col font-sans overflow-hidden">
      <AddTableModal
        isOpen={isAddTableModalOpen}
        onClose={() => setIsAddTableModalOpen(false)}
        devices={DEVICES}
        schemas={schemas.map(s => s.name)}
      />

      <div className="flex-1 flex gap-3 p-3 overflow-hidden">
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <Header
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            tabs={tabs}
            isTabClickable={isTabClickable}
            completedSteps={completedSteps}
          />

          <div className="flex-1 overflow-hidden">
            {activeTab === 'connected devices' && (
              <DeviceMapView
                devices={DEVICES}
                selectedDeviceId={selectedDeviceId}
                setSelectedDeviceId={setSelectedDeviceId}
              />
            )}
            {activeTab === 'schemas' && (
              <SchemasView
                schemas={schemas}
                onAddSchema={handleAddSchema}
                onDeleteSchema={handleDeleteSchema}
                onUpdateSchema={handleUpdateSchema}
                onDuplicateSchema={handleDuplicateSchema}
                onAddField={handleAddField}
                onDeleteField={handleDeleteField}
                onUpdateField={handleUpdateField}
              />
            )}
            {activeTab === 'tables' && (
              <TablesView
                tables={tables}
                onAddTable={() => setIsAddTableModalOpen(true)}
                onDeleteTable={handleDeleteTable}
                onUpdateTable={handleUpdateTable}
                onDuplicateTable={handleDuplicateTable}
                onAddRow={handleAddRow}
                onDeleteRow={handleDeleteRow}
                onUpdateRow={handleUpdateRow}
                onToggleRowValidation={handleToggleRowValidation}
                onValidateAllRows={handleValidateAllRows}
              />
            )}
          </div>
        </div>

        <AIChatPanel
          chatInput={chatInput}
          setChatInput={setChatInput}
          chatHistory={chatHistory}
          isLoading={isLoading}
          onSubmit={handleChatSubmit}
          stepConfigs={stepConfigs}
          stats={stats}
          activeTab={activeTab}
        />
      </div>
    </div>
  );
}
