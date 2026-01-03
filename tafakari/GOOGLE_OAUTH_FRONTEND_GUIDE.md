# Google OAuth Integration Guide for Next.js Frontend

## Overview
This guide explains how to integrate Google OAuth login with the Kazi Buddy Django backend from your Next.js frontend application.

## ⚠️ IMPORTANT: Admin Approval Required
**All new Google OAuth users require admin approval before they can log in.**
- New users are created but cannot log in until approved by admin
- No user type selection needed - admin assigns roles during approval
- User type is extracted from JWT token after login

## Backend Endpoint
```
https://kazi-buddy.onrender.com/api/v1/auth/google/callback/
```

## Environment Variables Required

Add to your `.env.local`:
```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
```

## Implementation

### Simple Google Login Button

```tsx
// components/GoogleLoginButton.tsx
'use client'; // if using App Router

export function GoogleLoginButton({ className }: { className?: string }) {
  const handleGoogleLogin = () => {
    const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const callbackUri = 'https://kazi-buddy.onrender.com/api/v1/auth/google/callback/';
    
    // Build Google OAuth URL (no user_type needed!)
    const params = new URLSearchParams({
      client_id: googleClientId!,
      redirect_uri: callbackUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
      prompt: 'consent',
    });
    
    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  };
  
  return (
    <button onClick={handleGoogleLogin} className={className}>
      Sign in with Google
    </button>
  );
}
```

### Usage Example

```tsx
// app/login/page.tsx
import { GoogleLoginButton } from '@/components/GoogleLoginButton';

export default function LoginPage() {
  return (
    <div>
      <h1>Sign In</h1>
      <GoogleLoginButton className="btn-primary" />
      <p className="note">New accounts require admin approval</p>
    </div>
  );
}
```

### Callback Handler (Optional)

If you want to handle the callback on the frontend:

