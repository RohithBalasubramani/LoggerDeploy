export interface DeviceProtocol {
  type: 'modbus' | 'opcua';
  port: number;
  unitId?: number;  // For Modbus
  endpoint?: string; // For OPC-UA
}

export interface DeviceRegister {
  address: string;
  name: string;
  value: number | string;
  unit: string;
  dataType: string;
}

export interface Device {
  id: string;
  name: string;
  ip: string;
  mac: string;
  type: 'edge' | 'router' | 'mfm';
  room: string;
  status: 'online' | 'offline' | 'warning';
  x: number;
  y: number;
  protocols: DeviceProtocol[];
  manufacturer?: string;
  model?: string;
  firmware?: string;
  registers?: DeviceRegister[];
}

export interface SetupStep {
  id: string;
  label: string;
  status: 'completed' | 'pending' | 'active';
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}

export interface Connection {
  from: string;
  to: string;
}

export interface Field {
  id: string;
  name: string;
  type: string;
  unit: string;
  scale: string;
}

export interface Schema {
  id: string;
  name: string;
  fields: Field[];
}

export interface TableRow {
  id: string;
  validated: boolean;
  key: string;
  address: string;
  dataType: string;
  scale: string;
  deadband: string;
}

export interface TableItem {
  id: string;
  name: string;
  validation: 'Pending' | 'Done';
  device: string;
  schema: string;
  db: string;
  type: 'map' | 'unmap';
  rows: TableRow[];
}
