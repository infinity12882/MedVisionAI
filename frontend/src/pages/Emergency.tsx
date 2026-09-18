import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Phone, AlertTriangle, Plus, Trash2, Loader2, Building2, Pill } from "lucide-react";
import { useTranslation } from "react-i18next";
import { emergencyApi } from "@/api";
import { extractErrorMessage } from "@/api/client";
import type { HospitalItem, PharmacyItem, EmergencyContactItem } from "@/types";

type Tab = "hospitals" | "pharmacies" | "contacts";

export default function Emergency() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("hospitals");
  const [hospitals, setHospitals] = useState<HospitalItem[]>([]);
  const [pharmacies, setPharmacies] = useState<PharmacyItem[]>([]);
  const [contacts, setContacts] = useState<EmergencyContactItem[]>([]);
  const [locating, setLocating] = useState(false);
  const [located, setLocated] = useState(false);
  const [loadingNearby, setLoadingNearby] = useState(false);
  const [locationMessage, setLocationMessage] = useState<string | null>(null);
  const [sosLoading, setSosLoading] = useState(false);
  const [sosMessage, setSosMessage] = useState<string | null>(null);
  const [newContact, setNewContact] = useState({ name: "", phone: "", relationship: "" });
  const [lat, setLat] = useState(41.3111);
  const [lon, setLon] = useState(69.2797);

  useEffect(() => {
    emergencyApi.listContacts().then(setContacts).catch(() => {});
    loadNearby(41.3111, 69.2797);
  }, []);

  function locate() {
    if (!navigator.geolocation) {
      setLocationMessage(t("emergency.location_error"));
      loadNearby(lat, lon);
      return;
    }

    setLocating(true);
    setLocationMessage(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude);
        setLon(pos.coords.longitude);
        setLocating(false);
        setLocated(true);
        setLocationMessage(null);
        loadNearby(pos.coords.latitude, pos.coords.longitude);
      },
      () => {
        setLocating(false);
        setLocationMessage(t("emergency.location_error"));
        loadNearby(lat, lon);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }

  async function loadNearby(la: number, lo: number) {
    setLoadingNearby(true);
    try {
      const [nearbyHospitals, nearbyPharmacies] = await Promise.all([
        emergencyApi.findHospitals(la, lo, 50),
        emergencyApi.findPharmacies(la, lo, 20),
      ]);

      const [resolvedHospitals, resolvedPharmacies] = await Promise.all([
        nearbyHospitals.length > 0 ? Promise.resolve(nearbyHospitals) : emergencyApi.findHospitals(la, lo, 500),
        nearbyPharmacies.length > 0 ? Promise.resolve(nearbyPharmacies) : emergencyApi.findPharmacies(la, lo, 500),
      ]);

      setHospitals(resolvedHospitals);
      setPharmacies(resolvedPharmacies);
    } catch {
      setLocationMessage(t("emergency.location_error"));
    } finally {
      setLoadingNearby(false);
    }
  }

  async function handleAddContact() {
    if (!newContact.name || !newContact.phone) return;
    await emergencyApi.addContact(newContact);
    setNewContact({ name: "", phone: "", relationship: "" });
    emergencyApi.listContacts().then(setContacts);
  }

  async function handleSOS() {
    setSosLoading(true);
    setSosMessage(null);
    try {
      await emergencyApi.triggerSos(lat, lon, "SOS — need immediate help");
      setSosMessage(t("emergency.sos_success"));
    } catch (err: any) {
      setSosMessage(extractErrorMessage(err) || t("emergency.sos_needs_contact"));
    } finally {
      setSosLoading(false);
    }
  }

  const TABS: { key: Tab; label: string; icon: typeof Building2 }[] = [
    { key: "hospitals",  label: t("emergency.find_hospitals"),  icon: Building2 },
    { key: "pharmacies", label: t("emergency.find_pharmacies"), icon: Pill       },
    { key: "contacts",   label: t("emergency.emergency_contacts"), icon: Phone   },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{t("emergency.title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("emergency.subtitle")}</p>
      </div>

      {/* SOS button */}
      <motion.button
        whileTap={{ scale: 0.96 }}
        onClick={handleSOS}
        disabled={sosLoading}
        className="w-full rounded-2xl bg-red-600 py-4 font-display text-lg font-extrabold text-white shadow-lg shadow-red-600/30 hover:bg-red-700 transition-colors disabled:opacity-60"
      >
        {sosLoading ? <Loader2 className="inline animate-spin" size={20} /> : <AlertTriangle className="inline" size={20} />}
        {" "}{t("emergency.sos_btn")}
      </motion.button>
      {sosMessage && (
        <p className={`text-sm ${sosMessage.includes(t("emergency.sos_success").slice(0, 10)) ? "text-emerald-600" : "text-red-600"}`}>
          {sosMessage}
        </p>
      )}

      {/* Locate button */}
      <div className="card space-y-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <input
            className="input-field"
            type="number"
            step="0.000001"
            value={lat}
            onChange={(e) => setLat(Number(e.target.value))}
            aria-label="Latitude"
          />
          <input
            className="input-field"
            type="number"
            step="0.000001"
            value={lon}
            onChange={(e) => setLon(Number(e.target.value))}
            aria-label="Longitude"
          />
          <button onClick={() => loadNearby(lat, lon)} disabled={loadingNearby} className="btn-secondary">
            {loadingNearby ? <Loader2 size={16} className="animate-spin" /> : <MapPin size={16} />}
            {t("emergency.find_hospitals")}
          </button>
        </div>
        <button onClick={locate} disabled={locating} className="btn-primary w-full">
          {locating ? <Loader2 size={16} className="animate-spin" /> : <MapPin size={16} />}
          {locating ? t("emergency.locating") : t("emergency.use_my_location")}
        </button>
        {locationMessage && <p className="text-sm text-amber-600 dark:text-amber-400">{locationMessage}</p>}
        {located && (
          <p className="text-xs text-slate-500">
            {t("emergency.current_coordinates")} {lat.toFixed(5)}, {lon.toFixed(5)}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800">
        {TABS.map((tab_) => (
          <button
            key={tab_.key}
            onClick={() => setTab(tab_.key)}
            className={
              tab === tab_.key
                ? "flex shrink-0 items-center gap-1.5 border-b-2 border-brand-600 px-4 py-2.5 text-sm font-semibold text-brand-600"
                : "flex shrink-0 items-center gap-1.5 border-b-2 border-transparent px-4 py-2.5 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }
          >
            <tab_.icon size={15} />{tab_.label}
          </button>
        ))}
      </div>

      {/* Hospitals */}
      {tab === "hospitals" && (
        <div className="space-y-3">
          {hospitals.length === 0 ? (
            <p className="text-sm text-slate-400">{t("emergency.no_hospitals")}</p>
          ) : hospitals.map((h) => (
            <div key={h.id} className="card flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600 dark:bg-red-900/30">
                <Building2 size={18} />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200">{h.name}</h3>
                  {h.has_emergency_room && (
                    <span className="badge badge-emergency">{t("emergency.emergency_room")}</span>
                  )}
                </div>
                <p className="text-xs text-slate-500">{h.address}</p>
                {h.specialties && <p className="mt-1 text-xs text-slate-400">{h.specialties}</p>}
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                  {h.phone && <span><span className="font-medium">{t("emergency.phone")}</span> {h.phone}</span>}
                  {h.distance_km != null && <span className="font-semibold text-brand-600">{h.distance_km} {t("emergency.km")}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pharmacies */}
      {tab === "pharmacies" && (
        <div className="space-y-3">
          {pharmacies.length === 0 ? (
            <p className="text-sm text-slate-400">{t("emergency.no_pharmacies")}</p>
          ) : pharmacies.map((p) => (
            <div key={p.id} className="card flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30">
                <Pill size={18} />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200">{p.name}</h3>
                  {p.is_24h && <span className="badge badge-low">{t("emergency.open_24h")}</span>}
                </div>
                <p className="text-xs text-slate-500">{p.address}</p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                  {p.phone && <span><span className="font-medium">{t("emergency.phone")}</span> {p.phone}</span>}
                  {p.distance_km != null && <span className="font-semibold text-brand-600">{p.distance_km} {t("emergency.km")}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Emergency contacts */}
      {tab === "contacts" && (
        <div className="space-y-4">
          <div className="card grid grid-cols-1 gap-2 sm:grid-cols-4">
            <input className="input-field" placeholder={t("emergency.contact_name")} value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} />
            <input className="input-field" placeholder={t("emergency.contact_phone")} value={newContact.phone} onChange={(e) => setNewContact({ ...newContact, phone: e.target.value })} />
            <input className="input-field" placeholder={t("emergency.contact_relationship")} value={newContact.relationship} onChange={(e) => setNewContact({ ...newContact, relationship: e.target.value })} />
            <button onClick={handleAddContact} className="btn-primary">
              <Plus size={14} />{t("emergency.add_contact")}
            </button>
          </div>
          {contacts.length === 0 ? (
            <p className="text-sm text-slate-400">{t("emergency.no_contacts")}</p>
          ) : contacts.map((c) => (
            <div key={c.id} className="card flex items-center justify-between">
              <div>
                <p className="font-semibold text-slate-800 dark:text-slate-200">{c.name}</p>
                <p className="text-xs text-slate-500">{c.relationship} · {c.phone}</p>
              </div>
              <button onClick={() => emergencyApi.deleteContact(c.id).then(() => emergencyApi.listContacts().then(setContacts))} className="text-red-400 hover:text-red-600">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
