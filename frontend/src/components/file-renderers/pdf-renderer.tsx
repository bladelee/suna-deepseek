'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface PdfRendererProps {
  url: string;
  className?: string;
}

export function PdfRenderer({ url, className }: PdfRendererProps) {
  return (
    <div className={cn('flex flex-col w-full h-full', className)}>
      <div className="flex-1 overflow-auto rounded-md">
        <iframe
          src={url}
          width="100%"
          height="100%"
          className="border-none"
          style={{ minHeight: '500px' }}
        />
      </div>
      
      <div className="flex items-center justify-center p-2 bg-background border-t">
        <span className="text-sm text-muted-foreground">
          PDF viewer - use browser controls to navigate
        </span>
      </div>
    </div>
  );
}
