import world from '../data/worldmap.json';

// Robinson projection. The same constants and the same fit that
// scripts generated src/data/worldmap.json with, so a marker placed here lands
// on the coastline drawn there.
const AA = [
  0.8487, 0.84751182, 0.84479598, 0.840213, 0.83359314, 0.8257851, 0.814752,
  0.80006949, 0.78216192, 0.76060494, 0.73658673, 0.7086645, 0.67777182,
  0.64475739, 0.60987582, 0.57134484, 0.52729731, 0.48562614, 0.45167814,
];
const BB = [
  0, 0.0838426, 0.1676852, 0.2515278, 0.3353704, 0.419213, 0.5030556, 0.5868982,
  0.6707408, 0.7545834, 0.838426, 0.9222686, 1.0061112, 1.0899538, 1.1737964,
  1.257639, 1.3414816, 1.4253242, 1.5091668,
];

export interface Point {
  x: number;
  y: number;
}

export function project(lon: number, lat: number): Point {
  const k = Math.min(18, Math.abs(lat) / 5);
  const i = Math.min(Math.floor(k), 17);
  const t = k - i;
  const X = AA[i] + (AA[i + 1] - AA[i]) * t;
  const Y = BB[i] + (BB[i + 1] - BB[i]) * t;
  const rx = (lon * Math.PI) / 180 * X;
  const ry = (lat >= 0 ? 1 : -1) * Y;
  const { minx, maxy, scale } = world.proj;
  return { x: (rx - minx) * scale, y: (maxy - ry) * scale };
}

export const map = {
  path: world.path,
  width: world.width,
  height: world.height,
};
