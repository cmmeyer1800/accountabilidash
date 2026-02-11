/** Credentials sent to POST /auth/login */
export interface LoginRequest {
  email: string;
  password: string;
}

/** Body sent to POST /auth/register */
export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

/** Response from POST /auth/login */
export interface TokenResponse {
  access_token: string;
  token_type: string;
}
