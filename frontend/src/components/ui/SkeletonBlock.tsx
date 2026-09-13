import React from 'react';
import { cn } from '../../utils/cn';

export interface SkeletonBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  rounded?: 'control' | 'card' | 'modal' | 'full' | 'none';
}

const roundedClasses: Record<'control' | 'card' | 'modal' | 'full' | 'none', string> = {
  control: 'rounded-control',
  card: 'rounded-card',
  modal: 'rounded-modal',
  full: 'rounded-full',
  none: 'rounded-none',
};

export const SkeletonBlock: React.FC<SkeletonBlockProps> = ({
  width,
  height,
  rounded = 'control',
  className,
  style,
  ...props
}) => {
  const inlineStyles: React.CSSProperties = {
    ...style,
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      aria-hidden="true"
      style={inlineStyles}
      className={cn(
        'bg-neutral-border/40 animate-pulse',
        roundedClasses[rounded],
        className
      )}
      {...props}
    />
  );
};

export default SkeletonBlock;
