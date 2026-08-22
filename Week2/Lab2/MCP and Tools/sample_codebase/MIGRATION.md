# Migration Notes

- Replaced deprecated logEvent(name, payload) with track({ name, props })
  across src/notifications.ts and src/orders.ts; imports updated.
- Renamed analytics event order_cancelled -> order_canceled (one L).