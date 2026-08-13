import { useState, useEffect, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  Sparkles,
  X,
  Send,
  Paperclip,
  RotateCcw,
  AlertCircle,
  Loader2,
  ExternalLink,
  Bot,
  MapPin,
  FileText,
  ShieldAlert,
  Hospital as HospitalIcon,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessage, sendChatImage, fetchCurradoHospitals } from "@/api/chat";
import { ChatMessage, Hospital } from "@/api/types";
import { APIError } from "@/api/client";
import { loadRecommendationResult } from "@/lib/analysis-store";

export function CurradoAgent() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [showGreeting, setShowGreeting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // User Geolocation State
  const [userLat, setUserLat] = useState<number | null>(() => {
    if (typeof window === "undefined" || typeof sessionStorage === "undefined") return null;
    try {
      const lat = sessionStorage.getItem("currado_lat");
      return lat ? parseFloat(lat) : null;
    } catch {
      return null;
    }
  });
  const [userLng, setUserLng] = useState<number | null>(() => {
    if (typeof window === "undefined" || typeof sessionStorage === "undefined") return null;
    try {
      const lng = sessionStorage.getItem("currado_lng");
      return lng ? parseFloat(lng) : null;
    } catch {
      return null;
    }
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check first-time session greeting
  useEffect(() => {
    if (typeof window === "undefined" || typeof sessionStorage === "undefined") return undefined;
    try {
      const dismissed = sessionStorage.getItem("currado_greeting_dismissed");
      if (!dismissed) {
        const timer = setTimeout(() => setShowGreeting(true), 1200);
        return () => clearTimeout(timer);
      }
    } catch {
      // Ignore storage restrictions
    }
    return undefined;
  }, []);

  // Request browser location automatically if not present
  const requestLocation = (): Promise<{ lat: number; lng: number } | null> => {
    return new Promise((resolve) => {
      if (typeof window === "undefined" || typeof navigator === "undefined" || !navigator.geolocation) {
        resolve(null);
        return;
      }
      setIsLocating(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          setUserLat(lat);
          setUserLng(lng);
          if (typeof sessionStorage !== "undefined") {
            try {
              sessionStorage.setItem("currado_lat", lat.toString());
              sessionStorage.setItem("currado_lng", lng.toString());
            } catch {
              // Ignore storage restrictions
            }
          }
          setIsLocating(false);
          resolve({ lat, lng });
        },
        () => {
          setIsLocating(false);
          resolve(null);
        },
        { timeout: 8000, enableHighAccuracy: true }
      );
    });
  };

  // Initial welcome message when panel opens if empty
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: "welcome-1",
          sender: "currado",
          text: "Namaste! I'm ✦ CURRADO, your Charak AI Healthcare Navigation Assistant. Tell me your symptoms, upload a prescription/report (PDF or Image), or ask for nearby hospitals.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, [isOpen, messages.length]);

  // Auto scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, isUploading, isLocating]);

  const handleDismissGreeting = () => {
    setShowGreeting(false);
    if (typeof sessionStorage !== "undefined") {
      try {
        sessionStorage.setItem("currado_greeting_dismissed", "true");
      } catch {
        // Ignore storage restrictions
      }
    }
  };

  const handleStartChatFromGreeting = () => {
    handleDismissGreeting();
    setIsOpen(true);
  };

  const handleSendMessage = async () => {
    const trimmed = inputMessage.trim();
    if (!trimmed || isLoading || isUploading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const activeResult = typeof window !== "undefined" ? loadRecommendationResult() : null;
      const contextPayload: Record<string, any> = {
        ...(activeResult
          ? {
              primary_specialty: activeResult.primary_specialty,
              urgency_category: activeResult.urgency_category,
              urgency_summary: activeResult.urgency_summary,
              clinical_summary: activeResult.clinical_summary,
              red_flags: activeResult.red_flags,
            }
          : {}),
        latitude: userLat,
        longitude: userLng,
      };

      const response = await sendChatMessage({
        message: trimmed,
        conversation_id: conversationId ?? undefined,
        context: contextPayload,
      });

      setConversationId(response.conversation_id);

      const botMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: "currado",
        text: response.response,
        urgency: response.urgency,
        specialties: response.specialties,
        red_flags: response.red_flags,
        suggested_action: response.suggested_action ?? undefined,
        analysis_id: response.analysis_id,
        intent_type: response.intent_type,
        hospitals: response.hospitals ?? undefined,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      let errText = "Currado can't reach the healthcare service right now. Please check backend connection.";
      if (err instanceof APIError) {
        if (err.code === "REQUEST_TIMEOUT") {
          errText = "Currado is taking too long to respond. Please try again.";
        } else if (err.message) {
          errText = err.message;
        }
      }
      setErrorMessage(errText);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
    if (!allowedTypes.includes(file.type)) {
      setErrorMessage("Please upload a valid image (JPEG, PNG, WEBP) or PDF file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("File size must be under 10MB limit.");
      return;
    }

    const isPdf = file.type === "application/pdf";
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text: `📎 [Uploaded ${isPdf ? "Medical PDF" : "Medical Image"}]: ${file.name}`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setErrorMessage(null);
    setIsUploading(true);

    const formData = new FormData();
    formData.append("image", file);
    if (inputMessage.trim()) {
      formData.append("message", inputMessage.trim());
      setInputMessage("");
    }
    if (conversationId) {
      formData.append("conversation_id", conversationId);
    }

    try {
      const response = await sendChatImage(formData);
      setConversationId(response.conversation_id);

      const botMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: "currado",
        text: response.response,
        urgency: response.urgency,
        specialties: response.specialties,
        red_flags: response.red_flags,
        suggested_action: response.suggested_action ?? undefined,
        intent_type: response.intent_type,
        prescription_extraction: response.prescription_extraction,
        document_type: response.document_type,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      let errText = "Failed to process document. Please try again.";
      if (err instanceof APIError && err.code === "REQUEST_TIMEOUT") {
        errText = "Document processing timed out. Please try again.";
      } else if (err instanceof APIError && err.message) {
        errText = err.message;
      }
      setErrorMessage(errText);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleExecuteAction = async (action: any) => {
    if (!action) return;

    const specialty = action.specialty || action.payload?.specialty || "General Medicine";
    const isEmergency = action.emergency_required || action.type === "FIND_EMERGENCY_HOSPITALS" || action.type === "EMERGENCY_ALERT";

    // Request GPS if missing
    let lat = userLat;
    let lng = userLng;
    if (lat === null || lng === null) {
      const coords = await requestLocation();
      if (coords) {
        lat = coords.lat;
        lng = coords.lng;
      }
    }

    if (action.route && !action.payload) {
      navigate({ to: action.route as any });
      return;
    }

    setIsLoading(true);
    try {
      const hospitalResults = await fetchCurradoHospitals({
        lat,
        lng,
        specialty,
        emergency_required: isEmergency,
      });

      const textReply = hospitalResults && hospitalResults.length > 0
        ? `Found ${hospitalResults.length} nearby ${isEmergency ? "emergency-capable" : specialty} facilities based on your location.`
        : `No verified ${specialty} facilities found within the immediate radius.`;

      const botMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: "currado",
        text: textReply,
        urgency: isEmergency ? "EMERGENCY" : "ROUTINE",
        specialties: [specialty],
        hospitals: hospitalResults,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      // Fallback navigation with parameters
      const params = new URLSearchParams();
      if (specialty) params.set("specialty", specialty);
      if (isEmergency) params.set("emergency", "true");
      navigate({ to: `/hospitals?${params.toString()}` as any });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearConversation = () => {
    setMessages([
      {
        id: `msg-${Date.now()}`,
        sender: "currado",
        text: "Conversation cleared. How can I assist your healthcare navigation now?",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setConversationId(undefined);
    setErrorMessage(null);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Auto-popup greeting card */}
      {showGreeting && !isOpen && (
        <div className="mb-3 max-w-sm rounded-2xl border border-teal/20 bg-card p-4 shadow-2xl backdrop-blur animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-teal/10 text-teal">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <h4 className="text-sm font-bold text-foreground">Hi, I'm Currado 👋</h4>
                <p className="text-xs text-muted-foreground">Charak Healthcare Assistant</p>
              </div>
            </div>
            <button
              onClick={handleDismissGreeting}
              className="rounded-full p-1 text-muted-foreground hover:bg-muted"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2.5 text-xs text-muted-foreground leading-relaxed">
            I can analyze symptoms, extract prescriptions/reports, find emergency care, and recommend nearby hospitals.
          </p>
          <div className="mt-3 flex items-center justify-end gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs rounded-full"
              onClick={handleDismissGreeting}
            >
              Not now
            </Button>
            <Button
              size="sm"
              className="h-7 text-xs rounded-full bg-teal text-white hover:bg-teal/90"
              onClick={handleStartChatFromGreeting}
            >
              Start chat
            </Button>
          </div>
        </div>
      )}

      {/* Floating Currado Toggle Button */}
      {!isOpen && (
        <button
          id="currado-toggle-btn"
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-2.5 rounded-full bg-gradient-to-r from-navy via-slate-900 to-teal px-5 py-3 text-white shadow-xl transition-all duration-300 hover:scale-105 hover:shadow-teal/20"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 text-teal-200 group-hover:rotate-12 transition-transform">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="text-sm font-bold tracking-wide">✦ CURRADO</span>
        </button>
      )}

      {/* Main Currado Chat Window */}
      {isOpen && (
        <div className="flex h-[600px] w-[360px] sm:w-[440px] flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border bg-navy px-4 py-3 text-white">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-teal text-white font-bold">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold leading-none flex items-center gap-1.5">
                  CURRADO <Sparkles className="h-3.5 w-3.5 text-teal" />
                </h3>
                <span className="text-[11px] text-teal-200 flex items-center gap-1">
                  Healthcare navigation agent
                  {userLat && <span className="text-[10px] text-emerald-400 font-semibold">• GPS Active</span>}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {!userLat && (
                <button
                  onClick={() => requestLocation()}
                  disabled={isLocating}
                  title="Enable Location for Nearby Hospital Discovery"
                  className="rounded-full p-1.5 text-teal-200 hover:bg-white/10 hover:text-white"
                >
                  <MapPin className={`h-4 w-4 ${isLocating ? "animate-bounce" : ""}`} />
                </button>
              )}
              <button
                onClick={handleClearConversation}
                title="Clear conversation"
                className="rounded-full p-1.5 text-slate-300 hover:bg-white/10 hover:text-white"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close assistant"
                className="rounded-full p-1.5 text-slate-300 hover:bg-white/10 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-background/50">
            {messages.map((m) => {
              const isEmergency = m.urgency === "EMERGENCY" || (m.red_flags && m.red_flags.length > 0);

              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${
                    m.sender === "user" ? "items-end" : "items-start"
                  }`}
                >
                  {/* Emergency Warning Banner above message if emergency */}
                  {m.sender === "currado" && isEmergency && (
                    <div className="mb-2 w-full rounded-xl border border-red-500/40 bg-red-950/80 p-3 text-red-100 shadow-md">
                      <div className="flex items-center gap-2 font-bold text-xs text-red-400 mb-1">
                        <ShieldAlert className="h-4 w-4 text-red-400 shrink-0" />
                        <span>⚠ CRITICAL MEDICAL ALERT</span>
                      </div>
                      <p className="text-[11px] leading-relaxed text-red-200">
                        Immediate emergency care is required. Call 102/108 or proceed to the nearest Emergency Department.
                      </p>
                    </div>
                  )}

                  <div
                    className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                      m.sender === "user"
                        ? "bg-teal text-white rounded-br-none shadow-sm"
                        : isEmergency
                        ? "bg-red-950/40 border border-red-500/30 text-foreground rounded-bl-none shadow-sm"
                        : "bg-muted text-foreground border border-border rounded-bl-none shadow-sm"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.text}</p>

                    {/* Prescription / Document Extraction View */}
                    {m.prescription_extraction && (
                      <div className="mt-3 rounded-xl border border-teal/30 bg-card/90 p-3 space-y-2 text-foreground">
                        <div className="flex items-center justify-between border-b border-border pb-1.5">
                          <span className="flex items-center gap-1.5 text-[11px] font-bold text-teal">
                            <FileText className="h-3.5 w-3.5" />
                            {m.prescription_extraction.document_type || "DOCUMENT EXTRACTION"}
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            {m.prescription_extraction.extraction_method || "Vision AI"}
                          </span>
                        </div>

                        {m.prescription_extraction.doctor_name && (
                          <div className="text-[11px]">
                            <span className="text-muted-foreground font-medium">Doctor:</span> {m.prescription_extraction.doctor_name}
                          </div>
                        )}

                        {m.prescription_extraction.medications.length > 0 && (
                          <div className="space-y-1 pt-1">
                            <span className="text-[11px] font-bold text-foreground">Extracted Medications:</span>
                            <div className="space-y-1">
                              {m.prescription_extraction.medications.map((med, idx) => (
                                <div key={idx} className="rounded bg-muted/60 p-1.5 text-[10px] border border-border/40">
                                  <div className="flex items-center justify-between">
                                    <span className="font-semibold text-foreground">{med.name || "Unreadable Medication"}</span>
                                    {med.confidence === "LOW" ? (
                                      <span className="text-[9px] text-amber-500 flex items-center gap-0.5">
                                        <AlertTriangle className="h-2.5 w-2.5" /> Unclear
                                      </span>
                                    ) : (
                                      <span className="text-[9px] text-emerald-500 flex items-center gap-0.5">
                                        <CheckCircle2 className="h-2.5 w-2.5" /> Verified
                                      </span>
                                    )}
                                  </div>
                                  {(med.dosage || med.frequency || med.duration) && (
                                    <p className="text-muted-foreground mt-0.5">
                                      {[med.dosage, med.frequency, med.duration].filter(Boolean).join(" • ")}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Inline Hospital Mini Cards */}
                    {m.hospitals && m.hospitals.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <div className="text-[11px] font-bold text-teal flex items-center gap-1">
                          <HospitalIcon className="h-3.5 w-3.5" />
                          <span>Matched Facilities ({m.hospitals.length}):</span>
                        </div>
                        {m.hospitals.slice(0, 3).map((h) => (
                          <div
                            key={h.id}
                            onClick={() => navigate({ to: `/hospital/$id`, params: { id: h.id } })}
                            className="group cursor-pointer rounded-xl border border-border bg-card p-2.5 text-left transition-all hover:border-teal hover:shadow-md"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <h5 className="font-bold text-[11px] text-foreground group-hover:text-teal">
                                  {h.name}
                                </h5>
                                <p className="text-[10px] text-muted-foreground line-clamp-1">{h.address}</p>
                              </div>
                              <span className="shrink-0 text-[10px] font-bold text-teal bg-teal/10 px-2 py-0.5 rounded-full">
                                {h.distance_km ? `${h.distance_km.toFixed(1)} km` : "Nearby"}
                              </span>
                            </div>
                            <div className="mt-1.5 flex items-center justify-between text-[9px] text-muted-foreground">
                              <span>{h.emergency_ready ? "🚨 Emergency Ready" : "General Medical"}</span>
                              <span className="font-semibold text-teal flex items-center gap-0.5">
                                View details <ExternalLink className="h-2.5 w-2.5" />
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Red flags list */}
                    {m.red_flags && m.red_flags.length > 0 && (
                      <div className="mt-2 rounded-lg bg-danger/10 border border-danger/30 p-2 text-danger text-[11px]">
                        <span className="font-semibold">⚠️ Alert Signals:</span> {m.red_flags.join(", ")}
                      </div>
                    )}

                    {/* Action Button */}
                    {m.suggested_action && (
                      <button
                        onClick={() => handleExecuteAction(m.suggested_action)}
                        className={`mt-2.5 flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[11px] font-bold shadow-sm transition-all ${
                          isEmergency
                            ? "bg-red-600 text-white hover:bg-red-700 animate-pulse"
                            : "bg-teal text-white hover:bg-teal/90"
                        }`}
                      >
                        <span>{m.suggested_action.label}</span>
                        <ExternalLink className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                  <span className="mt-1 text-[10px] text-muted-foreground px-1">
                    {m.timestamp}
                  </span>
                </div>
              );
            })}

            {/* Location Access Prompt Button if GPS requested */}
            {userLat === null && (
              <div className="rounded-xl border border-teal/30 bg-teal/5 p-3 text-center text-xs text-foreground space-y-2">
                <p className="text-[11px] text-muted-foreground">
                  📍 Enable location access for exact Haversine distance and accurate nearby hospital discovery.
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => requestLocation()}
                  disabled={isLocating}
                  className="h-7 text-xs rounded-full border-teal text-teal hover:bg-teal hover:text-white"
                >
                  {isLocating ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <MapPin className="h-3 w-3 mr-1" />}
                  {isLocating ? "Detecting location..." : "Allow Location Access"}
                </Button>
              </div>
            )}

            {/* Typing Indicator */}
            {(isLoading || isUploading || isLocating) && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 w-fit rounded-full px-3 py-1.5 border border-border">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-teal" />
                <span>
                  {isUploading
                    ? "Extracting document..."
                    : isLocating
                    ? "Acquiring GPS location..."
                    : "Analyzing symptoms..."}
                </span>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="flex items-start gap-2 rounded-xl bg-danger/10 border border-danger/20 p-3 text-xs text-danger">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p>{errorMessage}</p>
                  <button
                    onClick={() => {
                      setErrorMessage(null);
                      if (inputMessage) handleSendMessage();
                    }}
                    className="mt-1 font-semibold underline hover:text-danger/80"
                  >
                    Try again
                  </button>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input Area */}
          <div className="border-t border-border p-3 bg-card">
            <div className="flex items-center gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept="image/jpeg,image/png,image/webp,application/pdf"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading || isUploading}
                title="Upload prescription or medical report (JPEG, PNG, WEBP, PDF up to 10MB)"
                className="rounded-full p-2 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
              >
                <Paperclip className="h-4 w-4" />
              </button>

              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Type symptoms (e.g. ftigue, chest pain)..."
                disabled={isLoading || isUploading}
                className="h-9 text-xs rounded-full bg-background border-border"
              />

              <Button
                type="button"
                size="sm"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading || isUploading}
                className="h-9 w-9 rounded-full bg-teal text-white hover:bg-teal/90 p-0 shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-2 text-[10px] text-center text-muted-foreground">
              Currado provides navigation assistance only. Not medical diagnosis.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
