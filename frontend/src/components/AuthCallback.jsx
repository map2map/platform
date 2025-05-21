import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleAuth = async () => {
      try {
        // Extract token from URL hash if present
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const token = hashParams.get('token');
        
        if (token) {
          // Store the token in localStorage as a fallback (optional)
          localStorage.setItem('auth_token', token);
          
          // Clean up the URL
          window.history.replaceState({}, document.title, window.location.pathname);
        }

        // Verify authentication with the backend
        const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/check`, {
          credentials: 'include',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        });

        if (response.ok) {
          // If authenticated, redirect to dashboard
          navigate('/', { replace: true });
        } else {
          // If not authenticated, try to use the token from the URL
          if (token) {
            const userResponse = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/check`, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
              credentials: 'include'
            });

            if (userResponse.ok) {
              navigate('/', { replace: true });
              return;
            }
          }
          
          console.error('Authentication failed');
          navigate('/login', { replace: true });
        }
      } catch (error) {
        console.error('Auth error:', error);
        setError('Authentication failed. Please try again.');
        setTimeout(() => navigate('/login', { replace: true }), 3000);
      }
    };

    // Small delay to ensure any redirects have completed
    const timer = setTimeout(handleAuth, 500);
    return () => clearTimeout(timer);
  }, [navigate, location]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-red-600">Error</h2>
          <p className="mt-2 text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900">Completing sign in...</h2>
        <p className="mt-2 text-gray-600">Please wait while we redirect you.</p>
      </div>
    </div>
  );
} 