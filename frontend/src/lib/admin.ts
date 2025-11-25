/**
 * Admin authentication utilities
 */

const ADMIN_PASSWORD_KEY = 'querydawg_admin_password';

export const adminAuth = {
  /**
   * Get stored admin password from sessionStorage
   */
  getPassword: (): string | null => {
    if (typeof window === 'undefined') return null;
    return sessionStorage.getItem(ADMIN_PASSWORD_KEY);
  },

  /**
   * Store admin password in sessionStorage
   */
  setPassword: (password: string): void => {
    if (typeof window === 'undefined') return;
    sessionStorage.setItem(ADMIN_PASSWORD_KEY, password);
  },

  /**
   * Clear admin password from sessionStorage
   */
  clearPassword: (): void => {
    if (typeof window === 'undefined') return;
    sessionStorage.removeItem(ADMIN_PASSWORD_KEY);
  },

  /**
   * Check if admin password is stored
   */
  isAuthenticated: (): boolean => {
    return !!adminAuth.getPassword();
  },
};

/**
 * Check if admin authentication is required (ADMIN_PASSWORD is set on server)
 */
export async function checkAdminRequired(): Promise<boolean> {
  try {
    const response = await fetch('/api/admin/status');
    if (!response.ok) return false;
    const data = await response.json();
    return data.admin_required === true;
  } catch {
    return false;
  }
}

/**
 * Verify admin password with the server
 */
export async function verifyAdminPassword(password: string): Promise<boolean> {
  try {
    const response = await fetch('/api/admin/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Password': password,
      },
    });
    return response.ok;
  } catch {
    return false;
  }
}
