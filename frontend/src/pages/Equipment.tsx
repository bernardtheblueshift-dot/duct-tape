import { useState } from 'react';
import { useEquipmentList, useCreateEquipment, useUpdateEquipment, useDeleteEquipment, useUpdateCondition } from '@/hooks/useEquipment';
import { DataTable } from '@/components/features/DataTable';
import type { EquipmentCondition } from '@/types/api';
import { Pencil, Trash2, X, Check } from 'lucide-react';

type ConditionConfig = {
  label: string;
  className: string;
};

const CONDITION_STYLES: Record<EquipmentCondition, ConditionConfig> = {
  good: { label: 'GOOD', className: 'bg-job-active/20 text-job-active' },
  fair: { label: 'FAIR', className: 'bg-job-simmer/20 text-job-simmer' },
  poor: { label: 'POOR', className: 'bg-destructive/20 text-destructive' },
  maintenance: { label: 'MAINT', className: 'bg-muted/20 text-muted' },
};

export function EquipmentPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [condition, setCondition] = useState<string | undefined>(undefined);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data: equipment, isLoading } = useEquipmentList({
    search: search || undefined,
    category,
    condition
  });
  const createMutation = useCreateEquipment();
  const updateMutation = useUpdateEquipment();
  const deleteMutation = useDeleteEquipment();
  const updateConditionMutation = useUpdateCondition();

  // Collect unique categories for filter
  const allCategories = Array.from(
    new Set(equipment?.map(e => e.category).filter((c): c is string => c !== null) || [])
  ).sort();

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    createMutation.mutate({
      name: formData.get('name') as string,
      category: (formData.get('category') as string) || null,
      quantity: parseInt(formData.get('quantity') as string) || 1,
      condition: (formData.get('condition') as EquipmentCondition) || 'good',
      notes: (formData.get('notes') as string) || null,
      serial_number: (formData.get('serial_number') as string) || null,
    }, {
      onSuccess: () => {
        setShowAddForm(false);
        e.currentTarget.reset();
      },
    });
  };

  const handleUpdate = (id: string, e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    updateMutation.mutate({
      id,
      data: {
        name: formData.get('name') as string,
        category: (formData.get('category') as string) || null,
        quantity: parseInt(formData.get('quantity') as string),
        condition: formData.get('condition') as EquipmentCondition,
        notes: (formData.get('notes') as string) || null,
        serial_number: (formData.get('serial_number') as string) || null,
      },
    }, {
      onSuccess: () => setEditingId(null),
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete this equipment? This cannot be undone.')) {
      deleteMutation.mutate(id);
    }
  };

  const handleConditionChange = (id: string, newCondition: EquipmentCondition) => {
    updateConditionMutation.mutate({ id, condition: newCondition });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Equipment</h1>
          <p className="text-muted font-mono text-sm">// inventory</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Equipment'}
        </button>
      </div>

      {/* Add form */}
      {showAddForm && (
        <form onSubmit={handleCreate} className="rounded-lg border border-border bg-surface p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="text"
              name="name"
              placeholder="Name *"
              required
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <input
              type="text"
              name="category"
              placeholder="Category"
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <input
              type="number"
              name="quantity"
              placeholder="Quantity"
              defaultValue={1}
              min={1}
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <select
              name="condition"
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
              <option value="maintenance">Maintenance</option>
            </select>
            <input
              type="text"
              name="serial_number"
              placeholder="Serial Number"
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <input
              type="text"
              name="notes"
              placeholder="Notes"
              className="px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="Search equipment..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-3 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <select
          value={category || ''}
          onChange={(e) => setCategory(e.target.value || undefined)}
          className="px-3 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="">All Categories</option>
          {allCategories.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          value={condition || ''}
          onChange={(e) => setCondition(e.target.value || undefined)}
          className="px-3 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="">All Conditions</option>
          <option value="good">Good</option>
          <option value="fair">Fair</option>
          <option value="poor">Poor</option>
          <option value="maintenance">Maintenance</option>
        </select>
      </div>

      {/* Data table */}
      <DataTable
        data={equipment || []}
        columns={[
          {
            key: 'name',
            header: 'Name',
            render: (item) => {
              if (editingId === item.id) {
                return (
                  <form onSubmit={(e) => handleUpdate(item.id, e)} className="flex gap-2">
                    <input
                      type="text"
                      name="name"
                      defaultValue={item.name}
                      required
                      className="px-2 py-1 rounded border border-border bg-background text-sm"
                    />
                    <input type="hidden" name="category" defaultValue={item.category ?? ''} />
                    <input type="hidden" name="quantity" defaultValue={item.quantity} />
                    <input type="hidden" name="condition" defaultValue={item.condition} />
                    <input type="hidden" name="notes" defaultValue={item.notes ?? ''} />
                    <input type="hidden" name="serial_number" defaultValue={item.serial_number ?? ''} />
                    <button type="submit" className="p-1 text-green-500"><Check className="h-4 w-4" /></button>
                    <button type="button" onClick={() => setEditingId(null)} className="p-1 text-muted"><X className="h-4 w-4" /></button>
                  </form>
                );
              }
              return <span className="font-medium">{item.name}</span>;
            },
          },
          {
            key: 'category',
            header: 'Category',
            render: (item) => item.category || <span className="text-muted">—</span>,
            className: 'hidden sm:table-cell',
            hideOnMobile: true,
          },
          {
            key: 'quantity',
            header: 'Qty',
            render: (item) => <span className="font-mono text-sm">{item.quantity}</span>,
          },
          {
            key: 'condition',
            header: 'Condition',
            render: (item) => {
              const config = CONDITION_STYLES[item.condition];
              return (
                <select
                  value={item.condition}
                  onChange={(e) => handleConditionChange(item.id, e.target.value as EquipmentCondition)}
                  className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${config.className} border-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/50`}
                >
                  {Object.entries(CONDITION_STYLES).map(([value, cfg]) => (
                    <option key={value} value={value}>{cfg.label}</option>
                  ))}
                </select>
              );
            },
          },
          {
            key: 'serial',
            header: 'Serial',
            render: (item) => (
              <span className="font-mono text-xs text-muted">
                {item.serial_number || '—'}
              </span>
            ),
            className: 'hidden md:table-cell',
            hideOnMobile: true,
          },
          {
            key: 'actions',
            header: 'Actions',
            render: (item) => (
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingId(item.id)}
                  className="p-1 rounded hover:bg-surface-hover transition-colors"
                  title="Edit"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ),
          },
        ]}
        renderMobileCard={(item) => {
          const config = CONDITION_STYLES[item.condition];
          return (
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <div className="font-medium">{item.name}</div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingId(item.id)}
                    className="p-1 rounded hover:bg-surface-hover transition-colors"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              {item.category && <div className="text-sm text-muted">{item.category}</div>}
              <div className="flex justify-between items-center">
                <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${config.className}`}>
                  {config.label}
                </span>
                <span className="font-mono text-sm">Qty: {item.quantity}</span>
              </div>
              {item.serial_number && (
                <div className="text-xs text-muted font-mono">{item.serial_number}</div>
              )}
            </div>
          );
        }}
        emptyMessage="No equipment found"
        loading={isLoading}
      />
    </div>
  );
}
