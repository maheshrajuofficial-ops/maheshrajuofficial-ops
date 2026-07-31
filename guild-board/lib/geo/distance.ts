/** Geodesic helpers shared by the map, the radius slider and the board query. */

const EARTH_RADIUS_MILES = 3958.7613;

export interface LatLng {
  lat: number;
  long: number;
}

/** Great-circle distance in miles. */
export function haversineMiles(a: LatLng, b: LatLng): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.long - a.long);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);

  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.sin(dLng / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);

  return 2 * EARTH_RADIUS_MILES * Math.asin(Math.sqrt(h));
}

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

/**
 * Bounding box for a radius, used to set the initial map viewport before the
 * server has answered. Longitude degrees shrink with latitude, hence the
 * cos() term; clamped so a large radius near the poles can't blow up.
 */
export function radiusBounds(
  center: LatLng,
  radiusMiles: number
): { north: number; south: number; east: number; west: number } {
  const latDelta = radiusMiles / 69.0;
  const cosLat = Math.max(Math.cos(toRad(center.lat)), 0.01);
  const lngDelta = radiusMiles / (69.0 * cosLat);

  return {
    north: Math.min(90, center.lat + latDelta),
    south: Math.max(-90, center.lat - latDelta),
    east: center.long + lngDelta,
    west: center.long - lngDelta,
  };
}

/**
 * Blur a precise address into a pin that's safe to show on a public board.
 *
 * Open tasks expose a location to strangers, so the board never plots the
 * doorstep. We offset by a random bearing at a fixed radius, seeded off the
 * task id so the pin doesn't jitter between renders — a jittering pin can be
 * averaged back to the true point across reloads.
 */
export function coarsenLocation(point: LatLng, taskId: string, jitterMiles = 0.25): LatLng {
  const seed = hashString(taskId);
  const bearing = (seed % 360) * (Math.PI / 180);
  const distance = jitterMiles * (0.4 + ((seed >>> 9) % 60) / 100);

  const latDelta = (distance / 69.0) * Math.cos(bearing);
  const cosLat = Math.max(Math.cos(toRad(point.lat)), 0.01);
  const lngDelta = (distance / (69.0 * cosLat)) * Math.sin(bearing);

  return {
    lat: Number((point.lat + latDelta).toFixed(5)),
    long: Number((point.long + lngDelta).toFixed(5)),
  };
}

function hashString(value: string): number {
  let hash = 2166136261;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

/** Zoom level that roughly frames a given radius in a standard viewport. */
export function zoomForRadius(radiusMiles: number): number {
  if (radiusMiles <= 2) return 13.5;
  if (radiusMiles <= 5) return 12.5;
  if (radiusMiles <= 10) return 11.5;
  if (radiusMiles <= 20) return 10.5;
  if (radiusMiles <= 35) return 9.8;
  return 9;
}
