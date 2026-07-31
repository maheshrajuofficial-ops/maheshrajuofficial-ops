/** Platform-wide constants. Anything tunable per-environment lives in env. */

/** Bumped whenever the safety disclaimer copy changes; stored per task. */
export const SAFETY_DISCLAIMER_VERSION = '2026-01-v1';

export const PLATFORM_FEE_BPS = Number(process.env.PLATFORM_FEE_BPS ?? 750);

export const ESCROW_AUTO_RELEASE_HOURS = Number(
  process.env.ESCROW_AUTO_RELEASE_HOURS ?? 72
);

export const RADIUS_MIN_MILES = 1;
export const RADIUS_MAX_MILES = 50;
export const RADIUS_DEFAULT_MILES = 15;

export const REWARD_MIN = 5;
export const REWARD_MAX = 25_000;

export const BOARD_PAGE_SIZE = 24;

export const TASK_STATUS_LABELS = {
  open: 'Open for bids',
  assigned: 'Assigned',
  in_escrow: 'Funds in escrow',
  completed: 'Completed',
  disputed: 'In dispute',
  cancelled: 'Cancelled',
} as const;

export const RISK_TIER_LABELS = {
  low: 'Standard',
  medium: 'Elevated care',
  high_licensed: 'Licensed trade',
} as const;

export const BOARD_SORTS = [
  { value: 'nearest', label: 'Nearest first' },
  { value: 'newest', label: 'Newest first' },
  { value: 'reward_desc', label: 'Highest reward' },
  { value: 'reward_asc', label: 'Lowest reward' },
] as const;

/**
 * Shown verbatim in the final step of the task wizard. Consent is recorded
 * with a timestamp and this version string — it is a compliance artefact, so
 * do not edit the text without bumping SAFETY_DISCLAIMER_VERSION.
 */
export const SAFETY_DISCLAIMER = [
  'Guild Board is a neutral venue. We introduce requesters to independent workers; we do not employ, supervise, direct or insure them.',
  'Licensed trades — electrical, plumbing, gas, HVAC, roofing, structural, medical, legal and financial advice — may only be performed by someone holding the licence your jurisdiction requires. Posting such a task means you accept that we will verify the licence before work begins, and that the task may be removed if we cannot.',
  'You will not post anything illegal, hazardous beyond ordinary care, sexual in nature, involving weapons or controlled substances, or requiring a minor.',
  'Payment is held in escrow and released on sign-off or automatically after the dispute window. Arranging payment off-platform voids escrow protection and is grounds for removal.',
  'You are responsible for your own insurance, and for the accuracy of the address and access details you provide.',
] as const;
