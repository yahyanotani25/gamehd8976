// The shared chart for s2 (order block) and s3 (breaker block). Plain data,
// no imports. Candle i sits at x = i + 0.5. See docs/STORYBOARD.md.
export const CANDLES = [
  { o: 8.6, h: 9.0, l: 7.4, c: 7.6 },   // 0 downtrend
  { o: 7.6, h: 7.9, l: 6.2, c: 6.4 },   // 1
  { o: 6.4, h: 6.8, l: 5.0, c: 5.3 },   // 2
  { o: 5.3, h: 5.6, l: 3.9, c: 4.1 },   // 3
  { o: 4.1, h: 4.4, l: 2.9, c: 3.2 },   // 4 ORDER BLOCK: last down candle before the impulse
  { o: 3.2, h: 5.9, l: 3.0, c: 5.7 },   // 5 impulse
  { o: 5.7, h: 8.3, l: 5.5, c: 8.1 },   // 6 impulse
  { o: 8.1, h: 10.6, l: 7.9, c: 10.3 }, // 7 impulse, breaks above candle 0's high
  { o: 10.3, h: 10.6, l: 8.9, c: 9.1 }, // 8 pullback
  { o: 9.1, h: 9.3, l: 7.0, c: 7.2 },   // 9
  { o: 7.2, h: 7.4, l: 5.2, c: 5.4 },   // 10
  { o: 5.4, h: 5.6, l: 3.7, c: 4.2 },   // 11 taps the zone
  { o: 4.2, h: 6.6, l: 4.0, c: 6.4 },   // 12 reaction
  { o: 6.4, h: 8.9, l: 6.2, c: 8.7 },   // 13
  { o: 8.7, h: 11.6, l: 8.5, c: 11.3 }, // 14 new high
  { o: 11.3, h: 11.5, l: 9.6, c: 9.8 }, // 15 (s3) return down
  { o: 9.8, h: 10.0, l: 7.6, c: 7.8 },  // 16
  { o: 7.8, h: 8.0, l: 5.0, c: 5.2 },   // 17 reaches the zone
  { o: 5.2, h: 5.4, l: 1.2, c: 1.5 },   // 18 FAIL: smashes through the zone
  { o: 1.5, h: 1.7, l: 0.2, c: 0.4 },   // 19 continuation
  { o: 0.4, h: 1.8, l: 0.2, c: 1.6 },   // 20 retrace up
  { o: 1.6, h: 2.7, l: 1.5, c: 2.4 },   // 21
  { o: 2.4, h: 3.8, l: 2.0, c: 2.1 },   // 22 REJECTION: wick into the zone from below
  { o: 2.1, h: 2.3, l: 0.4, c: 0.6 },   // 23 drop
  { o: 0.6, h: 0.8, l: -1.1, c: -0.9 }, // 24
  { o: -0.9, h: -0.7, l: -2.4, c: -2.2 }, // 25
];
export const OB_INDEX = 4;
export const FAIL_INDEX = 18;
export const REJECT_INDEX = 22;
export const ZONE = { x0: 4.05, y0: 2.9, y1: 4.4 };
// Zone right edge: in s2 it grows to x 15.4; in s3 it is already extended to 27.
export const ZONE_X1_S2 = 15.4;
export const ZONE_X1_S3 = 27.0;
export const X = (i) => i + 0.5;
