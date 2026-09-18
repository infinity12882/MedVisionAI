import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Calendar, Plus, Video, X } from "lucide-react";
import { appointmentsApi, careApi } from "@/api";
import { useAppSelector } from "@/hooks/redux";
import type { AppointmentItem, AppointmentStatus, DoctorPublic, TimeSlot } from "@/types";
import { formatDateTime } from "@/utils/format";

const STATUS_COLOR: Record<AppointmentStatus, string> = {
  pending: "badge-moderate",
  confirmed: "badge-low",
  completed: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  cancelled: "badge-emergency",
};

export default function Appointments() {
  const { user } = useAppSelector((s) => s.auth);
  const [appointments, setAppointments] = useState<AppointmentItem[]>([]);

  function refresh() {
    appointmentsApi.myAppointments().then(setAppointments);
  }

  useEffect(refresh, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Appointments</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {user?.role === "doctor" ? "Manage your availability and patient bookings." : "Book a consultation with a doctor."}
        </p>
      </div>

      {user?.role === "doctor" ? <DoctorSlotManager onBooked={refresh} /> : <PatientBookingFlow onBooked={refresh} />}

      <div>
        <h2 className="mb-3 font-display text-lg font-bold text-slate-900 dark:text-white">My Appointments</h2>
        {appointments.length === 0 ? (
          <p className="text-sm text-slate-400">No appointments yet.</p>
        ) : (
          <div className="space-y-3">
            {appointments.map((a) => (
              <div key={a.id} className="card flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200">
                    <Calendar size={14} /> {formatDateTime(a.scheduled_at)} ({a.duration_minutes} min)
                  </p>
                  {a.reason && <p className="mt-1 text-xs text-slate-500">{a.reason}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`badge ${STATUS_COLOR[a.status]} capitalize`}>{a.status}</span>
                  {a.status === "confirmed" && (
                    <Link to={`/call/${a.id}`} className="btn-secondary text-xs">
                      <Video size={13} /> Join Call
                    </Link>
                  )}
                  {user?.role === "doctor" && a.status === "pending" && (
                    <button
                      onClick={() => appointmentsApi.updateStatus(a.id, "confirmed").then(refresh)}
                      className="text-xs font-semibold text-brand-600 hover:underline"
                    >
                      Confirm
                    </button>
                  )}
                  {user?.role === "patient" && (a.status === "pending" || a.status === "confirmed") && (
                    <button
                      onClick={() => {
                        if (confirm("Are you sure you want to cancel this appointment?")) {
                          appointmentsApi.cancel(a.id).then(refresh);
                        }
                      }}
                      className="text-xs font-semibold text-red-600 hover:underline"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PatientBookingFlow({ onBooked }: { onBooked: () => void }) {
  const [doctors, setDoctors] = useState<DoctorPublic[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<string>("");
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [reason, setReason] = useState("");

  useEffect(() => {
    careApi.listDoctors().then(setDoctors);
  }, []);

  useEffect(() => {
    if (selectedDoctor) appointmentsApi.listSlots(selectedDoctor).then(setSlots);
  }, [selectedDoctor]);

  async function handleBook(slotId: string) {
    await appointmentsApi.book(selectedDoctor, slotId, reason || undefined);
    setReason("");
    appointmentsApi.listSlots(selectedDoctor).then(setSlots);
    onBooked();
  }

  return (
    <div className="card space-y-3">
      <h2 className="font-display text-base font-bold text-slate-900 dark:text-white">Book a Consultation</h2>
      <select value={selectedDoctor} onChange={(e) => setSelectedDoctor(e.target.value)} className="input-field">
        <option value="">Select a doctor...</option>
        {doctors.map((d) => (
          <option key={d.user_id} value={d.user_id}>
            Dr. {d.full_name} — {d.specialty} {d.is_verified ? "✓" : ""}
          </option>
        ))}
      </select>

      {selectedDoctor && (
        <>
          <input
            className="input-field"
            placeholder="Reason for visit (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          {slots.length === 0 ? (
            <p className="text-xs text-slate-400">No open slots for this doctor right now.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {slots.map((s) => (
                <button key={s.id} onClick={() => handleBook(s.id)} className="btn-secondary text-xs">
                  {formatDateTime(s.start_time)}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function DoctorSlotManager({ onBooked }: { onBooked: () => void }) {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [mySlots, setMySlots] = useState<TimeSlot[]>([]);
  const { user } = useAppSelector((s) => s.auth);

  function refreshSlots() {
    if (user) appointmentsApi.listSlots(user.id).then(setMySlots);
  }

  useEffect(refreshSlots, [user]);

  async function handleCreate() {
    if (!start || !end) return;
    await appointmentsApi.createSlot(new Date(start).toISOString(), new Date(end).toISOString());
    setStart("");
    setEnd("");
    refreshSlots();
    onBooked();
  }

  return (
    <div className="card space-y-3">
      <h2 className="font-display text-base font-bold text-slate-900 dark:text-white">Add Availability Slot</h2>
      <div className="flex flex-wrap gap-2">
        <input type="datetime-local" className="input-field flex-1" value={start} onChange={(e) => setStart(e.target.value)} />
        <input type="datetime-local" className="input-field flex-1" value={end} onChange={(e) => setEnd(e.target.value)} />
        <button onClick={handleCreate} className="btn-primary">
          <Plus size={14} /> Add
        </button>
      </div>

      {mySlots.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2">
          {mySlots.map((s) => (
            <span
              key={s.id}
              className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300"
            >
              {formatDateTime(s.start_time)}
              {!s.is_booked && (
                <button onClick={() => appointmentsApi.deleteSlot(s.id).then(refreshSlots)} className="text-red-400">
                  <X size={12} />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
