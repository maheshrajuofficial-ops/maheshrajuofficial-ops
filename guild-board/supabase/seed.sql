-- ============================================================================
-- Guild Board — seed data (launch cities + category taxonomy)
-- Idempotent: safe to re-run against a local stack.
-- ============================================================================

insert into public.cities (name, slug, country, lat, long, radius_miles, timezone, currency, active_status) values
  ('New York',      'new-york',      'US', 40.712776,  -74.005974, 35, 'America/New_York',    'USD', true),
  ('Chicago',       'chicago',       'US', 41.878113,  -87.629799, 30, 'America/Chicago',     'USD', true),
  ('Los Angeles',   'los-angeles',   'US', 34.052235, -118.243683, 40, 'America/Los_Angeles', 'USD', true),
  ('Austin',        'austin',        'US', 30.267153,  -97.743057, 25, 'America/Chicago',     'USD', true),
  ('London',        'london',        'GB', 51.507351,   -0.127758, 25, 'Europe/London',       'GBP', true),
  ('Berlin',        'berlin',        'DE', 52.520008,   13.404954, 25, 'Europe/Berlin',       'EUR', true),
  ('Tokyo',         'tokyo',         'JP', 35.689487,  139.691711, 30, 'Asia/Tokyo',          'JPY', true),
  ('Singapore',     'singapore',     'SG',  1.352083,  103.819839, 20, 'Asia/Singapore',      'SGD', true),
  ('Toronto',       'toronto',       'CA', 43.653225,  -79.383186, 30, 'America/Toronto',     'CAD', true),
  ('Sydney',        'sydney',        'AU',-33.868820,  151.209290, 30, 'Australia/Sydney',    'AUD', false)
on conflict (slug) do nothing;

insert into public.categories (name, slug, description, icon, is_licensed_trade_required, default_risk_tier, sort_order) values
  ('Moving & Heavy Lifting', 'moving',        'Furniture, boxes, van loads and two-person carries.',            'Truck',       false, 'medium',        10),
  ('Assembly & Mounting',    'assembly',      'Flat-pack builds, TV mounts, shelving and brackets.',            'Wrench',      false, 'low',           20),
  ('Cleaning',               'cleaning',      'Deep cleans, end-of-tenancy, post-event and yard clear-outs.',   'Sparkles',    false, 'low',           30),
  ('Delivery & Courier',     'delivery',      'Same-day pickups, queue-standing and cross-town drop-offs.',     'Package',     false, 'low',           40),
  ('Yard & Garden',          'yard',          'Mowing, hedges, leaf clearing and seasonal tidy-ups.',           'Trees',       false, 'low',           50),
  ('Tech & Devices',         'tech',          'Setup, migration, home network and smart-device help.',          'Laptop',      false, 'low',           60),
  ('Creative & Media',       'creative',      'Photo, video, design, editing and one-off creative commissions.','Camera',      false, 'low',           70),
  ('Events & Staffing',      'events',        'Setup crews, extra hands, day-of coordination.',                 'PartyPopper', false, 'low',           80),
  ('Pet Care',               'pets',          'Walks, sitting, transport to the vet.',                          'PawPrint',    false, 'low',           90),
  ('Errands & Admin',        'errands',       'Queues, returns, paperwork runs and pickups.',                   'ClipboardList', false, 'low',        100),
  ('Hyper-Niche Requests',   'niche',         'The genuinely odd jobs that fit nowhere else.',                  'Sparkle',     false, 'medium',       110),
  ('Electrical',             'electrical',    'Licensed electrical work only. Verified trade licence required.','Zap',         true,  'high_licensed',120),
  ('Plumbing',               'plumbing',      'Licensed plumbing work only. Verified trade licence required.',  'Droplets',    true,  'high_licensed',130),
  ('HVAC',                   'hvac',          'Licensed heating, ventilation and cooling work.',                'Wind',        true,  'high_licensed',140),
  ('Roofing & Height Work',  'roofing',       'Licensed and insured work at height.',                           'Home',        true,  'high_licensed',150)
on conflict (slug) do nothing;
