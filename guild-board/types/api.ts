/**
 * Request/response contracts for the Guild Board HTTP API.
 * Zod schemas live next to the route handlers; these are the wire types both
 * sides compile against.
 */

import type {
  BidWithMember,
  EscrowStatus,
  RiskTier,
  TaskWithDistance,
  TaskWithRelations,
} from './database';

export type ApiResponse<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

export interface ApiError {
  code: ApiErrorCode;
  message: string;
  /** Field-level detail for form rendering. */
  fields?: Record<string, string>;
  /** Populated when the safety filter is what rejected the request. */
  safety?: SafetyVerdict;
}

export type ApiErrorCode =
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'validation_failed'
  | 'prohibited_content'
  | 'verification_required'
  | 'payout_setup_required'
  | 'conflict'
  | 'payment_failed'
  | 'rate_limited'
  | 'internal_error';

/* -------------------------------------------------------------------------- */
/* Safety                                                                     */
/* -------------------------------------------------------------------------- */

export type SafetyAction = 'allow' | 'review' | 'block';

export interface SafetyMatch {
  /** The rule that fired, e.g. `weapons`, `licensed_trade.electrical`. */
  rule: string;
  /** The literal text in the submission that matched. */
  term: string;
  category: SafetyCategory;
}

export type SafetyCategory =
  | 'illegal'
  | 'weapons'
  | 'controlled_substances'
  | 'sexual_services'
  | 'hazardous'
  | 'licensed_trade'
  | 'financial_fraud'
  | 'privacy_violation'
  | 'platform_circumvention'
  | 'minors';

export interface SafetyVerdict {
  action: SafetyAction;
  riskTier: RiskTier;
  matches: SafetyMatch[];
  /** Human-readable explanation shown to the poster when action !== 'allow'. */
  reason: string | null;
  /** Licence slugs the assigned worker must hold, if any. */
  requiredLicences: string[];
}

/* -------------------------------------------------------------------------- */
/* Board discovery                                                            */
/* -------------------------------------------------------------------------- */

export interface BoardQuery {
  city: string;
  lat?: number;
  long?: number;
  radiusMiles?: number;
  categories?: string[];
  minReward?: number;
  maxReward?: number;
  sort?: BoardSort;
  page?: number;
}

export type BoardSort = 'nearest' | 'newest' | 'reward_desc' | 'reward_asc';

export interface BoardResponse {
  tasks: TaskWithDistance[];
  total: number;
  page: number;
  pageSize: number;
}

/* -------------------------------------------------------------------------- */
/* Tasks                                                                      */
/* -------------------------------------------------------------------------- */

export interface CreateTaskInput {
  title: string;
  description: string;
  citySlug: string;
  categoryId: string;
  rewardAmount: number;
  lat: number;
  long: number;
  addressLine?: string;
  deadlineAt?: string;
  imageUrls?: string[];
  /** Version string of the disclaimer the user actually saw. */
  safetyAckVersion: string;
}

export interface CreateTaskResponse {
  task: TaskWithRelations;
  safety: SafetyVerdict;
}

/* -------------------------------------------------------------------------- */
/* Bids                                                                       */
/* -------------------------------------------------------------------------- */

export interface CreateBidInput {
  taskId: string;
  amount: number;
  proposalText: string;
  estimatedHours?: number;
  canStartAt?: string;
}

export interface AcceptBidResponse {
  bid: BidWithMember;
  /** Client secret for the manual-capture PaymentIntent backing the escrow. */
  clientSecret: string;
  paymentIntentId: string;
  amount: number;
  platformFee: number;
  payoutAmount: number;
}

/* -------------------------------------------------------------------------- */
/* Stripe Connect                                                             */
/* -------------------------------------------------------------------------- */

export interface ConnectOnboardingResponse {
  accountId: string;
  onboardingUrl: string;
  payoutsEnabled: boolean;
  chargesEnabled: boolean;
  /** Requirements Stripe still needs before payouts unlock. */
  requirementsDue: string[];
}

export interface EscrowAuthorizeInput {
  taskId: string;
  bidId: string;
}

export interface EscrowReleaseInput {
  taskId: string;
  /** Why funds are moving. Audited on the transaction row. */
  reason: 'manual_signoff' | 'auto_release_72h' | 'dispute_resolution' | 'admin';
}

export interface EscrowStatusResponse {
  transactionId: string;
  escrowStatus: EscrowStatus;
  amount: number;
  platformFee: number;
  payoutAmount: number;
  currency: string;
  releasesAt: string | null;
  hoursRemaining: number | null;
}

/* -------------------------------------------------------------------------- */
/* Verification vendors                                                       */
/* -------------------------------------------------------------------------- */

export type VerificationStatus =
  | 'not_started'
  | 'pending'
  | 'approved'
  | 'declined'
  | 'needs_review';

export interface IdentityVerificationSession {
  provider: 'persona';
  inquiryId: string;
  status: VerificationStatus;
  /** Hosted flow the user is redirected into. */
  sessionUrl: string | null;
}

export interface BackgroundCheckReport {
  provider: 'checkr';
  candidateId: string;
  reportId: string;
  status: VerificationStatus;
  /** Trade licences the vendor confirmed, mapped to our category slugs. */
  verifiedLicences: string[];
  completedAt: string | null;
}
