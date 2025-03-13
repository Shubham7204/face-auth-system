import { useState, useEffect, useRef } from 'react';

interface AuthState {
  status: string;
  aadhaar_score: number;
  bank_score: number;
  avg_score: number;
  threshold: number;
  verification_details?: {
    aadhaar_verified: boolean;
    bank_verified: boolean;
    timestamp: string;
  };
  auth_result?: {
    success: boolean;
    score: number;
    log_message: string;
  };
}

function App() {
  const [authState, setAuthState] = useState<AuthState | null>(null);
  const [loading, setLoading] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Check for stored auth state
    const storedAuth = localStorage.getItem('authState');
    if (storedAuth) {
      const authData = JSON.parse(storedAuth);
      if (authData.timestamp && (new Date().getTime() - new Date(authData.verification_details.timestamp).getTime()) < 3600000) {
        setAuthState(authData);
      } else {
        localStorage.removeItem('authState');
      }
    }

    // Start webcam
    startWebcam();
  }, []);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error('Webcam access denied:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authState');
    setAuthState(null);
  };

  const captureAndVerify = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setLoading(true);
    const canvas = canvasRef.current;
    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    if (!context) return;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) return;

      const formData = new FormData();
      formData.append('live_image', blob, 'live_image.jpg');

      try {
        const response = await fetch('http://127.0.0.1:5000/verify', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        setAuthState(data);
        
        if (data.status !== 'error') {
          localStorage.setItem('authState', JSON.stringify(data));
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    }, 'image/jpeg');
  };

  return (
    <div className="max-w-4xl mx-auto my-12 p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-[#075985] text-2xl font-bold mb-6">Union Bank Face Authentication</h2>
      
      <div className="mb-6">
        <video 
          ref={videoRef} 
          autoPlay 
          className="w-full border-4 border-[#075985] rounded-lg"
        ></video>
        <canvas ref={canvasRef} className="hidden"></canvas>
      </div>

      <button 
        onClick={captureAndVerify} 
        disabled={loading}
        className={`px-6 py-3 text-lg font-medium rounded-md text-white transition-colors
          ${loading 
            ? 'bg-gray-400 cursor-not-allowed' 
            : 'bg-[#075985] hover:bg-[#054964] active:bg-[#043b52]'
          }`}
      >
        {loading ? 'Processing...' : 'Capture & Verify'}
      </button>

      {authState && (
        <div className="mt-8">
          <div className={`p-4 rounded-md mb-6 text-lg font-medium ${
            authState.status === 'success' 
              ? 'bg-green-600 text-white' 
              : 'bg-[#dc2626] text-white'
          }`}>
            {authState.auth_result?.log_message}
          </div>

          <div className="bg-[#e0f2fe] p-6 rounded-lg text-left">
            {/* Aadhaar Score */}
            <div className="mb-4">
              <div className="mb-1">Aadhaar Match: {authState.aadhaar_score}%</div>
              <div className="h-3 bg-gray-200 rounded-full relative">
                <div 
                  className="h-full bg-[#075985] rounded-full transition-all duration-300"
                  style={{ width: `${authState.aadhaar_score}%` }}
                />
              </div>
            </div>

            {/* Bank Score */}
            <div className="mb-4">
              <div className="mb-1">Bank Match: {authState.bank_score}%</div>
              <div className="h-3 bg-gray-200 rounded-full relative">
                <div 
                  className="h-full bg-[#075985] rounded-full transition-all duration-300"
                  style={{ width: `${authState.bank_score}%` }}
                />
              </div>
            </div>

            {/* Overall Score */}
            <div className="mb-4">
              <div className="mb-1 text-lg font-bold text-[#075985]">
                Overall Match: {authState.avg_score}%
              </div>
              <div className="h-3 bg-gray-200 rounded-full relative">
                <div 
                  className="h-full bg-[#075985] rounded-full transition-all duration-300"
                  style={{ width: `${authState.avg_score}%` }}
                />
                <div 
                  className="absolute top-[-4px] w-0.5 h-5 bg-[#dc2626]"
                  style={{ left: `${authState.threshold}%` }}
                />
              </div>
            </div>

            <div className="text-gray-600 italic mt-3">
              Required threshold: {authState.threshold}%
            </div>

            {authState.verification_details && (
              <div className="text-gray-600 text-sm mt-4">
                Verified at: {authState.verification_details.timestamp}
              </div>
            )}
          </div>

          {authState.status === 'success' && (
            <button 
              onClick={handleLogout} 
              className="mt-6 px-5 py-2.5 text-lg font-medium rounded-md text-white 
                bg-[#dc2626] hover:bg-[#b91c1c] transition-colors"
            >
              Logout
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
