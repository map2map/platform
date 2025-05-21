import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    // First, check if we have an access token in the URL hash
    const checkForToken = () => {
      // If there's a hash with token info, the backend has already set the cookie
      // and we can proceed to check authentication
      if (window.location.hash) {
        // Remove the hash from the URL without refreshing
        window.history.replaceState({}, document.title, window.location.pathname);
      }
      checkAuth();
    };

    // Check if we're authenticated
    const checkAuth = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/check`, {
          credentials: 'include',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        });
        
        if (response.ok) {
          // If authenticated, redirect to root which will show the dashboard
          navigate('/', { replace: true });
        } else {
          // If not authenticated, redirect to login
          console.error('Authentication failed');
          navigate('/login', { replace: true });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        navigate('/', { replace: true });
      }
    };

    // Small delay to ensure the cookie is set
    const timer = setTimeout(checkForToken, 500);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900">Completing sign in...</h2>
        <p className="mt-2 text-gray-600">Please wait while we redirect you.</p>
      </div>
    </div>
  );
} 