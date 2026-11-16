interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

const sizes = { sm: 'w-4 h-4', md: 'w-7 h-7', lg: 'w-10 h-10' };

export default function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8">
      <div className={`${sizes[size]} border-2 border-sk-secondary border-t-sk-primary rounded-full animate-spin`} />
      {text && <p className="text-sm text-sk-text-secondary">{text}</p>}
    </div>
  );
}
