import 'server-only';

import type { IdentityVerificationSession, VerificationStatus } from '@/types/api';

/**
 * Persona — government-ID + selfie identity verification.
 *
 * Integration stub. The shapes and the status mapping are real; the network
 * calls are guarded so the app runs end-to-end without a Persona account.
 * Set PERSONA_API_KEY to switch from simulated inquiries to live ones.
 *
 * Compliance note: identity documents never touch our database. Persona holds
 * the PII; we store the inquiry id and the boolean outcome. `identity-docs` in
 * Supabase Storage exists only for the manual-review fallback and is
 * admin-read-only.
 */

const PERSONA_API = 'https://api.withpersona.com/api/v1';

function isConfigured(): boolean {
  return Boolean(process.env.PERSONA_API_KEY && process.env.PERSONA_TEMPLATE_ID);
}

export async function createIdentityInquiry(params: {
  userId: string;
  email?: string;
  fullName?: string;
}): Promise<IdentityVerificationSession> {
  if (!isConfigured()) {
    return {
      provider: 'persona',
      inquiryId: `inq_sim_${params.userId.slice(0, 8)}`,
      status: 'pending',
      sessionUrl: null,
    };
  }

  const response = await fetch(`${PERSONA_API}/inquiries`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.PERSONA_API_KEY}`,
      'Content-Type': 'application/json',
      'Persona-Version': '2023-01-05',
    },
    body: JSON.stringify({
      data: {
        attributes: {
          'inquiry-template-id': process.env.PERSONA_TEMPLATE_ID,
          'reference-id': params.userId,
          fields: {
            'email-address': params.email,
            'name-first': params.fullName?.split(' ')[0],
            'name-last': params.fullName?.split(' ').slice(1).join(' '),
          },
        },
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Persona inquiry failed: ${response.status} ${await response.text()}`);
  }

  const payload = (await response.json()) as {
    data: { id: string; attributes: { status: string } };
  };

  return {
    provider: 'persona',
    inquiryId: payload.data.id,
    status: mapPersonaStatus(payload.data.attributes.status),
    sessionUrl: `https://withpersona.com/verify?inquiry-id=${payload.data.id}`,
  };
}

export async function getInquiryStatus(inquiryId: string): Promise<VerificationStatus> {
  if (!isConfigured()) return 'pending';

  const response = await fetch(`${PERSONA_API}/inquiries/${inquiryId}`, {
    headers: {
      Authorization: `Bearer ${process.env.PERSONA_API_KEY}`,
      'Persona-Version': '2023-01-05',
    },
  });

  if (!response.ok) return 'pending';

  const payload = (await response.json()) as {
    data: { attributes: { status: string } };
  };
  return mapPersonaStatus(payload.data.attributes.status);
}

export function mapPersonaStatus(status: string): VerificationStatus {
  switch (status) {
    case 'completed':
    case 'approved':
      return 'approved';
    case 'failed':
    case 'declined':
      return 'declined';
    case 'needs_review':
    case 'pending':
      return 'needs_review';
    case 'created':
    case 'started':
      return 'pending';
    default:
      return 'not_started';
  }
}
