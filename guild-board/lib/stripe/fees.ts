import { PLATFORM_FEE_BPS } from '@/lib/constants';

/** Currencies with no minor unit — amounts are already in the smallest unit. */
const ZERO_DECIMAL = new Set([
  'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA',
  'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF',
]);

export function toMinorUnits(amount: number, currency: string): number {
  return ZERO_DECIMAL.has(currency.toUpperCase())
    ? Math.round(amount)
    : Math.round(amount * 100);
}

export function fromMinorUnits(minor: number, currency: string): number {
  return ZERO_DECIMAL.has(currency.toUpperCase()) ? minor : minor / 100;
}

export interface FeeBreakdown {
  /** What the requester is charged, in major units. */
  amount: number;
  /** Guild Board's cut, in major units. */
  platformFee: number;
  /** What lands in the member's Connect account, in major units. */
  payoutAmount: number;
  /** Same three figures in Stripe's smallest currency unit. */
  amountMinor: number;
  platformFeeMinor: number;
  payoutAmountMinor: number;
  currency: string;
  feeBps: number;
}

/**
 * Split a bid amount into charge / platform fee / member payout.
 *
 * The fee is computed on the minor-unit integer and the payout is the
 * remainder, so the two always sum back to the charge exactly — no rounding
 * dust that would make a transfer fail for being a cent over the balance.
 */
export function calculateFees(
  bidAmount: number,
  currency = 'USD',
  feeBps: number = PLATFORM_FEE_BPS
): FeeBreakdown {
  const amountMinor = toMinorUnits(bidAmount, currency);
  const platformFeeMinor = Math.round((amountMinor * feeBps) / 10_000);
  const payoutAmountMinor = amountMinor - platformFeeMinor;

  return {
    amount: fromMinorUnits(amountMinor, currency),
    platformFee: fromMinorUnits(platformFeeMinor, currency),
    payoutAmount: fromMinorUnits(payoutAmountMinor, currency),
    amountMinor,
    platformFeeMinor,
    payoutAmountMinor,
    currency: currency.toUpperCase(),
    feeBps,
  };
}
