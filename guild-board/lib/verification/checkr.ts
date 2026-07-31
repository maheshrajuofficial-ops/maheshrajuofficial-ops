import 'server-only';

import type { BackgroundCheckReport, VerificationStatus } from '@/types/api';

/**
 * Checkr — criminal background checks and trade-licence verification.
 *
 * Integration stub, same shape as `persona.ts`: real request/response
 * contracts, simulated when CHECKR_API_KEY is absent.
 *
 * Legal note worth keeping in front of whoever wires this up for real. In the
 * US a background check on a worker is an FCRA "consumer report", which means:
 * written consent before ordering, adverse-action notice with a copy of the
 * report and a dispute window before acting on it, and state-level rules
 * (California, New York City, Illinois) that limit what may be considered and
 * when it may be asked. `orderBackgroundCheck` therefore refuses to run
 * without a recorded consent timestamp — do not remove that guard.
 */

const CHECKR_API = 'https://api.checkr.com/v1';

function isConfigured(): boolean {
  return Boolean(process.env.CHECKR_API_KEY);
}

function authHeader(): string {
  // Checkr uses HTTP Basic with the API key as the username, empty password.
  return `Basic ${Buffer.from(`${process.env.CHECKR_API_KEY}:`).toString('base64')}`;
}

export async function createCandidate(params: {
  userId: string;
  email: string;
  fullName: string;
  country?: string;
}): Promise<string> {
  if (!isConfigured()) return `cand_sim_${params.userId.slice(0, 8)}`;

  const [firstName, ...rest] = params.fullName.trim().split(/\s+/);

  const response = await fetch(`${CHECKR_API}/candidates`, {
    method: 'POST',
    headers: { Authorization: authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: params.email,
      first_name: firstName,
      last_name: rest.join(' ') || firstName,
      work_locations: [{ country: params.country ?? 'US' }],
      custom_id: params.userId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Checkr candidate failed: ${response.status} ${await response.text()}`);
  }

  const payload = (await response.json()) as { id: string };
  return payload.id;
}

export async function orderBackgroundCheck(params: {
  candidateId: string;
  /** ISO timestamp of the worker's FCRA disclosure consent. Required. */
  consentAt: string | null;
  packageSlug?: string;
}): Promise<BackgroundCheckReport> {
  if (!params.consentAt) {
    throw new Error(
      'A background check cannot be ordered without recorded FCRA consent from the worker'
    );
  }

  if (!isConfigured()) {
    return {
      provider: 'checkr',
      candidateId: params.candidateId,
      reportId: `rep_sim_${params.candidateId.slice(-8)}`,
      status: 'pending',
      verifiedLicences: [],
      completedAt: null,
    };
  }

  const response = await fetch(`${CHECKR_API}/reports`, {
    method: 'POST',
    headers: { Authorization: authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      candidate_id: params.candidateId,
      package: params.packageSlug ?? process.env.CHECKR_PACKAGE_SLUG ?? 'tasker_pro',
    }),
  });

  if (!response.ok) {
    throw new Error(`Checkr report failed: ${response.status} ${await response.text()}`);
  }

  const payload = (await response.json()) as {
    id: string;
    status: string;
    completed_at: string | null;
  };

  return {
    provider: 'checkr',
    candidateId: params.candidateId,
    reportId: payload.id,
    status: mapCheckrStatus(payload.status),
    verifiedLicences: [],
    completedAt: payload.completed_at,
  };
}

/**
 * Trade-licence verification.
 *
 * There is no single national registry: licences are issued per state, per
 * province, per council. Checkr covers some via its professional-licence
 * screening; the rest need a per-jurisdiction connector or manual admin
 * review against an uploaded certificate. This returns the slugs we could
 * confirm, which is what `users.licensed_trades` is populated from — and that
 * column is what the bid trigger in 001 actually enforces against.
 */
export async function verifyTradeLicence(params: {
  candidateId: string;
  trade: string;
  licenceNumber: string;
  jurisdiction: string;
}): Promise<{ verified: boolean; source: string; expiresAt: string | null }> {
  if (!isConfigured()) {
    return { verified: false, source: 'manual_review_required', expiresAt: null };
  }

  const response = await fetch(`${CHECKR_API}/screenings/professional_license_verifications`, {
    method: 'POST',
    headers: { Authorization: authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      candidate_id: params.candidateId,
      license_number: params.licenceNumber,
      license_type: params.trade,
      license_state: params.jurisdiction,
    }),
  });

  if (!response.ok) {
    return { verified: false, source: 'manual_review_required', expiresAt: null };
  }

  const payload = (await response.json()) as {
    status: string;
    expiration_date: string | null;
  };

  return {
    verified: payload.status === 'clear',
    source: 'checkr',
    expiresAt: payload.expiration_date,
  };
}

export function mapCheckrStatus(status: string): VerificationStatus {
  switch (status) {
    case 'clear':
      return 'approved';
    case 'consider':
    case 'dispute':
      return 'needs_review';
    case 'suspended':

      return 'declined';
    case 'pending':

      return 'pending';
    default:
      return 'not_started';
  }
}
