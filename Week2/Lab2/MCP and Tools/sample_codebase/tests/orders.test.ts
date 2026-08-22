import { markDelivered } from "../src/orders";

test("markDelivered runs without throwing", () => {
  expect(() => markDelivered("NP-100190")).not.toThrow();
});