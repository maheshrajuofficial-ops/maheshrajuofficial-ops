'use client';

import * as React from 'react';
import mapboxgl from 'mapbox-gl';
import { Crosshair, MapPin } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import 'mapbox-gl/dist/mapbox-gl.css';

export interface LatLng {
  lat: number;
  long: number;
}

/**
 * Drop-a-pin location input for the task wizard.
 *
 * Falls back to two number fields when no Mapbox token is configured, so the
 * wizard is completable in a bare dev environment.
 */
export function LocationPicker({
  center,
  value,
  onChange,
}: {
  center: LatLng;
  value: LatLng | null;
  onChange: (point: LatLng) => void;
}) {
  const container = React.useRef<HTMLDivElement>(null);
  const map = React.useRef<mapboxgl.Map | null>(null);
  const marker = React.useRef<mapboxgl.Marker | null>(null);
  const onChangeRef = React.useRef(onChange);

  React.useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

  React.useEffect(() => {
    if (!token || !container.current || map.current) return;

    mapboxgl.accessToken = token;

    const instance = new mapboxgl.Map({
      container: container.current,
      style: process.env.NEXT_PUBLIC_MAPBOX_STYLE ?? 'mapbox://styles/mapbox/streets-v12',
      center: [value?.long ?? center.long, value?.lat ?? center.lat],
      zoom: value ? 14 : 11,
    });

    instance.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');

    const pin = new mapboxgl.Marker({ color: '#b45309', draggable: true }).setLngLat([
      value?.long ?? center.long,
      value?.lat ?? center.lat,
    ]);

    pin.on('dragend', () => {
      const { lat, lng } = pin.getLngLat();
      onChangeRef.current({ lat: round(lat), long: round(lng) });
    });

    instance.on('click', (event) => {
      pin.setLngLat(event.lngLat).addTo(instance);
      onChangeRef.current({
        lat: round(event.lngLat.lat),
        long: round(event.lngLat.lng),
      });
    });

    if (value) pin.addTo(instance);

    map.current = instance;
    marker.current = pin;

    return () => {
      instance.remove();
      map.current = null;
      marker.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      const point = {
        lat: round(position.coords.latitude),
        long: round(position.coords.longitude),
      };
      onChange(point);
      marker.current?.setLngLat([point.long, point.lat]);
      if (map.current) {
        marker.current?.addTo(map.current);
        map.current.flyTo({ center: [point.long, point.lat], zoom: 14 });
      }
    });
  }

  if (!token) {
    return (
      <div className="space-y-2">
        <Label>Location</Label>
        <div className="flex gap-2">
          <Input
            type="number"
            step="0.00001"
            placeholder="Latitude"
            value={value?.lat ?? ''}
            onChange={(e) =>
              onChange({ lat: Number(e.target.value), long: value?.long ?? center.long })
            }
          />
          <Input
            type="number"
            step="0.00001"
            placeholder="Longitude"
            value={value?.long ?? ''}
            onChange={(e) =>
              onChange({ lat: value?.lat ?? center.lat, long: Number(e.target.value) })
            }
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Add NEXT_PUBLIC_MAPBOX_TOKEN for the pin-drop map.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Drop a pin</Label>
        <Button type="button" variant="ghost" size="sm" onClick={useMyLocation}>
          <Crosshair className="h-3.5 w-3.5" />
          Use my location
        </Button>
      </div>
      <div
        ref={container}
        className="h-64 w-full overflow-hidden rounded-lg border"
        role="application"
        aria-label="Click the map to place your task pin"
      />
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <MapPin className="h-3 w-3" />
        {value
          ? `Pinned at ${value.lat.toFixed(4)}, ${value.long.toFixed(4)}`
          : 'Click the map to place your pin.'}
      </p>
    </div>
  );
}

function round(value: number): number {
  return Number(value.toFixed(5));
}
