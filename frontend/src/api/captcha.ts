/** CAPTCHA helper — fetch SVG challenge from backend. */

import api from "./client";

interface CaptchaResponse {
  captcha_token: string;
  svg: string;
}

export async function fetchCaptcha(): Promise<CaptchaResponse> {
  const resp = await api.get<CaptchaResponse>("/auth/captcha");
  return resp.data;
}
