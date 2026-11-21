'use client';

import { useMemo } from 'react';

const NO_HIGHLIGHT: readonly string[] = [];

interface Segment {
  readonly value: string;
  readonly marked: boolean;
}

function segments(text: string, highlight: readonly string[]): Segment[] {
  if (highlight.length === 0) {
    return [{ value: text, marked: false }];
  }
  const haystack = text.toLowerCase();
  const ranges: Array<[number, number]> = [];
  for (const term of highlight) {
    const needle = term.toLowerCase();
    if (!needle) {
      continue;
    }
    let from = 0;
    for (;;) {
      const at = haystack.indexOf(needle, from);
      if (at < 0) {
        break;
      }
      ranges.push([at, at + needle.length]);
      from = at + needle.length;
    }
  }
  ranges.sort((left, right) => left[0] - right[0]);
  const merged: Array<[number, number]> = [];
  for (const range of ranges) {
    const last = merged[merged.length - 1];
    if (last && range[0] <= last[1]) {
      last[1] = Math.max(last[1], range[1]);
    } else {
      merged.push([range[0], range[1]]);
    }
  }
  const parts: Segment[] = [];
  let cursor = 0;
  for (const [start, end] of merged) {
    if (start > cursor) {
      parts.push({ value: text.slice(cursor, start), marked: false });
    }
    parts.push({ value: text.slice(start, end), marked: true });
    cursor = end;
  }
  if (cursor < text.length) {
    parts.push({ value: text.slice(cursor), marked: false });
  }
  return parts.length > 0 ? parts : [{ value: text, marked: false }];
}

export default function SafeText({
  text,
  highlight = NO_HIGHLIGHT,
  className,
}: {
  text: string;
  highlight?: readonly string[];
  className?: string;
}) {
  const parts = useMemo(() => segments(text, highlight), [text, highlight]);
  return (
    <span className={className}>
      {parts.map((part, index) =>
        part.marked ? (
          <mark key={index}>{part.value}</mark>
        ) : (
          <span key={index}>{part.value}</span>
        ),
      )}
    </span>
  );
}
