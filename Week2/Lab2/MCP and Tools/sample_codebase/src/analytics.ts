// analytics.ts - NorthPeak event tracking.
//
// NOTE: logEvent() is DEPRECATED. New code should call track() instead.
// This lab's refactor task is to migrate every logEvent(...) call to track(...).

export type AnalyticsEvent = { name: string; props?: Record<string, unknown> };

/** @deprecated Use track() instead. */
export function logEvent(name: string, payload?: Record<string, unknown>): void {
  console.log("[analytics:legacy]", name, payload ?? {});
}

export function track(event: AnalyticsEvent): void {
  console.log("[analytics]", event.name, event.props ?? {});
}