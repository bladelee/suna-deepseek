'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { cn } from '@/lib/utils';

// Simple iframe-based PDF viewer for Electron compatibility
interface PdfDocumentProps {
    url: string;
    containerWidth: number | null;
}

const PdfDocument = ({ url, containerWidth }: PdfDocumentProps) => {
    return (
        <iframe
            src={url}
            width={containerWidth ?? '100%'}
            height="600"
            className="border border-border rounded bg-white"
            style={{ minHeight: '400px' }}
        />
    );
};

// Dynamic import to avoid SSR issues
const DynamicPdfDocument = dynamic(() => Promise.resolve(PdfDocument), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center bg-muted/20">
            <div className="text-sm text-muted-foreground">Loading PDF...</div>
        </div>
    )
});

interface PdfRendererProps {
    url?: string | null;
    className?: string;
}

// Minimal inline PDF preview for attachment grid. No toolbar. First page only.
export function PdfRenderer({ url, className }: PdfRendererProps) {
    const [containerWidth, setContainerWidth] = React.useState<number | null>(null);
    const wrapperRef = React.useRef<HTMLDivElement | null>(null);

    React.useEffect(() => {
        if (!wrapperRef.current) return;
        const element = wrapperRef.current;
        const setWidth = () => setContainerWidth(element.clientWidth);
        setWidth();
        const observer = new ResizeObserver(() => setWidth());
        observer.observe(element);
        return () => observer.disconnect();
    }, []);

    if (!url) {
        return (
            <div className={cn('w-full h-full flex items-center justify-center bg-muted/20', className)} />
        );
    }

    return (
        <div ref={wrapperRef} className={cn('w-full h-full overflow-auto bg-background', className)}>
            <div className="flex justify-center">
                <DynamicPdfDocument url={url} containerWidth={containerWidth} />
            </div>
        </div>
    );
}


