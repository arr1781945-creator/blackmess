import { useEffect, useRef, useState } from 'react'

interface Props {
  user: { name: string; avatar: string }
  onClose: () => void
}

export function VideoCall({ user, onClose }: Props) {
  const localRef = useRef<HTMLVideoElement>(null)
  const [muted, setMuted] = useState(false)
  const [videoOff, setVideoOff] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [status, setStatus] = useState<'connecting'|'connected'|'error'>('connecting')
  const [errorMsg, setErrorMsg] = useState('')
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    startCamera()
    const timer = setInterval(() => setSeconds(s => s + 1), 1000)
    return () => {
      clearInterval(timer)
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: true
      })
      streamRef.current = stream
      if (localRef.current) {
        localRef.current.srcObject = stream
      }
      setTimeout(() => setStatus('connected'), 1500)
    } catch(e: any) {
      if (e.name === 'NotAllowedError') {
        setErrorMsg('Izin kamera ditolak!')
      } else {
        setErrorMsg('Kamera tidak tersedia')
      }
      setStatus('error')
    }
  }

  const toggleMute = () => {
    streamRef.current?.getAudioTracks().forEach(t => { t.enabled = !t.enabled })
    setMuted(!muted)
  }

  const toggleVideo = () => {
    streamRef.current?.getVideoTracks().forEach(t => { t.enabled = !t.enabled })
    setVideoOff(!videoOff)
  }

  const handleEnd = () => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    onClose()
  }

  const fmt = (s: number) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`

  if (status === 'error') return (
    <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-20 h-20 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-4">
          <svg className="w-10 h-10 text-red-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <p className="text-red-400 font-semibold mb-4">{errorMsg}</p>
        <button onClick={handleEnd} className="px-6 py-2.5 rounded-xl bg-white text-black font-bold text-sm">Tutup</button>
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Remote area */}
      <div className="flex-1 relative bg-[#0a0a0a] flex items-center justify-center">
        {/* Remote placeholder */}
        <div className="text-center">
          <div className="w-28 h-28 rounded-full bg-gray-800 flex items-center justify-center text-white text-5xl font-bold mx-auto mb-4 shadow-2xl">
            {user.avatar}
          </div>
          <p className="text-white font-semibold text-xl">{user.name}</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400 animate-pulse'}`}/>
            <p className="text-gray-400 text-sm">
              {status === 'connecting' ? 'Menghubungkan...' : fmt(seconds)}
            </p>
          </div>
        </div>

        {/* Local video */}
        <div className="absolute bottom-4 right-4 w-28 h-36 rounded-2xl overflow-hidden bg-gray-900 border-2 border-gray-700 shadow-xl">
          {!videoOff ? (
            <video ref={localRef} autoPlay muted playsInline className="w-full h-full object-cover"/>
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-900">
              <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-white text-sm font-bold">
                {user.avatar[0]}
              </div>
            </div>
          )}
          <div className="absolute bottom-1 left-0 right-0 text-center">
            <span className="text-white text-xs bg-black/50 px-2 py-0.5 rounded-full">Kamu</span>
          </div>
        </div>

        {/* Status badge */}
        {status === 'connected' && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/60 backdrop-blur px-3 py-1.5 rounded-full">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
            <span className="text-white text-xs font-medium">{fmt(seconds)}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="h-28 bg-[#0a0a0a] border-t border-gray-800 flex items-center justify-center gap-5">
        <div className="flex flex-col items-center gap-1">
          <button onClick={toggleMute}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${muted ? 'bg-red-500' : 'bg-gray-800 hover:bg-gray-700'}`}>
            {muted ? (
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"/>
              </svg>
            ) : (
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
              </svg>
            )}
          </button>
          <span className="text-gray-500 text-xs">{muted ? 'Bisu' : 'Suara'}</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <button onClick={handleEnd}
            className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center shadow-lg transition-all">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"/>
            </svg>
          </button>
          <span className="text-gray-500 text-xs">Akhiri</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <button onClick={toggleVideo}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${videoOff ? 'bg-red-500' : 'bg-gray-800 hover:bg-gray-700'}`}>
            {videoOff ? (
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18"/>
              </svg>
            ) : (
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
            )}
          </button>
          <span className="text-gray-500 text-xs">{videoOff ? 'Video Mati' : 'Video'}</span>
        </div>
      </div>
    </div>
  )
}
