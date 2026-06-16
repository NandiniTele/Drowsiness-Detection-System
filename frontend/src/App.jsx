import { useEffect, useState } from 'react';

// Formatter for elapsed simulation time (session duration)
const formatDuration = (seconds) => {
  if (seconds === undefined || seconds === null) return '00:00:00';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return [
    hrs.toString().padStart(2, '0'),
    mins.toString().padStart(2, '0'),
    secs.toString().padStart(2, '0')
  ].join(':');
};

// Formatter for short time strings
const formatTime = (isoString) => {
  if (!isoString) return '';
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    return '';
  }
};

export default function App() {
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Poll backend APIs
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch real-time metrics
        const statusRes = await fetch('/api/status');
        if (!statusRes.ok) throw new Error('Failed to fetch status');
        const statusData = await statusRes.json();
        setStatus(statusData);

        // Fetch recent alerts
        const alertsRes = await fetch('/api/alerts');
        if (alertsRes.ok) {
          const alertsData = await alertsRes.json();
          setAlerts(alertsData);
        }

        setIsConnected(true);
        setError(null);
      } catch (e) {
        setIsConnected(false);
        setError(e.message || 'API connection lost');
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  // Determine styles based on alert level
  const isDanger = status?.alert_level === 'danger';
  const isWarning = status?.alert_level === 'warning';
  const isNormal = status?.alert_level === 'normal' || !status;

  const statusBg = isDanger
    ? 'bg-red-950/30 border-red-500/30 text-red-200'
    : isWarning
    ? 'bg-amber-950/30 border-amber-500/30 text-amber-200'
    : 'bg-emerald-950/20 border-emerald-500/20 text-emerald-200';

  const statusBadge = isDanger
    ? 'bg-red-500 text-white shadow-lg shadow-red-500/40 animate-pulse'
    : isWarning
    ? 'bg-amber-500 text-slate-900 shadow-lg shadow-amber-500/40'
    : 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* HEADER */}
      <header className="border-b border-slate-900 bg-slate-900/30 backdrop-blur-md px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-slate-200 font-mono">NEURALWATCH</h1>
            <p className="text-xs text-slate-400 uppercase tracking-widest font-mono">Driver Drowsiness AI Telemetry</p>
          </div>
        </div>

        {/* CONNECTION & SESSION STATUS */}
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono">SESSION TIME:</span>
            <span className="font-mono text-blue-400 font-semibold bg-blue-950/40 border border-blue-900/30 px-3 py-1 rounded-md">
              {formatDuration(status?.session_duration)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-red-500'}`} />
            <span className={`w-2 h-2 rounded-full -ml-4 ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="font-mono text-xs text-slate-400">
              {isConnected ? 'LIVE INTERACTIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </header>

      {/* ERROR DISMISSAL */}
      {error && (
        <div className="bg-red-950/40 border border-red-900/50 text-red-400 text-sm px-6 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Connection lost to backend API. Please run <code>python -m backend.main</code> to restore real-time data feeds.</span>
          </div>
        </div>
      )}

      {/* DASHBOARD CONTENT GRID */}
      <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: CRITICAL ALERTS & GAUGE (col-span-5) */}
        <section className="lg:col-span-5 flex flex-col gap-6">
          
          {/* DRIVER ALARM BANNER */}
          <div className={`border rounded-2xl p-6 transition-all duration-300 ${statusBg} flex flex-col justify-between h-[180px] shadow-xl relative overflow-hidden`}>
            {/* Ambient Pulse Glow in Dangerous states */}
            {isDanger && <div className="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none" />}
            {isWarning && <div className="absolute inset-0 bg-amber-500/5 animate-pulse pointer-events-none" />}
            
            <div className="flex justify-between items-start z-10">
              <span className="text-xs font-mono font-semibold tracking-widest text-slate-400 uppercase">
                Alert Status
              </span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wide ${statusBadge}`}>
                {status?.alert_level || 'UNKNOWN'}
              </span>
            </div>

            <div className="mt-4 z-10">
              <h2 className="text-3xl font-extrabold tracking-tight">
                {status?.alert ? 'WARNING: DROWSINESS' : 'DRIVER ATTENTIVE'}
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                {status?.alert 
                  ? 'Immediate reaction required! High fatigue patterns detected.' 
                  : 'All biometrics are within optimal baseline levels.'}
              </p>
            </div>
          </div>

          {/* DROWSINESS INDEX progress bar */}
          <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 flex flex-col justify-between flex-1 shadow-lg">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-mono font-semibold tracking-widest text-slate-400 uppercase">
                  Drowsiness score
                </span>
                <span className="text-xs text-slate-400 font-mono">Confidence: {status ? (status.confidence * 100).toFixed(0) : 0}%</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`text-5xl font-black font-mono tracking-tighter ${
                  isDanger ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-emerald-500'
                }`}>
                  {status ? status.drowsiness_score.toFixed(0) : '0'}
                </span>
                <span className="text-lg text-slate-500 font-mono">%</span>
              </div>
            </div>

            {/* Visual Progress Bar */}
            <div className="my-6">
              <div className="h-4 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-900">
                <div 
                  className={`h-full rounded-full transition-all duration-500 shadow-md ${
                    isDanger 
                      ? 'bg-gradient-to-r from-red-600 to-red-500 shadow-red-500/20' 
                      : isWarning 
                      ? 'bg-gradient-to-r from-amber-600 to-amber-500 shadow-amber-500/20' 
                      : 'bg-gradient-to-r from-emerald-600 to-emerald-500 shadow-emerald-500/20'
                  }`}
                  style={{ width: `${status ? status.drowsiness_score : 0}%` }}
                />
              </div>
              
              {/* Scale Labels */}
              <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-2 px-1">
                <span>0% ATTENTIVE</span>
                <span>35% FATIGUE THRESHOLD</span>
                <span>60% DANGER ZONE</span>
              </div>
            </div>

            {/* Quick Microstats */}
            <div className="grid grid-cols-2 gap-4 border-t border-slate-800/60 pt-4">
              <div>
                <span className="block text-[10px] font-mono text-slate-400 uppercase">Blink Frequency</span>
                <span className="text-lg font-bold text-slate-200 font-mono">
                  {status ? status.blink_rate.toFixed(1) : '0.0'} <span className="text-xs text-slate-500 font-normal">/min</span>
                </span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-slate-400 uppercase">Yawn Count</span>
                <span className="text-lg font-bold text-slate-200 font-mono">
                  {status ? status.yawn_count : '0'} <span className="text-xs text-slate-500 font-normal">total</span>
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* MIDDLE COLUMN: REAL-TIME BIOMETRICS (col-span-4) */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 shadow-lg flex-1 flex flex-col justify-between">
            <h3 className="text-xs font-mono font-semibold tracking-widest text-slate-400 uppercase mb-6">
              Face Analysis Metrics
            </h3>

            {/* EYE ASPECT RATIO (EAR) */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  EYE ASPECT RATIO (EAR)
                </span>
                <span className={`font-bold ${status?.eye_aspect_ratio < 0.20 ? 'text-red-400' : 'text-blue-400'}`}>
                  {status ? status.eye_aspect_ratio.toFixed(3) : '0.000'}
                </span>
              </div>
              <div className="h-2 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-900">
                <div 
                  className={`h-full rounded-full transition-all duration-300 ${
                    status?.eye_aspect_ratio < 0.20 ? 'bg-red-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${Math.min(100, (status?.eye_aspect_ratio || 0) / 0.4 * 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-slate-500 mt-1">
                <span>0.00 CLOSED</span>
                <span className="text-red-400/80">0.20 THRESHOLD</span>
                <span>0.40 WIDE</span>
              </div>

              {/* L / R EAR Details */}
              <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] font-mono text-slate-400">
                <div className="bg-slate-950/40 border border-slate-900/50 rounded p-1.5 flex justify-between">
                  <span>L-EAR:</span>
                  <span className="font-semibold text-slate-200">{status ? status.left_ear.toFixed(3) : '0.000'}</span>
                </div>
                <div className="bg-slate-950/40 border border-slate-900/50 rounded p-1.5 flex justify-between">
                  <span>R-EAR:</span>
                  <span className="font-semibold text-slate-200">{status ? status.right_ear.toFixed(3) : '0.000'}</span>
                </div>
              </div>
            </div>

            {/* MOUTH ASPECT RATIO (MAR) */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.871 4A17.926 17.926 0 003 12c0 2.871.67 5.59 1.871 8m14.13 0a17.93 17.93 0 01-1.87-8c0-2.871.67-5.59 1.87-8M9 9h1.5m3 0H15m-5.25 6h4.5" />
                  </svg>
                  MOUTH ASPECT RATIO (MAR)
                </span>
                <span className={`font-bold ${status?.mouth_aspect_ratio > 0.55 ? 'text-amber-400 animate-pulse' : 'text-blue-400'}`}>
                  {status ? status.mouth_aspect_ratio.toFixed(3) : '0.000'}
                </span>
              </div>
              <div className="h-2 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-900">
                <div 
                  className={`h-full rounded-full transition-all duration-300 ${
                    status?.mouth_aspect_ratio > 0.55 ? 'bg-amber-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${Math.min(100, (status?.mouth_aspect_ratio || 0) / 0.8 * 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-slate-500 mt-1">
                <span>0.10 CLOSED</span>
                <span className="text-amber-400/80">0.55 YAWNING</span>
                <span>0.80 OPEN</span>
              </div>
            </div>

            {/* HEAD POSTURE */}
            <div className="border-t border-slate-800/60 pt-6">
              <span className="text-xs font-mono text-slate-400 uppercase block mb-3">Head Pose Telemetry</span>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3 flex flex-col justify-center">
                  <span className="text-[10px] font-mono text-slate-500 uppercase">Pitch (Nod)</span>
                  <span className="text-xl font-bold font-mono text-slate-200 mt-1">
                    {status ? status.head_pitch.toFixed(1) : '0.0'}°
                  </span>
                  <div className="w-full bg-slate-900 h-1 rounded-full mt-2 relative">
                    <div 
                      className="absolute bg-blue-500 h-1 rounded-full transition-all duration-300"
                      style={{ 
                        left: status?.head_pitch < 0 ? 'auto' : '50%',
                        right: status?.head_pitch < 0 ? '50%' : 'auto',
                        width: `${Math.min(50, Math.abs(status?.head_pitch || 0) * 2.5)}%` 
                      }}
                    />
                  </div>
                </div>

                <div className="bg-slate-950/40 border border-slate-900 rounded-xl p-3 flex flex-col justify-center">
                  <span className="text-[10px] font-mono text-slate-500 uppercase">Yaw (Turn)</span>
                  <span className="text-xl font-bold font-mono text-slate-200 mt-1">
                    {status ? status.head_yaw.toFixed(1) : '0.0'}°
                  </span>
                  <div className="w-full bg-slate-900 h-1 rounded-full mt-2 relative">
                    <div 
                      className="absolute bg-blue-500 h-1 rounded-full transition-all duration-300"
                      style={{ 
                        left: status?.head_yaw < 0 ? 'auto' : '50%',
                        right: status?.head_yaw < 0 ? '50%' : 'auto',
                        width: `${Math.min(50, Math.abs(status?.head_yaw || 0) * 2.5)}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: ALERTS LOG STREAM (col-span-3) */}
        <section className="lg:col-span-3 flex flex-col gap-6">
          <div className="bg-slate-900/40 border border-slate-900 rounded-2xl p-6 shadow-lg flex-1 flex flex-col justify-between h-[450px]">
            <div className="flex justify-between items-center mb-4 border-b border-slate-800/60 pb-3">
              <h3 className="text-xs font-mono font-semibold tracking-widest text-slate-400 uppercase">
                Activity Alarms
              </h3>
              <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                {alerts.length} LOGS
              </span>
            </div>

            {/* SCROLLING ALERTS LIST */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[350px] scrollbar-thin scrollbar-thumb-slate-800">
              {alerts.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-4">
                  <svg className="w-8 h-8 text-slate-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-xs text-slate-500 font-mono">No warning events logged during this session.</p>
                </div>
              ) : (
                alerts.map((alertItem) => {
                  const itemIsDanger = alertItem.level === 'danger';
                  const itemIsWarning = alertItem.level === 'warning';
                  
                  const itemBorder = itemIsDanger 
                    ? 'border-red-900/40 bg-red-950/15' 
                    : itemIsWarning 
                    ? 'border-amber-900/40 bg-amber-950/15' 
                    : 'border-slate-800 bg-slate-900/20';

                  const badgeText = itemIsDanger 
                    ? 'text-red-400' 
                    : itemIsWarning 
                    ? 'text-amber-400' 
                    : 'text-slate-400';

                  return (
                    <div 
                      key={alertItem.id} 
                      className={`p-3 border rounded-xl flex flex-col gap-1 transition-all duration-300 hover:border-slate-700/50 ${itemBorder}`}
                    >
                      <div className="flex justify-between items-center text-[10px] font-mono">
                        <span className={`font-bold uppercase tracking-wider ${badgeText}`}>
                          [{alertItem.level}]
                        </span>
                        <span className="text-slate-500">
                          {formatTime(alertItem.timestamp)}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 leading-normal">
                        {alertItem.message}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </section>
        
      </main>

      {/* FOOTER */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-mono text-slate-500">
        <div>
          <span>SYSTEM CALIBRATED: EYE PATTERN INDEX, YAWN FREQUENCY, ATTRIBUTE POSE</span>
        </div>
        <div>
          <span>NEURALWATCH V1.0.0</span>
        </div>
      </footer>
    </div>
  );
}