```tsx
// app/auth/google/callback/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function GoogleCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');
      
      if (errorParam) {
        setError(`Google OAuth error: ${errorParam}`);
        setTimeout(() => router.push('/login'), 3000);
        return;
      }
      
      if (!code) {
        setError('No authorization code received');
        setTimeout(() => router.push('/login'), 3000);
        return;
      }
      
      try {
        const response = await fetch(
          `https://kazi-buddy.onrender.com/api/v1/auth/google/callback/?code=${code}`
        );
        
        const data = await response.json();
        
        // Handle new user (pending approval)
        if (response.status === 201 && data.pending_approval) {
          router.push('/pending-approval');
          return;
        }
        
        // Handle existing user not approved
        if (response.status === 403) {
          setError(data.message);
          router.push('/pending-approval');
          return;
        }
        
        // Handle approved user
        if (response.ok && data.tokens) {
          localStorage.setItem('access_token', data.tokens.access);
          localStorage.setItem('refresh_token', data.tokens.refresh);
          localStorage.setItem('user_info', JSON.stringify(data.user_info));
          
          // Redirect based on user type from token
          const redirectPath = data.user_info.user_type === 'employer' 
            ? '/employer/dashboard' 
            : '/worker/dashboard';
          
          router.push(redirectPath);
        } else {
          setError(data.error || 'Authentication failed');
          setTimeout(() => router.push('/login'), 3000);
        }
      } catch (err) {
        console.error('Callback error:', err);
        setError('Failed to complete authentication');
        setTimeout(() => router.push('/login'), 3000);
      }
    };
    
    handleCallback();
  }, [searchParams, router]);
  
  if (error) {
    return (
      <div className="error-container">
        <h2>Authentication Error</h2>
        <p>{error}</p>
        <p>Redirecting to login...</p>
      </div>
    );
  }
  
  return (
    <div className="loading-container">
      <h2>Completing sign in...</h2>
      <p>Please wait while we authenticate your account.</p>
    </div>
  );
}
```

## Backend Response Formats

### New User (Pending Approval) - Status 201
```json
{
  "message": "Account created successfully! Pending admin approval.",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_created": true,
  "pending_approval": true,
  "user_info": {
    "email": "user@example.com",
    "name": "John Doe",
    "profile_photo_url": "https://lh3.googleusercontent.com/..."
  },
  "note": "Your account has been created but requires admin approval before you can log in. You will be notified once approved."
}
```

**⚠️ Note**: No tokens are returned for new users!

### Existing User (Approved) - Status 200
```json
{
  "message": "Welcome back! Google login successful",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user_created": false,
  "user_info": {
    "email": "user@example.com",
    "name": "John Doe",
    "profile_photo_url": "https://lh3.googleusercontent.com/...",
    "user_type": "worker"
  }
}
```

**Note**: `user_type` is extracted from JWT token, not from user selection!

### Existing User (Not Approved) - Status 403
```json
{
  "error": "Account pending approval",
  "message": "Your account has been created but is pending admin approval. Please wait for approval before logging in.",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

### Error Response
```json
{
  "error": "Failed to exchange code for tokens",
  "details": "400 Client Error: Bad Request"
}
```

## TypeScript Types

```typescript
// types/auth.ts

export type UserType = 'worker' | 'employer' | 'admin';

export interface GoogleOAuthTokens {
  access: string;
  refresh: string;
}

export interface UserInfo {
  email: string;
  name: string;
  profile_photo_url: string;
  user_type?: UserType; // Optional - only present for approved users
}

export interface GoogleOAuthNewUserResponse {
  message: string;
  user_id: string;
  user_created: true;
  pending_approval: true;
  user_info: UserInfo;
  note: string;
}

export interface GoogleOAuthApprovedUserResponse {
  message: string;
  user_id: string;
  tokens: GoogleOAuthTokens;
  user_created: boolean;
  user_info: UserInfo & { user_type: UserType }; // user_type required for approved users
}

export interface GoogleOAuthPendingResponse {
  error: string;
  message: string;
  user_id: string;
  email: string;
}

export interface GoogleOAuthErrorResponse {
  error: string;
  details?: string;
  traceback?: string;
}

export type GoogleOAuthResponse = 
  | GoogleOAuthNewUserResponse 
  | GoogleOAuthApprovedUserResponse 
  | GoogleOAuthPendingResponse
  | GoogleOAuthErrorResponse;

// Type guards
export function isNewUser(response: GoogleOAuthResponse): response is GoogleOAuthNewUserResponse {
  return 'pending_approval' in response && response.pending_approval === true;
}

export function isApprovedUser(response: GoogleOAuthResponse): response is GoogleOAuthApprovedUserResponse {
  return 'tokens' in response;
}

export function isPendingApproval(response: GoogleOAuthResponse): response is GoogleOAuthPendingResponse {
  return 'error' in response && response.error === 'Account pending approval';
}
```

## Important Notes

### 1. No User Type Selection
- **Removed**: Users no longer select "Worker" or "Employer" during login
- **Default**: New users are created with `user_type='worker'`
- **Admin Control**: Admin assigns the correct role before approving the account
- **Token-based**: User type is extracted from JWT token after login

### 2. Admin Approval Workflow
1. User signs in with Google → Account created
2. User sees "Pending approval" message
3. Admin reviews account in admin panel
4. Admin assigns correct role (worker/employer/admin)
5. Admin approves account (`is_verified=True`)
6. User can now log in successfully

### 3. Google Cloud Console Configuration

Add this redirect URI in Google Cloud Console:
- `https://kazi-buddy.onrender.com/api/v1/auth/google/callback/`

For local development:
- `http://localhost:8000/api/v1/auth/google/callback/`

### 4. Token Storage

**Option A: localStorage**
```javascript
localStorage.setItem('access_token', data.tokens.access);
localStorage.setItem('refresh_token', data.tokens.refresh);
```

**Option B: httpOnly Cookies (Recommended)**
```javascript
// app/api/auth/set-tokens/route.ts
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  const { access, refresh } = await request.json();
  
  cookies().set('access_token', access, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7 // 7 days
  });
  
  cookies().set('refresh_token', refresh, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 30 // 30 days
  });
  
  return Response.json({ success: true });
}
```

### 5. Using JWT Tokens for API Requests

```typescript
// utils/api.ts
export async function authenticatedFetch(url: string, options: RequestInit = {}) {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  });
  
  // Handle token refresh if needed
  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`,
          'Content-Type': 'application/json',
        },
      });
    }
  }
  
  return response;
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token');
  
  try {
    const response = await fetch('https://kazi-buddy.onrender.com/api/v1/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return data.access;
  } catch {
    window.location.href = '/login';
    return null;
  }
}
```

## Pending Approval Page

Create a page to show users waiting for approval:

```tsx
// app/pending-approval/page.tsx
export default function PendingApproval() {
  return (
    <div className="pending-container">
      <h1>Account Pending Approval</h1>
      <p>
        Your account has been created successfully! However, it requires 
        admin approval before you can log in.
      </p>
      <p>
        You will receive an email notification once your account has been approved.
      </p>
      <p>
        Please check back later or contact support if you have any questions.
      </p>
    </div>
  );
}
```

## Common Issues

### Issue: "redirect_uri_mismatch"
**Solution**: Ensure the redirect_uri in your code **exactly matches** what's in Google Cloud Console (including trailing slash).

### Issue: User can't log in after Google signup
**Solution**: This is expected! New users require admin approval. Check if `is_verified=True` in the database.

### Issue: CORS errors
**Solution**: Ensure Django CORS settings allow your Next.js domain:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-nextjs-app.com",
]
```

## Support

If you encounter issues, check:
1. Browser console for JavaScript errors
2. Network tab for API response details
3. Django backend logs for server-side errors

The backend returns detailed error messages with `traceback` in development mode to help debug issues.
