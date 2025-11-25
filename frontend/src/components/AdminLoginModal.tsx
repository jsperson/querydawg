'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { adminAuth, checkAdminRequired, verifyAdminPassword } from '@/lib/admin';

interface AdminLoginModalProps {
  onSuccess: () => void;
  onCancel?: () => void;
  title?: string;
  description?: string;
}

export function AdminLoginModal({
  onSuccess,
  onCancel,
  title = 'Admin Authentication Required',
  description = 'This action requires admin privileges. Please enter the admin password.',
}: AdminLoginModalProps) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsVerifying(true);

    try {
      const isValid = await verifyAdminPassword(password);
      if (isValid) {
        adminAuth.setPassword(password);
        onSuccess();
      } else {
        setError('Invalid admin password');
      }
    } catch {
      setError('Failed to verify password');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onCancel?.()}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="admin-password">Admin Password</Label>
            <Input
              id="admin-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter admin password"
              autoFocus
              className="mt-2"
            />
            {error && (
              <p className="text-sm text-destructive mt-2">{error}</p>
            )}
          </div>
          <DialogFooter>
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={isVerifying || !password}>
              {isVerifying ? 'Verifying...' : 'Login'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface UseAdminAuthReturn {
  isAdmin: boolean;
  isLoading: boolean;
  adminRequired: boolean;
  showLoginModal: boolean;
  requestAdminAccess: () => void;
  AdminModal: React.ReactNode;
  logout: () => void;
}

export function useAdminAuth(): UseAdminAuthReturn {
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [adminRequired, setAdminRequired] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      // Check if admin is required
      const required = await checkAdminRequired();
      setAdminRequired(required);

      // If admin is required, check if we have a valid password stored
      if (required) {
        const storedPassword = adminAuth.getPassword();
        if (storedPassword) {
          // Verify the stored password is still valid
          const isValid = await verifyAdminPassword(storedPassword);
          setIsAdmin(isValid);
          if (!isValid) {
            adminAuth.clearPassword();
          }
        }
      } else {
        // No admin required, everyone is admin
        setIsAdmin(true);
      }

      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const requestAdminAccess = () => {
    setShowLoginModal(true);
  };

  const handleLoginSuccess = () => {
    setIsAdmin(true);
    setShowLoginModal(false);
  };

  const handleLoginCancel = () => {
    setShowLoginModal(false);
  };

  const logout = () => {
    adminAuth.clearPassword();
    setIsAdmin(false);
  };

  const AdminModal = showLoginModal ? (
    <AdminLoginModal
      onSuccess={handleLoginSuccess}
      onCancel={handleLoginCancel}
    />
  ) : null;

  return {
    isAdmin,
    isLoading,
    adminRequired,
    showLoginModal,
    requestAdminAccess,
    AdminModal,
    logout,
  };
}
