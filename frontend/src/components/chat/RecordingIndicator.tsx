/**
 * Recording indicator component.
 * Animated pulsing mic icon displayed during voice recording.
 */

export function RecordingIndicator() {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-destructive/10 border border-destructive/30">
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-destructive" />
      </span>
      <span className="text-xs font-medium text-destructive">Recording...</span>
    </div>
  );
}
