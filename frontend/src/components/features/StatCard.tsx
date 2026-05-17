import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  className?: string;
  trend?: string;
}

export function StatCard({ label, value, icon: Icon, className, trend }: StatCardProps) {
  return (
    <div className={cn(
      "rounded-lg border border-border bg-surface p-5 hover:border-border-hover transition-colors",
      "group",
      className
    )}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-muted">{label}</span>
        <Icon className="h-4 w-4 text-muted group-hover:text-primary transition-colors" />
      </div>
      <div className="font-mono text-3xl font-bold tracking-tight">{value}</div>
      {trend && <p className="text-xs text-muted-foreground font-mono mt-1">{trend}</p>}
    </div>
  );
}
