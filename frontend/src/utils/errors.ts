/**
 * ClarifAI API & Mock Error Primitives (PRD Ch. 30.8 & Section 8)
 *
 * Enforces the standardized error shape:
 * { error: { code, message } } (code, not field)
 */

export interface ApiErrorDetail {
  code: string;
  message: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export class MockApiError extends Error {
  status: number;
  error: ApiErrorDetail;

  constructor(message: string, code: string = 'ERROR', status: number = 400) {
    super(message);
    this.name = 'MockApiError';
    this.status = status;
    this.error = {
      code,
      message,
    };
  }
}
