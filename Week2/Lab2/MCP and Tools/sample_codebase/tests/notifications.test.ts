import { sendOrderShipped } from "../src/notifications";

test("sendOrderShipped runs without throwing", () => {
  expect(() => sendOrderShipped("NP-100245", "alex@northpeak-demo.test")).not.toThrow();
});