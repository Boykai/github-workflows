/**
 * BoardSkeleton — skeleton grid matching the ProjectBoard layout.
 *
 * Renders 5 BoardColumnSkeleton columns in the same CSS grid used by
 * ProjectBoard, providing spatial continuity during first-time board loads.
 */

import { BoardColumnSkeleton } from './BoardColumnSkeleton';

const SKELETON_COLUMN_COUNT = 5;

export function BoardSkeleton() {
  return (
    <div
      className="celestial-fade-in flex h-full w-full flex-1 overflow-x-auto overflow-y-visible pb-6"
      role="region"
      aria-busy="true"
      aria-label="Loading board"
    >
      <div
        className="grid min-h-full min-w-full items-stretch gap-5 pb-2"
        style={{
          gridTemplateColumns: `repeat(${SKELETON_COLUMN_COUNT}, minmax(min(16rem, 85vw), 1fr))`,
        }}
      >
        {Array.from({ length: SKELETON_COLUMN_COUNT }).map((_, i) => (
          <BoardColumnSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
