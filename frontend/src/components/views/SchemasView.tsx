import React, { useState } from 'react';
import { Search, SlidersHorizontal, Plus, Copy, Trash2, MoreHorizontal, MoreVertical, Pencil, Check, X } from 'lucide-react';
import { Field, Schema } from '../../types';

interface SchemasViewProps {
  schemas: Schema[];
  onAddSchema: (name: string) => void;
  onDeleteSchema: (schemaId: string) => void;
  onUpdateSchema: (schemaId: string, name: string) => void;
  onDuplicateSchema: (schemaId: string) => void;
  onAddField: (schemaId: string, field: Omit<Field, 'id'>) => void;
  onDeleteField: (schemaId: string, fieldId: string) => void;
  onUpdateField: (schemaId: string, fieldId: string, updates: Partial<Field>) => void;
}

interface FieldFilterState {
  dataType: string[];
  unit: string[];
}

export const SchemasView: React.FC<SchemasViewProps> = ({
  schemas,
  onAddSchema,
  onDeleteSchema,
  onUpdateSchema,
  onDuplicateSchema,
  onAddField,
  onDeleteField,
  onUpdateField
}) => {
  const [selectedSchemaId, setSelectedSchemaId] = useState(schemas[0]?.id || '');
  const [isAddingField, setIsAddingField] = useState(false);
  const [isAddingSchema, setIsAddingSchema] = useState(false);
  const [newSchemaName, setNewSchemaName] = useState('');
  const [editingSchemaId, setEditingSchemaId] = useState<string | null>(null);
  const [editingSchemaName, setEditingSchemaName] = useState('');
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<Field | null>(null);
  const [newField, setNewField] = useState<Omit<Field, 'id'>>({ name: '', type: '', unit: '', scale: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [schemaSearchQuery, setSchemaSearchQuery] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [filters, setFilters] = useState<FieldFilterState>({ dataType: [], unit: [] });

  const selectedSchema = schemas.find(s => s.id === selectedSchemaId);

  // Filter schemas by search
  const filteredSchemas = schemas.filter(s =>
    s.name.toLowerCase().includes(schemaSearchQuery.toLowerCase())
  );

  // Filter fields by search and filters
  const filteredFields = (selectedSchema?.fields || []).filter(f => {
    const matchesSearch = f.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filters.dataType.length === 0 || filters.dataType.includes(f.type);
    const matchesUnit = filters.unit.length === 0 || filters.unit.includes(f.unit);
    return matchesSearch && matchesType && matchesUnit;
  });

  const toggleFilter = (category: keyof FieldFilterState, value: string) => {
    setFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }));
  };

  const clearFilters = () => {
    setFilters({ dataType: [], unit: [] });
  };

  const activeFilterCount = Object.values(filters).flat().length;

  const handleAddSchema = () => {
    if (!newSchemaName.trim()) return;
    onAddSchema(newSchemaName.trim());
    setNewSchemaName('');
    setIsAddingSchema(false);
  };

  const handleSaveSchemaName = () => {
    if (!editingSchemaName.trim() || !editingSchemaId) return;
    onUpdateSchema(editingSchemaId, editingSchemaName.trim());
    setEditingSchemaId(null);
    setEditingSchemaName('');
  };

  const handleDeleteSchema = (schemaId: string) => {
    onDeleteSchema(schemaId);
    if (selectedSchemaId === schemaId && schemas.length > 1) {
      const remaining = schemas.filter(s => s.id !== schemaId);
      setSelectedSchemaId(remaining[0]?.id || '');
    }
  };

  const handleAddField = () => {
    if (!newField.name || !selectedSchemaId) return;
    onAddField(selectedSchemaId, newField);
    setIsAddingField(false);
    setNewField({ name: '', type: '', unit: '', scale: '' });
  };

  const handleSaveFieldEdit = () => {
    if (!editingField || !editingFieldId || !selectedSchemaId) return;
    onUpdateField(selectedSchemaId, editingFieldId, editingField);
    setEditingFieldId(null);
    setEditingField(null);
  };

  const startEditingField = (field: Field) => {
    setEditingFieldId(field.id);
    setEditingField({ ...field });
  };

  return (
    <div className="flex-1 flex gap-3 h-full overflow-hidden">
      {/* Schemas List */}
      <div className="w-72 bg-white rounded-xl border border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-100 flex flex-col gap-3">
          <div className="flex justify-between items-center">
            <h2 className="font-bold text-gray-800 text-lg">Schemas</h2>
            <button
              onClick={() => setIsAddingSchema(true)}
              className="w-9 h-9 bg-gray-700 rounded-lg flex items-center justify-center text-white hover:bg-black"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search schemas..."
              value={schemaSearchQuery}
              onChange={(e) => setSchemaSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none text-sm"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {isAddingSchema && (
            <div className="p-3 rounded-lg border border-blue-300 bg-blue-50">
              <input
                type="text"
                placeholder="Schema name..."
                className="w-full px-3 py-2 border rounded-lg text-sm font-bold mb-2"
                value={newSchemaName}
                onChange={(e) => setNewSchemaName(e.target.value)}
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleAddSchema()}
              />
              <div className="flex justify-end gap-2">
                <button onClick={() => { setIsAddingSchema(false); setNewSchemaName(''); }} className="p-2 border rounded-lg hover:bg-white">
                  <X className="w-4 h-4" />
                </button>
                <button onClick={handleAddSchema} className="p-2 bg-gray-700 text-white rounded-lg hover:bg-black">
                  <Check className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
          {filteredSchemas.map((schema) => {
            const isSelected = selectedSchemaId === schema.id;
            const isEditing = editingSchemaId === schema.id;
            return (
              <div
                key={schema.id}
                onClick={() => !isEditing && setSelectedSchemaId(schema.id)}
                className={`group flex items-center justify-between p-3 rounded-lg border transition-all cursor-pointer
                  ${isSelected ? 'bg-gray-50 border-gray-300 ring-1 ring-gray-200' : 'bg-white border-transparent hover:bg-gray-50 hover:border-gray-200'}`}
              >
                {isEditing ? (
                  <div className="flex-1 flex items-center gap-2">
                    <input
                      type="text"
                      className="flex-1 px-2 py-1 border rounded text-sm font-bold"
                      value={editingSchemaName}
                      onChange={(e) => setEditingSchemaName(e.target.value)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveSchemaName();
                        if (e.key === 'Escape') { setEditingSchemaId(null); setEditingSchemaName(''); }
                      }}
                    />
                    <button onClick={(e) => { e.stopPropagation(); handleSaveSchemaName(); }} className="p-1 bg-gray-700 text-white rounded hover:bg-black">
                      <Check className="w-3 h-3" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); setEditingSchemaId(null); }} className="p-1 border rounded hover:bg-gray-100">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded accent-blue-500"
                        checked={isSelected}
                        onChange={() => setSelectedSchemaId(schema.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="font-bold text-gray-800 truncate text-sm">{schema.name}</span>
                    </div>
                    <span className="text-gray-400 text-xs px-2 whitespace-nowrap">{schema.fields.length} fields</span>
                    <div className="flex gap-1 text-gray-400">
                      {isSelected ? (
                        <>
                          <Pencil
                            className="w-4 h-4 cursor-pointer hover:text-gray-600"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingSchemaId(schema.id);
                              setEditingSchemaName(schema.name);
                            }}
                          />
                          <Copy
                            className="w-4 h-4 cursor-pointer hover:text-gray-600"
                            onClick={(e) => { e.stopPropagation(); onDuplicateSchema(schema.id); }}
                          />
                          <Trash2
                            className="w-4 h-4 cursor-pointer hover:text-red-500"
                            onClick={(e) => { e.stopPropagation(); handleDeleteSchema(schema.id); }}
                          />
                        </>
                      ) : (
                        <MoreHorizontal className="w-4 h-4 opacity-0 group-hover:opacity-100" />
                      )}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Fields Table */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h3 className="font-bold text-gray-700">{selectedSchema?.name || 'Select a schema'}</h3>
            <div className="flex gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search fields"
                  className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-48 bg-gray-50 focus:outline-none text-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowFilter(!showFilter)}
                  className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium ${activeFilterCount > 0 ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
                >
                  <SlidersHorizontal className="w-4 h-4" /> Filter
                  {activeFilterCount > 0 && (
                    <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">{activeFilterCount}</span>
                  )}
                </button>

                {/* Filter Dropdown */}
                {showFilter && (
                  <div className="absolute top-full right-0 mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-4">
                    <div className="flex justify-between items-center mb-3">
                      <span className="font-bold text-gray-800">Filters</span>
                      {activeFilterCount > 0 && (
                        <button onClick={clearFilters} className="text-xs text-blue-600 hover:underline">Clear all</button>
                      )}
                    </div>

                    {/* Data Type Filter */}
                    <div className="mb-3">
                      <span className="text-xs font-bold text-gray-500 uppercase">Data Type</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {['float', 'int16', 'int32', 'uint16', 'uint32', 'bool'].map(type => (
                          <button
                            key={type}
                            onClick={() => toggleFilter('dataType', type)}
                            className={`px-2 py-1 rounded text-xs font-medium border ${filters.dataType.includes(type) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                          >
                            {type}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Unit Filter */}
                    <div>
                      <span className="text-xs font-bold text-gray-500 uppercase">Unit</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {['Volt', 'Ampere', 'kW', 'kVAR', 'kVA', 'Hz', 'PF', '%'].map(unit => (
                          <button
                            key={unit}
                            onClick={() => toggleFilter('unit', unit)}
                            className={`px-2 py-1 rounded text-xs font-medium border ${filters.unit.includes(unit) ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'}`}
                          >
                            {unit}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <span className="text-sm text-gray-400">{filteredFields.length} of {selectedSchema?.fields.length || 0} fields</span>
          </div>
          <button
            onClick={() => setIsAddingField(true)}
            disabled={!selectedSchema}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg font-bold hover:bg-black text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add field
          </button>
        </div>
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100 sticky top-0">
              <tr className="text-gray-400 font-bold uppercase text-xs">
                <th className="px-4 py-3 w-[30%]">Field Name</th>
                <th className="px-4 py-3 w-[15%]">Data Type</th>
                <th className="px-4 py-3 w-[20%]">Unit</th>
                <th className="px-4 py-3 w-[15%]">Scale Factor</th>
                <th className="px-4 py-3 text-right w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isAddingField && selectedSchema && (
                <tr className="bg-blue-50/30">
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="e.g. Voltage L1-N"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                      value={newField.name}
                      onChange={(e) => setNewField({ ...newField, name: e.target.value })}
                      autoFocus
                    />
                  </td>
                  <td className="px-4 py-3">
                    <select
                      className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                      value={newField.type}
                      onChange={(e) => setNewField({ ...newField, type: e.target.value })}
                    >
                      <option value="">Select</option>
                      <option value="float">float</option>
                      <option value="int16">int16</option>
                      <option value="int32">int32</option>
                      <option value="uint16">uint16</option>
                      <option value="uint32">uint32</option>
                      <option value="bool">bool</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                      value={newField.unit}
                      onChange={(e) => setNewField({ ...newField, unit: e.target.value })}
                    >
                      <option value="">Select</option>
                      <option value="Volt">Volt (V)</option>
                      <option value="Ampere">Ampere (A)</option>
                      <option value="kW">Kilowatt (kW)</option>
                      <option value="kVAR">Kilovar (kVAR)</option>
                      <option value="kVA">Kilovolt-Amp (kVA)</option>
                      <option value="kWh">Kilowatt-hour (kWh)</option>
                      <option value="Hz">Hertz (Hz)</option>
                      <option value="PF">Power Factor</option>
                      <option value="Celsius">Celsius (C)</option>
                      <option value="%RH">Humidity (%RH)</option>
                      <option value="%">Percentage (%)</option>
                      <option value="hPa">Pressure (hPa)</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      placeholder="0.1"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                      value={newField.scale}
                      onChange={(e) => setNewField({ ...newField, scale: e.target.value })}
                    />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => { setIsAddingField(false); setNewField({ name: '', type: '', unit: '', scale: '' }); }} className="p-2 border rounded-lg hover:bg-gray-50">
                        <X className="w-4 h-4" />
                      </button>
                      <button onClick={handleAddField} className="p-2 bg-gray-700 text-white rounded-lg hover:bg-black">
                        <Check className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )}
              {filteredFields.map((field) => {
                const isEditing = editingFieldId === field.id;
                return (
                  <tr key={field.id} className="hover:bg-gray-50 group">
                    {isEditing && editingField ? (
                      <>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                            value={editingField.name}
                            onChange={(e) => setEditingField({ ...editingField, name: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <select
                            className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                            value={editingField.type}
                            onChange={(e) => setEditingField({ ...editingField, type: e.target.value })}
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
                          <select
                            className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                            value={editingField.unit}
                            onChange={(e) => setEditingField({ ...editingField, unit: e.target.value })}
                          >
                            <option value="Volt">Volt (V)</option>
                            <option value="Ampere">Ampere (A)</option>
                            <option value="kW">Kilowatt (kW)</option>
                            <option value="kVAR">Kilovar (kVAR)</option>
                            <option value="kVA">Kilovolt-Amp (kVA)</option>
                            <option value="kWh">Kilowatt-hour (kWh)</option>
                            <option value="Hz">Hertz (Hz)</option>
                            <option value="PF">Power Factor</option>
                            <option value="Celsius">Celsius (C)</option>
                            <option value="%RH">Humidity (%RH)</option>
                            <option value="%">Percentage (%)</option>
                            <option value="hPa">Pressure (hPa)</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-bold"
                            value={editingField.scale}
                            onChange={(e) => setEditingField({ ...editingField, scale: e.target.value })}
                          />
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button onClick={() => { setEditingFieldId(null); setEditingField(null); }} className="p-2 border rounded-lg hover:bg-gray-50">
                              <X className="w-4 h-4" />
                            </button>
                            <button onClick={handleSaveFieldEdit} className="p-2 bg-gray-700 text-white rounded-lg hover:bg-black">
                              <Check className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-3 font-bold text-gray-700 text-sm">{field.name}</td>
                        <td className="px-4 py-3 text-gray-500 text-sm font-mono">{field.type}</td>
                        <td className="px-4 py-3 text-gray-500 text-sm">{field.unit}</td>
                        <td className="px-4 py-3 text-gray-500 text-sm font-mono">{field.scale}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="hidden group-hover:flex justify-end gap-2 text-gray-400">
                            <Pencil
                              className="w-4 h-4 cursor-pointer hover:text-gray-600"
                              onClick={() => startEditingField(field)}
                            />
                            <Trash2
                              className="w-4 h-4 cursor-pointer hover:text-red-500"
                              onClick={() => selectedSchemaId && onDeleteField(selectedSchemaId, field.id)}
                            />
                          </div>
                          <MoreVertical className="w-4 h-4 text-gray-400 group-hover:hidden ml-auto" />
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

      {/* Click outside to close filter */}
      {showFilter && (
        <div className="fixed inset-0 z-40" onClick={() => setShowFilter(false)} />
      )}
    </div>
  );
};
