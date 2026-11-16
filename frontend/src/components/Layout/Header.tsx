import { Wifi, WifiOff, Cloud, CloudOff, Bell } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface HeaderProps {
  fogOnline?: number;
  fogTotal?: number;
  cloudConnected?: boolean;
}

export default function Header({ fogOnline = 3, fogTotal = 3, cloudConnected = true }: HeaderProps) {
  const { connected: wsConnected } = useWebSocket();

  return (
    <header className="h-14 bg-white border-b border-sk-border px-6 flex items-center justify-between shadow-sm z-10">
      {/* Left: breadcrumb placeholder */}
      <div className="text-sm text-sk-text-secondary font-medium">
        Agricultural Intelligence Dashboard
      </div>

      {/* Right: Status pills */}
      <div className="flex items-center gap-3">
        {/* WebSocket */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          wsConnected ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
        }`}>
          {wsConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          WS {wsConnected ? 'Live' : 'Offline'}
        </div>

        {/* Fog nodes */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          fogOnline === fogTotal ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${fogOnline === fogTotal ? 'bg-green-500' : 'bg-yellow-500'}`} />
          Fog: {fogOnline}/{fogTotal} Online
        </div>

        {/* Cloud */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          cloudConnected ? 'bg-blue-50 text-blue-700' : 'bg-red-50 text-red-600'
        }`}>
          {cloudConnected ? <Cloud className="w-3 h-3" /> : <CloudOff className="w-3 h-3" />}
          Cloud: {cloudConnected ? 'Connected' : 'Disconnected'}
        </div>

        {/* Bell */}
        <button className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-sk-bg transition-colors">
          <Bell className="w-4 h-4 text-sk-text-secondary" />
        </button>
      </div>
    </header>
  );
}
