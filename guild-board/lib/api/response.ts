import { NextResponse } from 'next/server';

import type { ApiError, ApiErrorCode, ApiResponse } from '@/types/api';

const STATUS: Record<ApiErrorCode, number> = {
  unauthorized: 401,
  forbidden: 403,
  not_found: 404,
  validation_failed: 422,
  prohibited_content: 422,
  verification_required: 403,
  payout_setup_required: 409,
  conflict: 409,
  payment_failed: 402,
  rate_limited: 429,
  internal_error: 500,
};

export function ok<T>(data: T, status = 200) {
  return NextResponse.json<ApiResponse<T>>({ ok: true, data }, { status });
}

export function fail(
  code: ApiErrorCode,
  message: string,
  extra?: Omit<ApiError, 'code' | 'message'>
) {
  return NextResponse.json<ApiResponse<never>>(
    { ok: false, error: { code, message, ...extra } },
    { status: STATUS[code] }
  );
}

/**
 * Wraps a handler so an unexpected throw becomes a 500 with a stable shape
 * instead of Next's HTML error page — and so the stack lands in the server log
 * rather than in the client's response body.
 */
export function withErrorHandling<Args extends unknown[]>(
  handler: (...args: Args) => Promise<Response>
) {
  return async (...args: Args): Promise<Response> => {
    try {
      return await handler(...args);
    } catch (error) {
      console.error('[api] unhandled error', error);
      return fail('internal_error', 'Something went wrong. Please try again.');
    }
  };
}
