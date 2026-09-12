import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { UILanguageSwitch } from '../../components/ui/UILanguageSwitch';

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="space-y-1 pb-4 border-b border-secondary-200">
        <h1 className="text-3xl font-serif font-bold text-primary-950">User Settings</h1>
        <p className="text-secondary-600 text-sm">
          Manage your account profile, preferences, and session security.
        </p>
      </div>

      {/* Profile Card */}
      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-base">Profile Information</CardTitle>
          <CardDescription>
            Your account identity and contact information.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            id="settings-name"
            label="Full Name"
            value={user?.fullName || 'ClarifAI User'}
            readOnly
          />
          <Input
            id="settings-email"
            label="Email Address"
            value={user?.email || 'user@clarifai.internal'}
            readOnly
          />
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-secondary-700">Account Status</label>
            <div>
              <Badge variant="success" size="sm">
                Active Tenant
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Preferences Card */}
      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-base">Interface Preferences</CardTitle>
          <CardDescription>
            Language and display options for ClarifAI.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary-900">{t('common.language', 'Language')}</p>
              <p className="text-xs text-secondary-500">Select interface and summary generation language.</p>
            </div>
            <UILanguageSwitch />
          </div>
        </CardContent>
      </Card>

      {/* Security & Token Architecture Card */}
      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-base">Security &amp; Token Architecture</CardTitle>
          <CardDescription>
            PRD Section 9.6 compliant token isolation.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-secondary-600 leading-relaxed">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="font-semibold text-secondary-800">Access Token:</span>
            <span>Stored in volatile memory (never written to localStorage or sessionStorage)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="font-semibold text-secondary-800">Refresh Token:</span>
            <span>Isolated in browser httpOnly Secure Cookie with automatic rotation</span>
          </div>
        </CardContent>
        <CardFooter className="pt-2 border-t border-secondary-100">
          <Button
            variant="outline"
            size="sm"
            onClick={() => alert('Full profile management will be available in Phase 03.')}
          >
            Edit Profile
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
