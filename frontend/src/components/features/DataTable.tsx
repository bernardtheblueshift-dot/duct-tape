import { cn } from '@/lib/utils';

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  className?: string;
  hideOnMobile?: boolean;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
  renderMobileCard: (item: T) => React.ReactNode;
  emptyMessage?: string;
  loading?: boolean;
}

export function DataTable<T extends { id: string }>({
  data, columns, onRowClick, renderMobileCard, emptyMessage = 'No data', loading
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1,2,3].map(i => (
          <div key={i} className="h-16 rounded-lg bg-surface animate-pulse" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return <div className="text-center py-12 text-muted font-mono text-sm">{emptyMessage}</div>;
  }

  return (
    <>
      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {columns.filter(c => !c.hideOnMobile).map(col => (
                <th key={col.key} className={cn("text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-4", col.className)}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map(item => (
              <tr
                key={item.id}
                onClick={() => onRowClick?.(item)}
                className={cn(
                  "border-b border-dashed border-border hover:bg-surface-hover transition-colors",
                  onRowClick && "cursor-pointer"
                )}
              >
                {columns.filter(c => !c.hideOnMobile).map(col => (
                  <td key={col.key} className={cn("py-3 px-4 text-sm", col.className)}>
                    {col.render(item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card layout */}
      <div className="md:hidden space-y-3">
        {data.map(item => (
          <div
            key={item.id}
            onClick={() => onRowClick?.(item)}
            className={cn(
              "rounded-lg border border-border bg-surface p-4 hover:border-border-hover transition-colors",
              onRowClick && "cursor-pointer"
            )}
          >
            {renderMobileCard(item)}
          </div>
        ))}
      </div>
    </>
  );
}
