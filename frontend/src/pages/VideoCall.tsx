import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Mic, MicOff, Video as VideoIcon, VideoOff, PhoneOff } from "lucide-react";

const STUN_SERVERS = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

export default function VideoCall() {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  const [status, setStatus] = useState("Connecting...");
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (cancelled) return;
      localStreamRef.current = stream;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;

      const pc = new RTCPeerConnection(STUN_SERVERS);
      pcRef.current = pc;
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      pc.ontrack = (event) => {
        if (remoteVideoRef.current) remoteVideoRef.current.srcObject = event.streams[0];
        setStatus("Connected");
      };

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/telemedicine/ws/${roomId}`);
      wsRef.current = ws;

      pc.onicecandidate = (event) => {
        if (event.candidate && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ice-candidate", candidate: event.candidate }));
        }
      };

      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "peer-joined") {
          // Second participant: initiate the offer.
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          ws.send(JSON.stringify({ type: "offer", sdp: offer }));
        } else if (message.type === "offer") {
          await pc.setRemoteDescription(new RTCSessionDescription(message.sdp));
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          ws.send(JSON.stringify({ type: "answer", sdp: answer }));
        } else if (message.type === "answer") {
          await pc.setRemoteDescription(new RTCSessionDescription(message.sdp));
        } else if (message.type === "ice-candidate") {
          try {
            await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
          } catch {
            /* ignore late candidates */
          }
        } else if (message.type === "peer-left") {
          setStatus("The other participant left the call.");
        } else if (message.type === "room-full") {
          setStatus("This call already has two participants.");
        }
      };

      ws.onopen = () => setStatus("Waiting for the other participant to join...");
    }

    start().catch(() => setStatus("Could not access camera/microphone."));

    return () => {
      cancelled = true;
      wsRef.current?.close();
      pcRef.current?.close();
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [roomId]);

  function toggleMic() {
    const track = localStreamRef.current?.getAudioTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setMicOn(track.enabled);
    }
  }

  function toggleCam() {
    const track = localStreamRef.current?.getVideoTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setCamOn(track.enabled);
    }
  }

  function hangUp() {
    wsRef.current?.close();
    pcRef.current?.close();
    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    navigate("/appointments");
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950">
      <div className="relative flex-1">
        <video ref={remoteVideoRef} autoPlay playsInline className="h-full w-full bg-black object-cover" />
        <video
          ref={localVideoRef}
          autoPlay
          playsInline
          muted
          className="absolute bottom-6 right-6 h-36 w-48 rounded-xl border-2 border-white/20 bg-black object-cover shadow-lg"
        />
        <div className="absolute left-6 top-6 rounded-full bg-black/50 px-4 py-1.5 text-sm text-white">{status}</div>
      </div>

      <div className="flex items-center justify-center gap-4 bg-slate-900 py-5">
        <button
          onClick={toggleMic}
          className={`flex h-12 w-12 items-center justify-center rounded-full ${micOn ? "bg-slate-700 text-white" : "bg-red-600 text-white"}`}
        >
          {micOn ? <Mic size={18} /> : <MicOff size={18} />}
        </button>
        <button
          onClick={toggleCam}
          className={`flex h-12 w-12 items-center justify-center rounded-full ${camOn ? "bg-slate-700 text-white" : "bg-red-600 text-white"}`}
        >
          {camOn ? <VideoIcon size={18} /> : <VideoOff size={18} />}
        </button>
        <button onClick={hangUp} className="flex h-12 w-12 items-center justify-center rounded-full bg-red-600 text-white">
          <PhoneOff size={18} />
        </button>
      </div>
    </div>
  );
}
