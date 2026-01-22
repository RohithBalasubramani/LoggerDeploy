# Logger - AI-Guided Industrial Data Acquisition Setup

A visual configuration tool for setting up data logging from industrial Multi-Function Meters (MFMs) and other Modbus devices. The app runs as a service and uses AI to guide users through discovering devices, creating schemas, and configuring database tables.

## What This App Does

This is an **AI-assisted visual agent** that helps configure industrial data acquisition:

1. **Discovers devices** on the network via Modbus TCP/RTU
2. **Reads available registers** from each device (voltage, current, power, etc.)
3. **Creates schemas** based on what data is available
4. **Maps devices to database tables** for continuous logging

### The 3-Step Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Step 1:        │     │  Step 2:        │     │  Step 3:        │
│  DEVICES        │ ──► │  SCHEMAS        │ ──► │  TABLES         │
│                 │     │                 │     │                 │
│  - Scan network │     │  - AI analyzes  │     │  - Link device  │
│  - Find MFMs    │     │    available    │     │    to schema    │
│  - Read IDs     │     │    registers    │     │  - Configure    │
│  - Get IPs      │     │  - Create field │     │    poll rate    │
│                 │     │    definitions  │     │  - Set database │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### AI Chat Panel

The right sidebar is an AI assistant that:
- Guides users through each step
- Helps troubleshoot connection issues
- Suggests schemas based on device type
- Answers questions about Modbus registers

## Real-World Use Case

**Scenario:** Factory with 10 energy meters monitoring different equipment

1. **Connect to Gateway** → AI scans network, finds all MFMs
2. **AI reads registers** → Discovers each meter has voltage, current, power, kWh
3. **Schema created** → "Energy Meter Basic" with 10 fields (V, I, P, PF, Hz, etc.)
4. **Tables created** → Each meter gets a table linked to the schema
5. **Logging starts** → Data flows to PostgreSQL every 5 seconds

## Device Types

| Type | Description | Example Data |
|------|-------------|--------------|
| **MFM** | Multi-Function Meter | Voltage, Current, Power, PF, kWh |
| **Edge** | Modbus Gateway | Acts as network bridge |
| **Router** | Industrial Router | Network infrastructure |

## Schema Fields (Energy Meter Example)

| Field | Type | Unit | Modbus Address |
|-------|------|------|----------------|
| Voltage L1-N | float | Volt | 40001 |
| Voltage L2-N | float | Volt | 40003 |
| Current L1 | float | Ampere | 40007 |
| Active Power | float | kW | 40013 |
| Power Factor | float | PF | 40017 |
| Frequency | float | Hz | 40019 |

## Tech Stack

- **React 19** + TypeScript
- **Vite 6** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`

## Project Structure

```
frontend/src/
├── components/
│   ├── chat/        # AI Chat panel with step progress
│   ├── views/       # DeviceMapView, SchemasView, TablesView
│   ├── devices/     # Device cards and detail panels
│   ├── layout/      # Header navigation
│   └── modals/      # Add table modal
├── types/           # TypeScript interfaces
└── App.tsx          # State management, dummy data
```

## Roadmap

- [ ] Backend service for Modbus scanning
- [ ] Real device discovery via pymodbus
- [ ] AI integration for register analysis
- [ ] Live data streaming to databases
- [ ] Job scheduling (poll intervals)
- [ ] Alert configuration
