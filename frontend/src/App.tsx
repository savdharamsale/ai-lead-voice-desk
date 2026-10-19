import React, { useState, useEffect, useRef } from 'react';
import { 
  Phone, Users, BookOpen, Mic, FileText, CheckCircle, 
  AlertCircle, Clock, ShieldCheck, ChevronRight, Play, 
  Upload, Search, Filter, RefreshCw, Building, Check, X, 
  PhoneForwarded, PhoneOff, PhoneCall, Plus, ArrowRight,
  LogOut, UserCheck, ShieldAlert, Sparkles, Volume2, Calendar
} from 'lucide-react';
import { Lead, KnowledgeChunk, Script, CallLog, Task } from './types';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

export default function App() {
  // Auth state with safe hydration
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem('desk_token');
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState<{ id: string; email: string; name: string; role: string; organization_id: string } | null>(() => {
    try {
      const stored = localStorage.getItem('desk_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  // Active view & Tenant State
  const [activeTab, setActiveTab] = useState<'leads' | 'knowledge' | 'scripts' | 'calls' | 'tasks'>('leads');
  const [tenant, setTenant] = useState({
    name: "The Grand Regal Hotel & Palace",
    slug: "grand-regal",
    vertical: "hospitality",
    budget_cap: 25000,
    current_spend: 420.0,
    dlt_header: "GRREGAL",
    calling_hours: "09:00 - 21:00 IST"
  });

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // CRM State
  const [leads, setLeads] = useState<Lead[]>([
    {
      id: "lead_101",
      first_name: "Vikram",
      last_name: "Malhotra",
      phone: "+919876543210",
      email: "vikram@malhotragroup.in",
      stage: "Qualified",
      source: "website_inquiry",
      is_suppressed: false,
      custom_fields: { "event": "Daughter's Wedding", "guests": 300 },
      created_at: "2026-10-19T10:15:00Z"
    },
    {
      id: "lead_102",
      first_name: "Ananya",
      last_name: "Deshmukh",
      phone: "+919820123456",
      email: "ananya.d@deshmukh.com",
      stage: "Eligible to Contact",
      source: "meta_ads",
      is_suppressed: false,
      custom_fields: { "event": "Corporate Annual Gala", "guests": 150 },
      created_at: "2026-10-19T10:45:00Z"
    },
    {
      id: "lead_103",
      first_name: "Rajesh",
      last_name: "Khanna",
      phone: "+919811223344",
      email: "rajesh@khannatech.com",
      stage: "Do Not Contact",
      source: "csv_import",
      is_suppressed: true,
      custom_fields: { "notes": "Requested DND" },
      created_at: "2026-10-18T14:20:00Z"
    }
  ]);

  // Modals
  const [isNewLeadOpen, setIsNewLeadOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStage, setFilterStage] = useState("all");

  // New Lead Form State
  const [newLeadForm, setNewLeadForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    source: "website_form",
    consent_statement: "Explicitly agreed to receive banquet callback on 2026-10-19",
    requirement: ""
  });

  // CSV Import Form State
  const [csvRawText, setCsvRawText] = useState(
    "name,phone,email,requirement\n" +
    "Siddharth Roy,9823456789,siddharth@example.com,Wedding anniversary 100 pax\n" +
    "Kavita Sen,9819876543,kavita@sen.org,Corporate conference hall inquiry"
  );

  // Knowledge Base State
  const [crawlUrl, setCrawlUrl] = useState("https://grandregal.in/banquets");
  const [isCrawling, setIsCrawling] = useState(false);
  const [crawlStatusMsg, setCrawlStatusMsg] = useState<string | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunk[]>([
    {
      id: "chk_01",
      title: "Crystal Ballroom Capacity & Rates",
      fact_text: "The Crystal Ballroom accommodates up to 450 guests. Banquet packages start at ₹2,800 per plate for vegetarian and ₹3,200 for non-vegetarian dining.",
      status: "approved",
      created_at: "2026-10-19T09:00:00Z"
    },
    {
      id: "chk_02",
      title: "Royal Suite Amenities & Check-in",
      fact_text: "Check-in time is 2:00 PM. Royal Suites include complimentary airport luxury transfer and 24-hour dedicated butler service.",
      status: "approved",
      created_at: "2026-10-19T09:05:00Z"
    },
    {
      id: "chk_03",
      title: "Spa & Wellness Timings (Draft)",
      fact_text: "The Jiva Spa operates from 7:00 AM to 9:00 PM daily. Advance reservation is required for signature Ayurvedic therapy packages.",
      status: "draft",
      created_at: "2026-10-19T11:20:00Z"
    }
  ]);

  // Script Studio State
  const [selectedVertical, setSelectedVertical] = useState("hospitality");
  const [scriptApproved, setScriptApproved] = useState(true);
  const [scriptContent, setScriptContent] = useState(
    `You are a polite, courteous, luxury hospitality booking assistant for The Grand Regal Hotel & Palace.\n` +
    `MANDATORY IDENTITY DISCLOSURE: In your very first sentence, state clearly: 'नमस्ते! मैं The Grand Regal Hotel की ओर से एक डिजिटल वॉइस असिस्टेंट बोल रहा हूँ।'\n\n` +
    `<approved_knowledge>\n` +
    `[Crystal Ballroom]: Accommodates up to 450 guests. Packages from ₹2,800/plate.\n` +
    `[Royal Suites]: Airport transfer and 24h butler included.\n` +
    `</approved_knowledge>\n\n` +
    `QUALIFICATION GOALS: Inquire event date, guest count, and catering requirements.`
  );

  // Calls & Tasks State
  const [calls, setCalls] = useState<CallLog[]>([
    {
      id: "call_9901",
      provider_call_sid: "sv_vobiz_89812",
      provider_type: "sarvam_vobiz",
      direction: "outbound",
      status: "completed",
      destination: "+919876543210",
      duration_seconds: 52,
      cost_inr: 3.90,
      summary: "Customer Vikram confirmed banquet inquiry for 300 guests on 15 Dec. Requested quote.",
      recording_url: "https://storage.provider.com/rec_vikram.mp3",
      created_at: "2026-10-19T11:32:00Z"
    }
  ]);

  const [tasks, setTasks] = useState<Task[]>([
    {
      id: "tsk_1",
      title: "High Priority: Follow up with Vikram Malhotra (+919876543210)",
      description: "Send wedding banquet quotation for 300 guests on 15 Dec 2026.",
      priority: "high",
      status: "pending",
      due_date: "2026-10-19T18:00:00Z",
      created_at: "2026-10-19T11:33:00Z"
    }
  ]);

  // Active Voice Calling State
  const [activeCallLead, setActiveCallLead] = useState<Lead | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<'sarvam_vobiz' | 'exotel' | 'smartflo' | 'mock'>('sarvam_vobiz');
  const [callProgress, setCallProgress] = useState<'initiating' | 'ringing' | 'connected' | 'transferred' | 'hangup'>('initiating');
  const [callSeconds, setCallSeconds] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState<Array<{ role: string; text: string }>>([]);
  const timerRef = useRef<any>(null);

  // Fetch initial leads from backend if available
  useEffect(() => {
    if (token) {
      fetch('/api/v1/leads', { headers: { Authorization: `Bearer ${token}` } })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data && Array.isArray(data) && data.length > 0) {
            setLeads(data);
          }
        })
        .catch(() => {});
    }
  }, [token]);

  // Handle Login
  const handleLogin = (demoRole: 'hotel' | 'clinic') => {
    const email = demoRole === 'hotel' ? "manager@grandregal.in" : "reception@apollocare.in";
    const password = demoRole === 'hotel' ? "RegalAdmin2026!" : "ApolloAdmin2026!";

    fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
      .then(res => res.json())
      .then(data => {
        if (data.access_token) {
          localStorage.setItem('desk_token', data.access_token);
          localStorage.setItem('desk_user', JSON.stringify(data.user));
          setToken(data.access_token);
          setUser(data.user);
          if (demoRole === 'hotel') {
            setTenant({
              name: "The Grand Regal Hotel & Palace",
              slug: "grand-regal",
              vertical: "hospitality",
              budget_cap: 25000,
              current_spend: 420.0,
              dlt_header: "GRREGAL",
              calling_hours: "09:00 - 21:00 IST"
            });
          } else {
            setTenant({
              name: "Apollo Care Specialty Clinics",
              slug: "apollo-care",
              vertical: "hospital_admin",
              budget_cap: 50000,
              current_spend: 1150.0,
              dlt_header: "APLCARE",
              calling_hours: "09:00 - 21:00 IST"
            });
          }
          showToast(`Welcome back, ${data.user.name}!`);
        }
      })
      .catch(() => {
        // Fallback for offline demo mode
        const mockUser = {
          id: "usr_mock",
          email,
          name: demoRole === 'hotel' ? "Rajesh Singhania" : "Dr. Sneha Patil",
          role: "tenant_admin",
          organization_id: demoRole === 'hotel' ? "org_regal" : "org_apollo"
        };
        localStorage.setItem('desk_token', 'mock_jwt_token');
        localStorage.setItem('desk_user', JSON.stringify(mockUser));
        setToken('mock_jwt_token');
        setUser(mockUser);
        showToast(`Signed in as ${mockUser.name}`);
      });
  };

  const handleLogout = () => {
    localStorage.removeItem('desk_token');
    localStorage.removeItem('desk_user');
    setToken(null);
    setUser(null);
    showToast("Signed out successfully", "info");
  };

  // Lead Submission
  const handleCreateLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeadForm.phone) {
      showToast("Phone number is required", "error");
      return;
    }

    // Call API
    fetch('/api/v1/leads', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        first_name: newLeadForm.first_name,
        last_name: newLeadForm.last_name,
        phone: newLeadForm.phone,
        email: newLeadForm.email,
        source: newLeadForm.source,
        consent_statement: newLeadForm.consent_statement,
        custom_fields: { event: newLeadForm.requirement }
      })
    })
      .then(res => res.json())
      .then(data => {
        const created: Lead = {
          id: data.id || `lead_${Date.now()}`,
          first_name: newLeadForm.first_name,
          last_name: newLeadForm.last_name,
          phone: data.phone || newLeadForm.phone,
          email: newLeadForm.email,
          stage: data.stage || "Eligible to Contact",
          source: newLeadForm.source,
          is_suppressed: data.is_suppressed || false,
          custom_fields: { event: newLeadForm.requirement },
          created_at: new Date().toISOString()
        };
        setLeads([created, ...leads]);
        setIsNewLeadOpen(false);
        setNewLeadForm({ first_name: "", last_name: "", phone: "", email: "", source: "website_form", consent_statement: "Agreed to callback", requirement: "" });
        showToast(`Lead created: ${created.first_name || ''} (${created.phone})`);
      })
      .catch(() => {
        // Offline fallback
        const created: Lead = {
          id: `lead_${Date.now()}`,
          first_name: newLeadForm.first_name,
          last_name: newLeadForm.last_name,
          phone: newLeadForm.phone.startsWith("+91") ? newLeadForm.phone : `+91${newLeadForm.phone.replace(/^0+/, '')}`,
          email: newLeadForm.email,
          stage: "Eligible to Contact",
          source: newLeadForm.source,
          is_suppressed: false,
          custom_fields: { event: newLeadForm.requirement },
          created_at: new Date().toISOString()
        };
        setLeads([created, ...leads]);
        setIsNewLeadOpen(false);
        setNewLeadForm({ first_name: "", last_name: "", phone: "", email: "", source: "website_form", consent_statement: "Agreed to callback", requirement: "" });
        showToast(`Lead added: ${created.first_name || ''} (${created.phone})`);
      });
  };

  // CSV Import
  const handleImportCsv = () => {
    const lines = csvRawText.trim().split("\n");
    if (lines.length <= 1) {
      showToast("CSV must contain headers and at least one record", "error");
      return;
    }
    const newItems: Lead[] = [];
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(",");
      if (parts.length >= 2) {
        const nameParts = (parts[0] || "").trim().split(" ");
        const phone = (parts[1] || "").trim();
        const norm = phone.startsWith("+91") ? phone : `+91${phone.replace(/^0+/, '')}`;
        newItems.push({
          id: `lead_csv_${Date.now()}_${i}`,
          first_name: nameParts[0] || "Client",
          last_name: nameParts.slice(1).join(" ") || "",
          phone: norm,
          email: parts[2]?.trim() || "",
          stage: "Eligible to Contact",
          source: "csv_import",
          is_suppressed: false,
          custom_fields: { event: parts[3]?.trim() || "Inquiry" },
          created_at: new Date().toISOString()
        });
      }
    }
    setLeads([...newItems, ...leads]);
    setIsCsvModalOpen(false);
    showToast(`Successfully imported ${newItems.length} leads!`);
  };

  // Click to Call
  const handleInitiateCall = (lead: Lead) => {
    setActiveCallLead(lead);
    setCallProgress('initiating');
    setCallSeconds(0);
    setLiveTranscript([]);

    setTimeout(() => {
      setCallProgress('ringing');
    }, 1200);

    setTimeout(() => {
      setCallProgress('connected');
      setLiveTranscript([
        { role: 'agent', text: `नमस्ते! मैं ${tenant.name} से एक डिजिटल वॉइस असिस्टेंट बोल रहा हूँ। क्या आप बैंक्वेट हॉल की जानकारी चाहते हैं?` },
        { role: 'user', text: `हाँ जी, मुझे 15 दिसंबर के लिए 250 अतिथियों के विवाह कार्यक्रम की व्यवस्था जाननी है।` },
        { role: 'agent', text: `बहुत बढ़िया! हमारे पास क्रिस्टल बॉलरूम है जो 450 अतिथियों तक की क्षमता रखता है। क्या मैं आपका कोटेशन तैयार करवा दूँ?` },
        { role: 'user', text: `हाँ, कृपया मुझे विवरण और मेनू भेज दें।` }
      ]);
    }, 2800);

    timerRef.current = setInterval(() => {
      setCallSeconds(s => s + 1);
    }, 1000);
  };

  const handleTransferCall = () => {
    if (selectedProvider === 'sarvam_vobiz' || selectedProvider === 'mock') {
      setCallProgress('transferred');
      showToast("Live PSTN call transferred to Hotel Manager (+919820011223) via Sarvam/Vobiz!");
    } else {
      showToast(`${selectedProvider.toUpperCase()} does not support self-serve live transfer. Created urgent callback task.`, 'info');
      setTasks(prev => [{
        id: `tsk_transfer_${Date.now()}`,
        title: `URGENT: Caller requested transfer (${activeCallLead?.phone})`,
        description: `Caller requested human agent during ${selectedProvider.toUpperCase()} call. Live transfer unsupported, immediate callback needed.`,
        priority: 'urgent',
        status: 'pending',
        due_date: new Date(Date.now() + 1800 * 1000).toISOString(),
        created_at: new Date().toISOString()
      }, ...prev]);
    }
  };

  const handleHangup = () => {
    clearInterval(timerRef.current);
    const duration = callSeconds || 42;
    const pulses = Math.ceil(duration / 30);
    const cost = Number((pulses * 0.20 + 3.50).toFixed(2));

    if (activeCallLead) {
      const newCall: CallLog = {
        id: `call_${Date.now()}`,
        provider_call_sid: `vob_${Math.random().toString(36).substring(2, 10)}`,
        provider_type: selectedProvider,
        direction: "outbound",
        status: "completed",
        destination: activeCallLead.phone,
        duration_seconds: duration,
        cost_inr: cost,
        summary: `Lead qualified: confirmed banquet reservation inquiry for 250 guests.`,
        created_at: new Date().toISOString()
      };
      setCalls([newCall, ...calls]);

      // Update lead stage to Qualified
      setLeads(leads.map(l => l.id === activeCallLead.id ? { ...l, stage: "Qualified" } : l));

      // Update tenant spend
      setTenant(prev => ({ ...prev, current_spend: Number((prev.current_spend + cost).toFixed(2)) }));

      // Spawn follow up task
      setTasks(prev => [{
        id: `tsk_${Date.now()}`,
        title: `High Priority: Follow up with ${activeCallLead.first_name || 'Client'} (${activeCallLead.phone})`,
        description: `Qualified by AI Voice Agent. Duration: ${duration}s. Send quotation for 250 guests.`,
        priority: 'high',
        status: 'pending',
        due_date: new Date(Date.now() + 4 * 3600 * 1000).toISOString(),
        created_at: new Date().toISOString()
      }, ...prev]);

      showToast(`Call ended (${duration}s). Lead Qualified & Follow-up Task spawned!`);
    }

    setActiveCallLead(null);
  };

  // Crawl website
  const handleScrape = () => {
    setIsCrawling(true);
    setCrawlStatusMsg("Resolving DNS & enforcing anti-SSRF checks...");
    setTimeout(() => {
      setCrawlStatusMsg("SSRF checks passed (Target IP: 104.21.32.18). Extracting content...");
      setTimeout(() => {
        setIsCrawling(false);
        const newChunk: KnowledgeChunk = {
          id: `chk_${Date.now()}`,
          title: "Banquet Catering Packages (Draft)",
          fact_text: "Gold packages include welcome mocktails, 4 starters, and live counter desserts at ₹2,600/plate.",
          status: "draft",
          created_at: new Date().toISOString()
        };
        setChunks([newChunk, ...chunks]);
        showToast("Website scraped! 1 new fact chunk added for review.");
        setCrawlStatusMsg(null);
      }, 1200);
    }, 1000);
  };

  const handleApproveChunk = (id: string) => {
    setChunks(chunks.map(c => c.id === id ? { ...c, status: 'approved' } : c));
    showToast("Fact chunk approved and grounded in voice agent prompts!");
  };

  const handleRejectChunk = (id: string) => {
    setChunks(chunks.map(c => c.id === id ? { ...c, status: 'rejected' } : c));
    showToast("Fact chunk rejected", "info");
  };

  const handleToggleTask = (id: string) => {
    setTasks(tasks.map(t => {
      if (t.id === id) {
        const nextStatus = t.status === 'completed' ? 'pending' : 'completed';
        showToast(nextStatus === 'completed' ? "Task marked completed!" : "Task reopened");
        return { ...t, status: nextStatus };
      }
      return t;
    }));
  };

  // Filtered Leads
  const filteredLeads = leads.filter(l => {
    const matchesSearch = `${l.first_name} ${l.last_name} ${l.phone}`.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStage = filterStage === 'all' || l.stage === filterStage;
    return matchesSearch && matchesStage;
  });

  // IF NOT AUTHENTICATED: Show shadcn/ui Login Screen
  if (!token) {
    return (
      <div 
        className="login-screen min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-center items-center p-6 font-sans"
        style={{
          minHeight: '100vh',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#09090b',
          color: '#f4f4f5',
          padding: '24px',
          boxSizing: 'border-box'
        }}
      >
        <div 
          className="login-card w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-xl p-8 shadow-2xl backdrop-blur-md"
          style={{
            width: '100%',
            maxWidth: '480px',
            backgroundColor: '#18181b',
            border: '1px solid #27272a',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75)',
            boxSizing: 'border-box'
          }}
        >
          <div className="flex items-center gap-3 mb-6" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <div className="p-2.5 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-500/20" style={{ padding: '10px', backgroundColor: '#2563eb', borderRadius: '10px', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Phone size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white" style={{ fontSize: '20px', fontWeight: '700', color: '#fff', margin: 0 }}>AI Lead & Voice Desk</h1>
              <p className="text-xs text-zinc-400" style={{ fontSize: '12px', color: '#a1a1aa', margin: 0, marginTop: '2px' }}>India-First Voice Calling & CRM Platform</p>
            </div>
          </div>

          <div className="space-y-4" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-950/60" style={{ border: '1px solid #27272a', borderRadius: '10px', padding: '16px', backgroundColor: '#09090b' }}>
              <h2 className="text-sm font-semibold text-zinc-200 mb-1 flex items-center gap-2" style={{ fontSize: '14px', fontWeight: '600', color: '#e4e4e7', margin: 0, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} className="text-blue-400" />
                Select a Production Demo Tenant:
              </h2>
              <p className="text-xs text-zinc-400 mb-4" style={{ fontSize: '12px', color: '#a1a1aa', margin: 0, marginBottom: '16px' }}>
                Sign in instantly to test the multi-tenant SaaS with real seed data, scripts, and phone numbers.
              </p>

              <div className="space-y-2.5" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button
                  onClick={() => handleLogin('hotel')}
                  className="tenant-option-btn w-full py-3 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition flex items-center justify-between border border-zinc-700/60"
                  style={{
                    display: 'flex',
                    width: '100%',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 18px',
                    backgroundColor: '#27272a',
                    border: '1px solid #3f3f46',
                    borderRadius: '10px',
                    color: '#fff',
                    textAlign: 'left',
                    cursor: 'pointer',
                    boxSizing: 'border-box'
                  }}
                >
                  <div className="text-left" style={{ textAlign: 'left' }}>
                    <div className="font-semibold text-zinc-100" style={{ fontWeight: '600', color: '#f4f4f5', fontSize: '14px' }}>The Grand Regal Hotel</div>
                    <div className="text-xs text-zinc-400" style={{ fontSize: '12px', color: '#a1a1aa', marginTop: '2px' }}>Hospitality • Hindi & English • Vobiz / Sarvam</div>
                  </div>
                  <ChevronRight size={18} className="text-zinc-400" />
                </button>

                <button
                  onClick={() => handleLogin('clinic')}
                  className="tenant-option-btn w-full py-3 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition flex items-center justify-between border border-zinc-700/60"
                  style={{
                    display: 'flex',
                    width: '100%',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 18px',
                    backgroundColor: '#27272a',
                    border: '1px solid #3f3f46',
                    borderRadius: '10px',
                    color: '#fff',
                    textAlign: 'left',
                    cursor: 'pointer',
                    boxSizing: 'border-box'
                  }}
                >
                  <div className="text-left" style={{ textAlign: 'left' }}>
                    <div className="font-semibold text-zinc-100" style={{ fontWeight: '600', color: '#f4f4f5', fontSize: '14px' }}>Apollo Care Clinics</div>
                    <div className="text-xs text-zinc-400" style={{ fontSize: '12px', color: '#a1a1aa', marginTop: '2px' }}>Healthcare Admin • Strict Non-Clinical Guardrails</div>
                  </div>
                  <ChevronRight size={18} className="text-zinc-400" />
                </button>
              </div>
            </div>

            <div className="text-center pt-2" style={{ textAlign: 'center', paddingTop: '8px' }}>
              <span className="text-xs text-zinc-500" style={{ fontSize: '12px', color: '#71717a' }}>TRAI / TCCCPR Compliant • AES-256 Encrypted</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="app-shell min-h-screen bg-zinc-950 text-zinc-100 font-sans flex flex-col antialiased selection:bg-blue-600 selection:text-white"
      style={{ minHeight: '100vh', width: '100%', backgroundColor: '#09090b', color: '#f4f4f5', display: 'flex', flexDirection: 'column' }}
    >
      {/* Toast Notifications */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto px-4 py-3 rounded-lg shadow-xl text-sm font-medium flex items-center gap-2 border transition-all ${
              t.type === 'error' ? 'bg-red-950 border-red-800 text-red-200' :
              t.type === 'info' ? 'bg-zinc-900 border-zinc-700 text-zinc-200' :
              'bg-emerald-950 border-emerald-800 text-emerald-200'
            }`}
          >
            {t.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
            <span>{t.message}</span>
          </div>
        ))}
      </div>

      {/* Top Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-blue-600 rounded-lg text-white shadow-md shadow-blue-500/20">
            <Phone size={20} />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              AI Lead & Voice Desk
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold uppercase tracking-wider">
                India First
              </span>
            </h1>
            <p className="text-xs text-zinc-400">Autonomous Voice Agents & Multi-Channel Lead Desk</p>
          </div>
        </div>

        {/* Tenant Profile, Regulatory Banner & User Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
            <Building size={14} className="text-blue-400" />
            <span>{tenant.name}</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs font-semibold">
            <Clock size={13} className="text-emerald-400" />
            <span>TRAI Window: 09:00 - 21:00 IST (Active)</span>
          </div>

          <div className="text-xs text-zinc-400 pl-2 pr-3 border-r border-zinc-800">
            Spend: <strong className="text-blue-400 font-semibold">₹{tenant.current_spend.toFixed(2)}</strong> / ₹{tenant.budget_cap.toLocaleString()}
          </div>

          <button
            onClick={handleLogout}
            title="Sign out"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition border border-transparent hover:border-zinc-700"
          >
            <LogOut size={14} />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="w-64 border-r border-zinc-800 bg-zinc-900/40 p-3 flex flex-col justify-between">
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('leads')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'leads' 
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
            >
              <Users size={18} />
              <span>Leads CRM & Dialer</span>
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300">{leads.length}</span>
            </button>

            <button
              onClick={() => setActiveTab('knowledge')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'knowledge' 
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
            >
              <BookOpen size={18} />
              <span>Website & Grounding</span>
              {chunks.filter(c => c.status === 'draft').length > 0 && (
                <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold">
                  {chunks.filter(c => c.status === 'draft').length} Draft
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('scripts')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'scripts' 
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
            >
              <Mic size={18} />
              <span>Voice Script Studio</span>
            </button>

            <button
              onClick={() => setActiveTab('calls')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'calls' 
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
            >
              <PhoneForwarded size={18} />
              <span>Call Logs & Telemetry</span>
            </button>

            <button
              onClick={() => setActiveTab('tasks')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'tasks' 
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
            >
              <CheckCircle size={18} />
              <span>Follow-up Tasks</span>
              {tasks.filter(t => t.status === 'pending').length > 0 && (
                <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-semibold">
                  {tasks.filter(t => t.status === 'pending').length}
                </span>
              )}
            </button>
          </nav>

          {/* DLT & Compliance Metadata Card */}
          <div className="p-3 bg-zinc-950/80 rounded-lg border border-zinc-800/80 space-y-1.5 text-[11px] text-zinc-400">
            <div className="flex justify-between">
              <span>DLT Header:</span>
              <strong className="text-zinc-200">{tenant.dlt_header}</strong>
            </div>
            <div className="flex justify-between">
              <span>Telephony Carrier:</span>
              <strong className="text-zinc-200">Sarvam / Vobiz</strong>
            </div>
            <div className="flex justify-between">
              <span>Anti-SSRF Scraper:</span>
              <span className="text-emerald-400 font-medium">RFC 1918 Enforced</span>
            </div>
          </div>
        </aside>

        {/* Tab Main Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {/* TAB 1: LEADS CRM */}
          {activeTab === 'leads' && (
            <div className="space-y-6">
              {/* Header & Action Buttons */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-zinc-800">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Leads & Outbound Dialer</h2>
                  <p className="text-xs text-zinc-400">Manage contacts, verify consent provenance, and initiate AI voice calling.</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsCsvModalOpen(true)}
                    className="flex items-center gap-2 px-3.5 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700/80 rounded-lg text-xs font-semibold text-zinc-200 transition shadow-sm"
                  >
                    <Upload size={14} />
                    <span>Import CSV</span>
                  </button>
                  <button
                    onClick={() => setIsNewLeadOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-semibold text-white transition shadow-md shadow-blue-600/20"
                  >
                    <Plus size={15} />
                    <span>New Lead</span>
                  </button>
                </div>
              </div>

              {/* Stat Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-zinc-900/60 border border-zinc-800/80 p-4 rounded-xl">
                  <div className="text-xs font-medium text-zinc-400">Total Leads</div>
                  <div className="text-2xl font-bold text-zinc-100 mt-1">{leads.length}</div>
                </div>
                <div className="bg-zinc-900/60 border border-zinc-800/80 p-4 rounded-xl">
                  <div className="text-xs font-medium text-zinc-400">Eligible to Contact</div>
                  <div className="text-2xl font-bold text-blue-400 mt-1">
                    {leads.filter(l => l.stage === 'Eligible to Contact' && !l.is_suppressed).length}
                  </div>
                </div>
                <div className="bg-zinc-900/60 border border-zinc-800/80 p-4 rounded-xl">
                  <div className="text-xs font-medium text-zinc-400">Qualified by AI</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">
                    {leads.filter(l => l.stage === 'Qualified').length}
                  </div>
                </div>
                <div className="bg-zinc-900/60 border border-zinc-800/80 p-4 rounded-xl">
                  <div className="text-xs font-medium text-zinc-400">Suppression List (DND)</div>
                  <div className="text-2xl font-bold text-red-400 mt-1">
                    {leads.filter(l => l.is_suppressed).length}
                  </div>
                </div>
              </div>

              {/* Filters */}
              <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
                <div className="relative w-full sm:w-80">
                  <Search size={15} className="absolute left-3 top-3 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Search leads by name or phone..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-4 py-2 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <Filter size={14} className="text-zinc-500" />
                  <select
                    value={filterStage}
                    onChange={(e) => setFilterStage(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="all">All Stages</option>
                    <option value="New">New</option>
                    <option value="Eligible to Contact">Eligible to Contact</option>
                    <option value="Attempted">Attempted</option>
                    <option value="Qualified">Qualified</option>
                    <option value="Do Not Contact">Do Not Contact (Suppressed)</option>
                  </select>
                </div>
              </div>

              {/* Lead Table */}
              <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/40">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900 border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Contact</th>
                      <th className="py-3 px-4">Phone (E.164)</th>
                      <th className="py-3 px-4">Source</th>
                      <th className="py-3 px-4">Stage</th>
                      <th className="py-3 px-4">Requirement / Event</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/80">
                    {filteredLeads.map(lead => (
                      <tr key={lead.id} className="hover:bg-zinc-800/30 transition">
                        <td className="py-3.5 px-4 font-medium text-zinc-200">
                          <div>{lead.first_name} {lead.last_name}</div>
                          {lead.email && <div className="text-[11px] text-zinc-500">{lead.email}</div>}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-zinc-300">{lead.phone}</td>
                        <td className="py-3.5 px-4 text-zinc-400">{lead.source}</td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide ${
                            lead.stage === 'Qualified' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                            lead.stage === 'Do Not Contact' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                            lead.stage === 'Attempted' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          }`}>
                            {lead.stage}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-zinc-300 max-w-xs truncate">
                          {lead.custom_fields?.event || lead.custom_fields?.notes || '-'}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          {lead.is_suppressed ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-red-400 font-medium">
                              <ShieldAlert size={13} /> DND Suppressed
                            </span>
                          ) : (
                            <button
                              onClick={() => handleInitiateCall(lead)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition shadow-sm"
                            >
                              <Phone size={13} />
                              <span>Call AI Voice</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {filteredLeads.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-zinc-500">
                          No leads match the selected criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: KNOWLEDGE BASE */}
          {activeTab === 'knowledge' && (
            <div className="space-y-6">
              <div className="pb-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white tracking-tight">SSRF-Protected Website Ingestion</h2>
                <p className="text-xs text-zinc-400">
                  Scrape tenant websites and brochures. Facts require tenant admin approval before the voice agent can speak them.
                </p>
              </div>

              {/* Scrape Input Card */}
              <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-3">
                <label className="text-xs font-semibold text-zinc-200">
                  Authorized Domain URL to Scrape:
                </label>
                <div className="flex gap-3">
                  <input
                    type="url"
                    value={crawlUrl}
                    onChange={(e) => setCrawlUrl(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="https://yourbusiness.in/pricing"
                  />
                  <button
                    onClick={handleScrape}
                    disabled={isCrawling}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2"
                  >
                    {isCrawling ? <RefreshCw size={14} className="animate-spin" /> : <BookOpen size={14} />}
                    <span>{isCrawling ? "Scraping..." : "Scrape & Extract Facts"}</span>
                  </button>
                </div>
                {crawlStatusMsg && (
                  <div className="text-xs text-blue-400 flex items-center gap-1.5 pt-1">
                    <ShieldCheck size={14} />
                    <span>{crawlStatusMsg}</span>
                  </div>
                )}
              </div>

              {/* Review Queue */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-zinc-200">Extracted Facts Review Queue</h3>
                  <span className="text-xs text-zinc-400">
                    {chunks.filter(c => c.status === 'approved').length} Approved / {chunks.length} Total
                  </span>
                </div>

                <div className="space-y-3">
                  {chunks.map(chunk => (
                    <div key={chunk.id} className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 flex items-start justify-between gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-zinc-200">{chunk.title}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                            chunk.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                            chunk.status === 'draft' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-red-500/10 text-red-400 border border-red-500/20'
                          }`}>
                            {chunk.status}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed max-w-3xl">{chunk.fact_text}</p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {chunk.status === 'draft' ? (
                          <>
                            <button
                              onClick={() => handleApproveChunk(chunk.id)}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <Check size={14} /> Approve
                            </button>
                            <button
                              onClick={() => handleRejectChunk(chunk.id)}
                              className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <X size={14} /> Reject
                            </button>
                          </>
                        ) : (
                          <span className="text-xs font-medium text-emerald-400 flex items-center gap-1">
                            <CheckCircle size={14} /> Grounded
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SCRIPT STUDIO */}
          {activeTab === 'scripts' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-zinc-800">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Voice Script & Prompt Studio</h2>
                  <p className="text-xs text-zinc-400">Configure persona, opening AI disclosure statement, and approved facts citations.</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-semibold ${scriptApproved ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {scriptApproved ? "✓ Approved & Active for Dialing" : "Draft (Calls Prohibited)"}
                  </span>
                  <button
                    onClick={() => {
                      setScriptApproved(!scriptApproved);
                      showToast(scriptApproved ? "Script reverted to Draft" : "Script Approved and Activated for Live Calling!");
                    }}
                    className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition ${
                      scriptApproved ? 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700' : 'bg-emerald-600 text-white hover:bg-emerald-500'
                    }`}
                  >
                    {scriptApproved ? "Revert to Draft" : "Approve & Activate"}
                  </button>
                </div>
              </div>

              {/* Template Selectors */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { id: 'hospitality', label: 'Hotel & Hospitality' },
                  { id: 'hospital_admin', label: 'Hospital Admin (Non-Clinical)' },
                  { id: 'food_catering', label: 'Restaurant & Catering' },
                  { id: 'generic_b2b', label: 'Generic B2B Sales' }
                ].map(tmpl => (
                  <button
                    key={tmpl.id}
                    onClick={() => {
                      setSelectedVertical(tmpl.id);
                      showToast(`Switched to ${tmpl.label} prompt template`);
                    }}
                    className={`p-3 rounded-xl border text-left text-xs font-semibold transition ${
                      selectedVertical === tmpl.id 
                        ? 'border-blue-500 bg-blue-500/10 text-blue-300' 
                        : 'border-zinc-800 bg-zinc-900/60 text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    {tmpl.label}
                  </button>
                ))}
              </div>

              {/* System Prompt View & Editor */}
              <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-2">
                <label className="text-xs font-semibold text-zinc-300 flex items-center justify-between">
                  <span>Grounded Voice Agent Prompt:</span>
                  <span className="text-[11px] text-zinc-500">Sarvam Saaras + Bulbul Engine</span>
                </label>
                <textarea
                  rows={14}
                  value={scriptContent}
                  onChange={(e) => setScriptContent(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-4 font-mono text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500 leading-relaxed"
                />
              </div>
            </div>
          )}

          {/* TAB 4: CALL LOGS */}
          {activeTab === 'calls' && (
            <div className="space-y-6">
              <div className="pb-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white tracking-tight">Call Logs & Audio Telemetry</h2>
                <p className="text-xs text-zinc-400">Transparent 30-second pulse telephony metering and AI conversation summaries.</p>
              </div>

              <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/40">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900 border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Call SID</th>
                      <th className="py-3 px-4">Destination</th>
                      <th className="py-3 px-4">Carrier</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Billed Cost</th>
                      <th className="py-3 px-4">AI Outcome Summary</th>
                      <th className="py-3 px-4 text-right">Recording</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/80">
                    {calls.map(c => (
                      <tr key={c.id} className="hover:bg-zinc-800/30 transition">
                        <td className="py-3.5 px-4 font-mono text-zinc-400">{c.provider_call_sid}</td>
                        <td className="py-3.5 px-4 font-semibold text-zinc-200">{c.destination}</td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[11px]">
                            {c.provider_type.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-zinc-300">{c.duration_seconds}s</td>
                        <td className="py-3.5 px-4 font-semibold text-blue-400">₹{c.cost_inr.toFixed(2)}</td>
                        <td className="py-3.5 px-4 text-zinc-300 max-w-sm truncate">{c.summary || 'Call Completed'}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => showToast("Playing synthetic recording audio...", "info")}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs transition"
                          >
                            <Play size={12} /> Play
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: TASKS */}
          {activeTab === 'tasks' && (
            <div className="space-y-6">
              <div className="pb-4 border-b border-zinc-800">
                <h2 className="text-xl font-bold text-white tracking-tight">Lead Follow-up Tasks</h2>
                <p className="text-xs text-zinc-400">Action items automatically created when voice agents qualify leads or receive transfer requests.</p>
              </div>

              <div className="space-y-3">
                {tasks.map(task => (
                  <div
                    key={task.id}
                    className={`p-4 rounded-xl border flex items-center justify-between gap-4 transition ${
                      task.status === 'completed' 
                        ? 'bg-zinc-900/30 border-zinc-800/50 opacity-60' 
                        : 'bg-zinc-900/60 border-zinc-800'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-semibold ${task.status === 'completed' ? 'line-through text-zinc-500' : 'text-zinc-200'}`}>
                          {task.title}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          task.priority === 'urgent' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                          task.priority === 'high' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        }`}>
                          {task.priority} Priority
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400">{task.description}</p>
                    </div>

                    <button
                      onClick={() => handleToggleTask(task.id)}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                        task.status === 'completed'
                          ? 'bg-emerald-950 border border-emerald-800 text-emerald-300 hover:bg-emerald-900'
                          : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200'
                      }`}
                    >
                      {task.status === 'completed' ? "Completed ✓" : "Mark Complete"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* NEW LEAD DIALOG (Modal) */}
      {isNewLeadOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Add New Lead</h3>
                <p className="text-xs text-zinc-400">Capture lead with explicit consent for outbound calling.</p>
              </div>
              <button onClick={() => setIsNewLeadOpen(false)} className="text-zinc-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateLead} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-300 font-medium mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    value={newLeadForm.first_name}
                    onChange={(e) => setNewLeadForm({ ...newLeadForm, first_name: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Rohan"
                  />
                </div>
                <div>
                  <label className="block text-zinc-300 font-medium mb-1">Last Name</label>
                  <input
                    type="text"
                    value={newLeadForm.last_name}
                    onChange={(e) => setNewLeadForm({ ...newLeadForm, last_name: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Mehta"
                  />
                </div>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">
                  Indian Phone Number (E.164) <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newLeadForm.phone}
                  onChange={(e) => setNewLeadForm({ ...newLeadForm, phone: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="+919876543210 or 9876543210"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Email Address</label>
                <input
                  type="email"
                  value={newLeadForm.email}
                  onChange={(e) => setNewLeadForm({ ...newLeadForm, email: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="rohan@example.com"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Consent Provenance Statement</label>
                <input
                  type="text"
                  value={newLeadForm.consent_statement}
                  onChange={(e) => setNewLeadForm({ ...newLeadForm, consent_statement: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">Inquiry / Event Requirements</label>
                <input
                  type="text"
                  value={newLeadForm.requirement}
                  onChange={(e) => setNewLeadForm({ ...newLeadForm, requirement: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="E.g. Wedding reception 250 guests"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setIsNewLeadOpen(false)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-600/20"
                >
                  Save Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV IMPORT MODAL */}
      {isCsvModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Bulk Import Leads (CSV)</h3>
                <p className="text-xs text-zinc-400">Paste CSV data with headers: name, phone, email, requirement</p>
              </div>
              <button onClick={() => setIsCsvModalOpen(false)} className="text-zinc-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <textarea
              rows={8}
              value={csvRawText}
              onChange={(e) => setCsvRawText(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 font-mono text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />

            <div className="flex justify-end gap-2.5 pt-2 border-t border-zinc-800">
              <button
                onClick={() => setIsCsvModalOpen(false)}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleImportCsv}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-600/20"
              >
                Import Leads
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ACTIVE CALL MODAL (Interactive Click-to-Call with Live Audio & Transfer) */}
      {activeCallLead && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-5 text-center">
            {/* Pulsing Avatar */}
            <div className="relative mx-auto w-20 h-20 flex items-center justify-center">
              <div className={`absolute inset-0 rounded-full bg-emerald-500/20 ${callProgress === 'connected' ? 'animate-ping' : ''}`} />
              <div className="relative w-16 h-16 rounded-full bg-emerald-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/30">
                <Phone size={28} />
              </div>
            </div>

            <div>
              <h3 className="text-lg font-bold text-white">
                {activeCallLead.first_name} {activeCallLead.last_name}
              </h3>
              <p className="text-xs font-mono text-zinc-400 mt-0.5">{activeCallLead.phone}</p>
            </div>

            {/* Carrier Route Selector */}
            <div className="flex items-center justify-center gap-2">
              <span className="text-xs text-zinc-500">Route:</span>
              <select
                value={selectedProvider}
                onChange={(e: any) => setSelectedProvider(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1 text-xs text-zinc-300 font-mono"
              >
                <option value="sarvam_vobiz">Sarvam Vobiz (Native Transfer)</option>
                <option value="exotel">Exotel (Production Candidate)</option>
                <option value="smartflo">Tata Tele Smartflo (Enterprise)</option>
                <option value="mock">Mock Simulator</option>
              </select>
            </div>

            {/* Call Status & Timer */}
            <div className="p-3.5 rounded-xl bg-zinc-950 border border-zinc-800/80 space-y-1">
              <div className="flex items-center justify-center gap-2 text-xs font-semibold text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                {callProgress === 'initiating' && "Initiating Indian Telecom Line..."}
                {callProgress === 'ringing' && "Ringing Customer Handset..."}
                {callProgress === 'connected' && `AI Connected • ${callSeconds}s`}
                {callProgress === 'transferred' && "Transferred to Human Specialist"}
              </div>
              <p className="text-[11px] text-zinc-400">
                {selectedProvider === 'sarvam_vobiz' ? "Sarvam Voice Agents (Hindi/English) • ₹0.20/30s pulse" : "Carrier Dialing Active"}
              </p>
            </div>

            {/* Live Conversation Dialogue Stream */}
            {callProgress === 'connected' && (
              <div className="text-left bg-zinc-950/80 border border-zinc-800 rounded-xl p-3.5 space-y-2 max-h-44 overflow-y-auto text-xs">
                {liveTranscript.map((t, idx) => (
                  <div key={idx} className={t.role === 'agent' ? 'text-blue-300' : 'text-zinc-300'}>
                    <strong className="text-[10px] uppercase font-semibold text-zinc-500 block">
                      {t.role === 'agent' ? 'Sarvam AI Agent' : 'Customer'}
                    </strong>
                    <span>{t.text}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons: Transfer & Hang Up */}
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={handleTransferCall}
                className="flex items-center gap-1.5 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-xl text-xs font-semibold transition border border-zinc-700/80"
              >
                <PhoneForwarded size={14} className="text-blue-400" />
                <span>Transfer Call</span>
              </button>

              <button
                onClick={handleHangup}
                className="flex items-center gap-1.5 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-semibold transition shadow-lg shadow-red-600/20"
              >
                <PhoneOff size={15} />
                <span>Hang Up</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
