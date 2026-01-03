# Google OAuth Integration Guide for Next.js Frontend

## Overview
This guide explains how to integrate Google OAuth login with the Kazi Buddy Django backend from your Next.js frontend application.

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

### Option 1: Simple Redirect (Recommended)

The simplest approach - just redirect to Google OAuth URL with proper parameters.

#### React/Next.js Component

```tsx
// components/GoogleLoginButton.tsx
'use client'; // if using App Router

interface GoogleLoginButtonProps {
  userType: 'worker' | 'employer';
  className?: string;
}

export function GoogleLoginButton({ userType, className }: GoogleLoginButtonProps) {
  const handleGoogleLogin = () => {
    // OAuth configuration
    const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const callbackUri = 'https://kazi-buddy.onrender.com/api/v1/auth/google/callback/';
    
    // IMPORTANT: Use state parameter to pass user_type
    // DO NOT modify the redirect_uri - it must match Google Console exactly
    const state = JSON.stringify({ user_type: userType });
    
    // Build Google OAuth URL
    const params = new URLSearchParams({
      client_id: googleClientId!,
      redirect_uri: callbackUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
      prompt: 'consent',
      state: state,
    });
    
    // Redirect to Google
    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  };
  
  return (
    <button onClick={handleGoogleLogin} className={className}>
      Sign in with Google as {userType}
    </button>
  );
}
```

#### Usage Example

```tsx
// app/login/page.tsx or pages/login.tsx
import { GoogleLoginButton } from '@/components/GoogleLoginButton';

export default function LoginPage() {
  return (
    <div>
      <h1>Sign In</h1>
      
      <div>
        <h2>Select Account Type</h2>
        <GoogleLoginButton userType="worker" className="btn-primary" />
        <GoogleLoginButton userType="employer" className="btn-primary" />
      </div>
    </div>
  );
}
```

### Option 2: With Frontend Callback Handler

If you want to intercept the callback on the frontend before storing tokens:

#### Callback Page

```tsx
// app/auth/google/callback/page.tsx (App Router)
// OR pages/auth/google/callback.tsx (Pages Router)
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
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');
      
      // Check for OAuth errors from Google
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
        // Forward to Django backend
        const response = await fetch(
          `https://kazi-buddy.onrender.com/api/v1/auth/google/callback/?code=${code}&state=${state}`
        );
        
        const data = await response.json();
        
        if (response.ok && data.tokens) {
          // Save tokens (choose your preferred method)
          localStorage.setItem('access_token', data.tokens.access);
          localStorage.setItem('refresh_token', data.tokens.refresh);
          
          // Save user info
          localStorage.setItem('user_info', JSON.stringify(data.user_info));
          
          // Redirect based on user type
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

#### Update Google Login Button for Option 2

If using frontend callback handler, update the redirect_uri in the button:

```tsx
const callbackUri = 'https://your-nextjs-app.com/auth/google/callback';
```

And add this to your **Google Cloud Console** as an authorized redirect URI.

## Backend Response Format

### Success Response (New User)
```json
{
  "message": "Account created successfully! Google login successful",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user_created": true,
  "user_info": {
    "email": "user@example.com",
    "name": "John Doe",
    "profile_photo_url": "https://lh3.googleusercontent.com/...",
    "user_type": "worker"
  }
}
```

### Success Response (Existing User)
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
  user_type: UserType;
}

export interface GoogleOAuthSuccessResponse {
  message: string;
  user_id: string;
  tokens: GoogleOAuthTokens;
  user_created: boolean;
  user_info: UserInfo;
}

export interface GoogleOAuthErrorResponse {
  error: string;
  details?: string;
  traceback?: string;
}

export type GoogleOAuthResponse = GoogleOAuthSuccessResponse | GoogleOAuthErrorResponse;

// Type guard
export function isOAuthError(
  response: GoogleOAuthResponse
): response is GoogleOAuthErrorResponse {
  return 'error' in response;
}
```

## Important Notes

### 1. State Parameter
**CRITICAL**: Always pass `user_type` via the `state` parameter, NOT by modifying the redirect_uri.

✅ **Correct:**
```javascript
const state = JSON.stringify({ user_type: 'worker' });
// redirect_uri stays constant
```

❌ **Wrong:**
```javascript
const callbackUri = 'https://kazi-buddy.onrender.com/api/v1/auth/google/callback/?user_type=worker';
// This will cause redirect_uri_mismatch error!
```

### 2. Google Cloud Console Configuration

Make sure these redirect URIs are added in Google Cloud Console:

**For Direct Backend Callback (Option 1):**
- `https://kazi-buddy.onrender.com/api/v1/auth/google/callback/`

**For Frontend Callback (Option 2):**
- `https://your-nextjs-app.com/auth/google/callback`
- `http://localhost:3000/auth/google/callback` (for local development)

### 3. Token Storage

Choose one of these methods to store JWT tokens:

**Option A: localStorage (Simple, but vulnerable to XSS)**
```javascript
localStorage.setItem('access_token', data.tokens.access);
localStorage.setItem('refresh_token', data.tokens.refresh);
```

**Option B: httpOnly Cookies (More secure)**
```javascript
// Set cookies via API route
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

### 4. Using JWT Tokens for API Requests

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
      // Retry request with new token
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
    // Refresh failed, redirect to login
    window.location.href = '/login';
    return null;
  }
}
```

## Testing Locally

For local development:

1. Update callback URI in your code:
   ```typescript
   const callbackUri = 'http://localhost:8000/api/v1/auth/google/callback/';
   ```

2. Add to Google Cloud Console:
   - `http://localhost:8000/api/v1/auth/google/callback/`

3. Make sure Django backend is running on `localhost:8000`

## Common Issues

### Issue: "redirect_uri_mismatch"
**Solution**: Ensure the redirect_uri in your code **exactly matches** what's in Google Cloud Console (including trailing slash).

### Issue: "Invalid state parameter"
**Solution**: Make sure you're JSON-encoding the state object:
```javascript
const state = JSON.stringify({ user_type: userType });
```

### Issue: CORS errors
**Solution**: Ensure Django CORS settings allow your Next.js domain in `settings.py`:
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
