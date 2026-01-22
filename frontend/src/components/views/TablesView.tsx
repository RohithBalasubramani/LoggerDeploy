import React, { useState } from 'react';
import { Search, Plus, MoreVertical, Unlink, CheckCircle2, Clock, Pencil, Link, Trash2, Copy, Check, X, SlidersHorizontal } from 'lucide-react';
import { TableItem, TableRow } from '../../types';

interface TablesViewProps {
  tables: TableItem[];
  onAddTable: () => void;
  onDeleteTable: (tableId: string) => void;
  onUpdateTable: (tableId: string, updates: Partial<Omit<TableItem, 'id' | 'rows'>>) => void;
  onDuplicateTable: (tableId: string) => void;
  onAddRow: (tableId: string, row: Omit<TableRow, 'id'>) => void;
  onDeleteRow: (tableId: string, rowId: string) => void;
  onUpdateRow: (tableId: string, rowId: string, updates: Partial<TableRow>) => void;
  onToggleRowValidation: (tableId: string, rowId: string) => void;
  onValidateAllRows: (tableId: string) => void;
}

interface TableFilterState {
  status: string[];
  type: string[];
}

interface RowFilterState {
  validation: string[];
  dataType: string[];
}

export const TablesView: React.FC<TablesViewProps> = ({
  tables,
  onAddTable,
  onDeleteTable,
  onUpdateTable,
  onDuplicateTable,
  onAddRow,
  onDeleteRow,
  onUpdateRow,
  onToggleRowValidation,
  onValidateAllRows
}) => {
  const [selectedTableId, setSelectedTableId] = useState(tables[0]?.id || '');
  const [editingTableId, setEditingTableId] = useState<string | null>(null);
  const [editingTableName, setEditingTableName] = useState('');
  const [isAddingRow, setIsAddingRow] = useState(false);
  const [editingRowId, setEditingRowId] = useState<string | null>(null);
  const [editingRow, setEditingRow] = useState<TableRow | null>(null);
  const [newRow, setNewRow] = useState<Omit<TableRow, 'id'>>({
    validated: false,
    key: '',
    address: '',
    dataType: 'float',
    scale: '1',
    deadband: '0'
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [tableSearchQuery, setTableSearchQuery] = useState('');
  const [showTableFilter, setShowTableFilter] = useState(false);
  const [showRowFilter, setShowRowFilter] = useState(false);
  const [tableFilters, setTableFilters] = useState<TableFilterState>({ status: [], type: [] });
  const [rowFilters, setRowFilters] = useState<RowFilterState>({ validation: [], dataType: [] });

  // Filter tables
  const filteredTables = tables.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(tableSearchQuery.toLowerCase()) ||
      t.device.toLowerCase().includes(tableSearchQuery.toLowerCase());
    const tablePending = t.rows.filter(r => !r.validated).length;
    const isFullyValidated = tablePending === 0 && t.rows.length > 0;
    const matchesStatus = tableFilters.status.length === 0 ||
      (tableFilters.status.includes('validated') && isFullyValidated) ||
      (tableFilters.status.includes('pending') && !isFullyValidated);
    const matchesType = tableFilters.type.length === 0 || tableFilters.type.includes(t.type);
    return matchesSearch && matchesStatus && matchesType;
  });

  const selectedTable = tables.find(t => t.id === selectedTableId);
  const rows = selectedTable?.rows || [];

  // Filter rows
  const filteredRows = rows.filter(r => {
    const matchesSearch = r.key.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesValidation = rowFilters.validation.length === 0 ||
      (rowFilters.validation.includes('validated') && r.validated) ||
      (rowFilters.validation.includes('pending') && !r.validated);
    const matchesDataType = rowFilters.dataType.length === 0 || rowFilters.dataType.includes(r.dataType);
    return matchesSearch && matchesValidation && matchesDataType;
  });

  const pendingCount = rows.filter(r => !r.validated).length;
  const validatedCount = rows.filter(r => r.validated).length;

  const toggleTableFilter = (category: keyof TableFilterState, value: string) => {
    setTableFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }));
  };

  const toggleRowFilter = (category: keyof RowFilterState, value: string) => {
    setRowFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }));
  };

  const clearTableFilters = () => setTableFilters({ status: [], type: [] });
  const clearRowFilters = () => setRowFilters({ validation: [], dataType: [] });

  const tableFilterCount = Object.values(tableFilters).flat().length;
  const rowFilterCount = Object.values(rowFilters).flat().length;

  const handleSaveTableName = () => {
    if (!editingTableName.trim() || !editingTableId) return;
    onUpdateTable(editingTableId, { name: editingTableName.trim() });
    setEditingTableId(null);
    setEditingTableName('');
  };

  const handleDeleteTable = (tableId: string) => {
    onDeleteTable(tableId);
    if (selectedTableId === tableId && tables.length > 1) {
      const remaining = tables.filter(t => t.id !== tableId);
      setSelectedTableId(remaining[0]?.id || '');
    }
  };

  const handleAddRow = () => {
    if (!newRow.key || !selectedTableId) return;
    onAddRow(selectedTableId, newRow);
    setIsAddingRow(false);
    setNewRow({
      validated: false,
      key: '',
      address: '',
      dataType: 'float',
      scale: '1',
      deadband: '0'
    });
  };

  const handleSaveRowEdit = () => {
    if (!editingRow || !editingRowId || !selectedTableId) return;
    onUpdateRow(selectedTableId, editingRowId, editingRow);
    setEditingRowId(null);
    setEditingRow(null);
  };

  const startEditingRow = (row: TableRow) => {
    setEditingRowId(row.id);
    setEditingRow({ ...row });
  };

  return (
    <div className="flex-1 flex gap-3 h-full overflow-hidden">
      {/* Tables List */}
      <div className="w-80 bg-white rounded-xl border border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-100 flex flex-col gap-3">
          <div className="flex justify-between items-center">
            <h2 className="font-bold text-gray-800 text-lg">Tables</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <button
                  onClick={() => setShowTableFilter(!showTableFilter)}
                  className={`p-2 rounded-lg ${tableFilterCount > 0 ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-100 text-gray-400'}`}
                >
                  <SlidersHorizontal className="w-4 h-4" />
                </button>
                {showTableFilter && (
                  <div className="absolute top-full right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-bold text-gray-800 text-sm">Filters</span>
                      {tableFilterCount > 0 && (
                        <button onClick={clearTableFilters} className="text-xs text-blue-600">Clear</button>
                      )}
                    </div>
                    <div className="mb-2">
                      <span className="text-xs font-bold text-gray-500 uppercase">Status</span>
                      <div className="flex gap-2 mt-1">
                        {['validated', 'pending'].map(s => (
                          <button
                            key={s}
                            onClick={() => toggleTableFilter('status', s)}
                            className={`px-2 py-1 rounded text-xs font-medium ${tableFilters.status.includes(s) ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'}`}
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-xs font-bold text-gray-500 uppercase">Mapping</span>
                      <div className="flex gap-2 mt-1">
                        {['map', 'unmap'].map(t => (
                          <button
                            key={t}
                            onClick={() => toggleTableFilter('type', t)}
                            className={`px-2 py-1 rounded text-xs font-medium ${tableFilters.type.includes(t) ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'}`}
                          >
                            {t === 'map' ? 'Mapped' : 'Unmapped'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <button onClick={onAddTable} className="w-9 h-9 bg-gray-700 rounded-lg flex items-center justify-center text-white hover:bg-black">
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search tables..."
              value={tableSearchQuery}
              onChange={(e) => setTableSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none text-sm"
            />
          </div>
          <span className="text-xs text-gray-400">{filteredTables.length} of {tables.length} tables</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filteredTables.map((item) => {
            const isSelected = item.id === selectedTableId;
            const isEditing = editingTableId === item.id;
            const tablePendingCount = item.rows.filter(r => !r.validated).length;
            const isFullyValidated = tablePendingCount === 0 && item.rows.length > 0;

            return (
              <div
                key={item.id}
                onClick={() => !isEditing && setSelectedTableId(item.id)}
                className={`bg-white rounded-lg border p-3 flex flex-col gap-1.5 transition-all cursor-pointer
                  ${isSelected ? 'border-gray-300 ring-1 ring-gray-200 bg-gray-50' : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'}`}
              >
                {isEditing ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      className="flex-1 px-2 py-1 border rounded text-sm font-bold"
                      value={editingTableName}
                      onChange={(e) => setEditingTableName(e.target.value)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveTableName();
                        if (e.key === 'Escape') { setEditingTableId(null); setEditingTableName(''); }
                      }}
                    />
                    <button onClick={(e) => { e.stopPropagation(); handleSaveTableName(); }} className="p-1 bg-gray-700 text-white rounded hover:bg-black">
                      <Check className="w-3 h-3" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); setEditingTableId(null); }} className="p-1 border rounded hover:bg-gray-100">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-gray-800 text-sm">{item.name}</span>
                      <div className="flex items-center gap-2 text-gray-400">
                        {item.type === 'map' ? (
                          <div className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                            <Link className="w-3 h-3" /> Mapped
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                            <Unlink className="w-3 h-3" /> Unmapped
                          </div>
                        )}
                        {isSelected ? (
                          <div className="flex gap-1">
                            <Pencil
                              className="w-4 h-4 cursor-pointer hover:text-gray-600"
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingTableId(item.id);
                                setEditingTableName(item.name);
                              }}
                            />
                            <Copy
                              className="w-4 h-4 cursor-pointer hover:text-gray-600"
                              onClick={(e) => { e.stopPropagation(); onDuplicateTable(item.id); }}
                            />
                            <Trash2
                              className="w-4 h-4 cursor-pointer hover:text-red-500"
                              onClick={(e) => { e.stopPropagation(); handleDeleteTable(item.id); }}
                            />
                          </div>
                        ) : (
                          <MoreVertical className="w-4 h-4 cursor-pointer hover:text-gray-600" />
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-400">Status:</span>
                      <div className={`flex items-center gap-1 ${isFullyValidated ? 'text-green-600' : 'text-amber-500'}`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${isFullyValidated ? 'bg-green-500' : 'bg-amber-400'}`} />
                        <span className="font-medium">{isFullyValidated ? 'Validated' : `${tablePendingCount} pending`}</span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      Device: <span className="text-gray-600 font-medium">{item.device}</span>
                    </div>
                    <div className="text-xs text-gray-400">
                      Schema: <span className="text-gray-600 font-medium">{item.schema}</span>
                    </div>
                    <div className="text-xs text-gray-400 truncate">
                      DB: <span className="text-gray-600 font-mono text-[11px]">{item.db}</span>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Table Detail */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <div>
            <h2 className="font-bold text-gray-800 text-lg">{selectedTable?.name || 'Select a table'}</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {selectedTable?.device} → {selectedTable?.schema}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search rows"
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-48 bg-gray-50 focus:outline-none text-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="relative">
              <button
                onClick={() => setShowRowFilter(!showRowFilter)}
                className={`flex items-center gap-2 px-3 py-2 border rounded-lg text-sm font-medium ${rowFilterCount > 0 ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
              >
                <SlidersHorizontal className="w-4 h-4" />
                {rowFilterCount > 0 && (
                  <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">{rowFilterCount}</span>
                )}
              </button>
              {showRowFilter && (
                <div className="absolute top-full right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-gray-800 text-sm">Row Filters</span>
                    {rowFilterCount > 0 && (
                      <button onClick={clearRowFilters} className="text-xs text-blue-600">Clear</button>
                    )}
                  </div>
                  <div className="mb-2">
                    <span className="text-xs font-bold text-gray-500 uppercase">Validation</span>
                    <div className="flex gap-2 mt-1">
                      {['validated', 'pending'].map(v => (
                        <button
                          key={v}
                          onClick={() => toggleRowFilter('validation', v)}
                          className={`px-2 py-1 rounded text-xs font-medium ${rowFilters.validation.includes(v) ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'}`}
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-gray-500 uppercase">Data Type</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {['float', 'int16', 'int32', 'uint16', 'bool'].map(dt => (
                        <button
                          key={dt}
                          onClick={() => toggleRowFilter('dataType', dt)}
                          className={`px-2 py-1 rounded text-xs font-medium ${rowFilters.dataType.includes(dt) ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'}`}
                        >
                          {dt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-green-600 font-medium">{validatedCount} validated</span>
              <span className="text-gray-300">|</span>
              <span className="text-amber-500 font-medium">{pendingCount} pending</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsAddingRow(true)}
                disabled={!selectedTable}
                className="px-4 py-2 bg-gray-100 rounded-lg text-gray-700 font-bold hover:bg-gray-200 text-sm disabled:opacity-50"
              >
                Add Row
              </button>
              <button
                onClick={() => selectedTableId && onValidateAllRows(selectedTableId)}
                disabled={!selectedTable || pendingCount === 0}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg font-bold hover:bg-black text-sm disabled:opacity-50"
              >
                Validate All
              </button>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100 sticky top-0">
              <tr className="text-gray-400 font-bold text-xs uppercase">
                <th className="px-4 py-3 w-[25%]">Field Name</th>
                <th className="px-4 py-3 text-center">Modbus Address</th>
                <th className="px-4 py-3 text-center">Data Type</th>
                <th className="px-4 py-3 text-center">Scale</th>
                <th className="px-4 py-3 text-center">Deadband</th>
                <th className="px-4 py-3 text-center w-28">Status</th>
                <th className="px-4 py-3 w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isAddingRow && selectedTable && (
                <tr className="bg-blue-50/30">
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="Field name"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                      value={newRow.key}
                      onChange={(e) => setNewRow({ ...newRow, key: e.target.value })}
                      autoFocus
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="40001"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                      value={newRow.address}
                      onChange={(e) => setNewRow({ ...newRow, address: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <select
                      className="w-full px-3 py-2 border rounded-lg text-sm font-mono"
                      value={newRow.dataType}
                      onChange={(e) => setNewRow({ ...newRow, dataType: e.target.value })}
                    >
                      <option value="float">float</option>
                      <option value="int16">int16</option>
                      <option value="int32">int32</option>
                      <option value="uint16">uint16</option>
                      <option value="uint32">uint32</option>
                      <option value="bool">bool</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="1"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                      value={newRow.scale}
                      onChange={(e) => setNewRow({ ...newRow, scale: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="0"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                      value={newRow.deadband}
                      onChange={(e) => setNewRow({ ...newRow, deadband: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-gray-400 text-sm">-</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setIsAddingRow(false)} className="p-2 border rounded-lg hover:bg-gray-50">
                        <X className="w-4 h-4" />
                      </button>
                      <button onClick={handleAddRow} className="p-2 bg-gray-700 text-white rounded-lg hover:bg-black">
                        <Check className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )}
              {filteredRows.map((row) => {
                const isEditing = editingRowId === row.id;
                return (
                  <tr key={row.id} className="hover:bg-gray-50 group">
                    {isEditing && editingRow ? (
                      <>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                            value={editingRow.key}
                            onChange={(e) => setEditingRow({ ...editingRow, key: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                            value={editingRow.address}
                            onChange={(e) => setEditingRow({ ...editingRow, address: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <select
                            className="w-full px-3 py-2 border rounded-lg text-sm font-mono"
                            value={editingRow.dataType}
                            onChange={(e) => setEditingRow({ ...editingRow, dataType: e.target.value })}
                          >
                            <option value="float">float</option>
                            <option value="int16">int16</option>
                            <option value="int32">int32</option>
                            <option value="uint16">uint16</option>
                            <option value="uint32">uint32</option>
                            <option value="bool">bool</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                            value={editingRow.scale}
                            onChange={(e) => setEditingRow({ ...editingRow, scale: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-mono text-center"
                            value={editingRow.deadband}
                            onChange={(e) => setEditingRow({ ...editingRow, deadband: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-gray-400 text-sm">-</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            <button onClick={() => { setEditingRowId(null); setEditingRow(null); }} className="p-2 border rounded-lg hover:bg-gray-50">
                              <X className="w-4 h-4" />
                            </button>
                            <button onClick={handleSaveRowEdit} className="p-2 bg-gray-700 text-white rounded-lg hover:bg-black">
                              <Check className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-3 flex items-center gap-2">
                          {row.validated ? (
                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                          ) : (
                            <Clock className="w-4 h-4 text-amber-400" />
                          )}
                          <span className="font-bold text-sm text-gray-700">{row.key}</span>
                        </td>
                        <td className="px-4 py-3 text-center text-sm font-mono text-gray-600">{row.address}</td>
                        <td className="px-4 py-3 text-center text-sm font-mono text-gray-600">{row.dataType}</td>
                        <td className="px-4 py-3 text-center text-sm font-mono text-gray-600">{row.scale}</td>
                        <td className="px-4 py-3 text-center text-sm font-mono text-gray-600">{row.deadband}</td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => selectedTableId && onToggleRowValidation(selectedTableId, row.id)}
                            className={`text-sm font-bold px-3 py-1 rounded ${
                              row.validated
                                ? 'text-gray-500 hover:text-red-500 hover:bg-red-50'
                                : 'text-green-600 hover:bg-green-50'
                            }`}
                          >
                            {row.validated ? 'Unvalidate' : 'Validate'}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <div className="hidden group-hover:flex justify-end gap-2 text-gray-400">
                            <Pencil
                              className="w-4 h-4 cursor-pointer hover:text-gray-600"
                              onClick={() => startEditingRow(row)}
                            />
                            <Trash2
                              className="w-4 h-4 cursor-pointer hover:text-red-500"
                              onClick={() => selectedTableId && onDeleteRow(selectedTableId, row.id)}
                            />
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Click outside to close filters */}
      {(showTableFilter || showRowFilter) && (
        <div className="fixed inset-0 z-40" onClick={() => { setShowTableFilter(false); setShowRowFilter(false); }} />
      )}
    </div>
  );
};
