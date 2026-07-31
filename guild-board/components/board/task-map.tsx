'use client';

import * as React from 'react';
import mapboxgl from 'mapbox-gl';

import { coarsenLocation, zoomForRadius } from '@/lib/geo/distance';
import { formatCurrency } from '@/lib/utils';
import type { TaskWithDistance } from '@/types/database';

import 'mapbox-gl/dist/mapbox-gl.css';

export interface TaskMapProps {
  tasks: TaskWithDistance[];
  center: { lat: number; long: number };
  radiusMiles: number;
  currency?: string;
  activeTaskId?: string | null;
  onSelect?: (taskId: string | null) => void;
}

/**
 * Interactive pin view of the board.
 *
 * Pins are drawn from `coarsenLocation`, not the raw coordinates — an open
 * task is public, and its exact address is not. The precise point is only
 * revealed to the assigned member, after the bid is accepted.
 */
export function TaskMap({
  tasks,
  center,
  radiusMiles,
  currency = 'USD',
  activeTaskId,
  onSelect,
}: TaskMapProps) {
  const container = React.useRef<HTMLDivElement>(null);
  const map = React.useRef<mapboxgl.Map | null>(null);
  const markers = React.useRef<Map<string, mapboxgl.Marker>>(new Map());
  const [ready, setReady] = React.useState(false);

  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  /* --- init ------------------------------------------------------------- */
  React.useEffect(() => {
    if (!container.current || map.current || !token) return;

    mapboxgl.accessToken = token;

    const instance = new mapboxgl.Map({
      container: container.current,
      style: process.env.NEXT_PUBLIC_MAPBOX_STYLE ?? 'mapbox://styles/mapbox/streets-v12',
      center: [center.long, center.lat],
      zoom: zoomForRadius(radiusMiles),
      attributionControl: true,
    });

    instance.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');
    instance.on('load', () => setReady(true));

    map.current = instance;

    return () => {
      instance.remove();
      map.current = null;
      setReady(false);
    };
    // Re-creating the map on every prop change would fight the user's panning;
    // subsequent updates are handled by the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  /* --- recentre when the city or radius changes ------------------------- */
  React.useEffect(() => {
    if (!map.current || !ready) return;
    map.current.easeTo({
      center: [center.long, center.lat],
      zoom: zoomForRadius(radiusMiles),
      duration: 600,
    });
  }, [center.lat, center.long, radiusMiles, ready]);

  /* --- radius ring ------------------------------------------------------ */
  React.useEffect(() => {
    const instance = map.current;
    if (!instance || !ready) return;

    const source = instance.getSource('radius') as mapboxgl.GeoJSONSource | undefined;
    const circle = radiusPolygon(center, radiusMiles);

    if (source) {
      source.setData(circle);
      return;
    }

    instance.addSource('radius', { type: 'geojson', data: circle });
    instance.addLayer({
      id: 'radius-fill',
      type: 'fill',
      source: 'radius',
      paint: { 'fill-color': '#b45309', 'fill-opacity': 0.06 },
    });
    instance.addLayer({
      id: 'radius-line',
      type: 'line',
      source: 'radius',
      paint: { 'line-color': '#b45309', 'line-width': 1.5, 'line-dasharray': [2, 2] },
    });
  }, [center, radiusMiles, ready]);

  /* --- pins ------------------------------------------------------------- */
  React.useEffect(() => {
    const instance = map.current;
    if (!instance || !ready) return;

    const seen = new Set<string>();

    for (const task of tasks) {
      seen.add(task.id);
      if (markers.current.has(task.id)) continue;

      const point = coarsenLocation({ lat: task.lat, long: task.long }, task.id);

      const el = document.createElement('button');
      el.type = 'button';
      el.className =
        'rounded-full border border-white/80 bg-primary px-2 py-1 text-xs font-semibold text-primary-foreground shadow-md transition-transform hover:scale-110';
      el.textContent = formatCurrency(task.reward_amount, currency);
      el.setAttribute('aria-label', `${task.title}, ${formatCurrency(task.reward_amount, currency)}`);
      el.addEventListener('click', () => onSelect?.(task.id));

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([point.long, point.lat])
        .setPopup(
          new mapboxgl.Popup({ offset: 16, closeButton: false }).setText(task.title)
        )
        .addTo(instance);

      markers.current.set(task.id, marker);
    }

    for (const [id, marker] of markers.current) {
      if (!seen.has(id)) {
        marker.remove();
        markers.current.delete(id);
      }
    }
  }, [tasks, currency, onSelect, ready]);

  /* --- highlight the hovered card's pin --------------------------------- */
  React.useEffect(() => {
    for (const [id, marker] of markers.current) {
      marker.getElement().classList.toggle('scale-125', id === activeTaskId);
      marker.getElement().classList.toggle('ring-2', id === activeTaskId);
      marker.getElement().classList.toggle('ring-foreground', id === activeTaskId);
    }
  }, [activeTaskId, tasks]);

  if (!token) {
    return (
      <div className="grid h-[28rem] place-items-center rounded-lg border border-dashed text-center text-sm text-muted-foreground">
        <p className="max-w-xs px-6">
          Set <code className="rounded bg-muted px-1">NEXT_PUBLIC_MAPBOX_TOKEN</code> to
          enable the map view. The grid view works without it.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={container}
      className="h-[28rem] w-full overflow-hidden rounded-lg border lg:h-[calc(100vh-12rem)]"
      role="application"
      aria-label="Map of nearby tasks"
    />
  );
}

/** Approximate a circle as a 64-sided polygon in GeoJSON. */
function radiusPolygon(
  center: { lat: number; long: number },
  radiusMiles: number
): GeoJSON.Feature<GeoJSON.Polygon> {
  const points: [number, number][] = [];
  const latDelta = radiusMiles / 69;
  const lngDelta = radiusMiles / (69 * Math.max(Math.cos((center.lat * Math.PI) / 180), 0.01));

  for (let i = 0; i <= 64; i += 1) {
    const theta = (i / 64) * 2 * Math.PI;
    points.push([
      center.long + lngDelta * Math.cos(theta),
      center.lat + latDelta * Math.sin(theta),
    ]);
  }

  return {
    type: 'Feature',
    properties: {},
    geometry: { type: 'Polygon', coordinates: [points] },
  };
}
