import { track } from "./analytics";

export function markDelivered(orderId: string): void {
  // ... update order status to delivered ...
  track({ name: "order_delivered", props: { orderId } });
}

export function cancelOrder(orderId: string, reason: string): void {
  // ... cancel the order ...
  track({ name: "order_cancelled", props: { orderId, reason } });
}