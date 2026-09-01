'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import catalogJson from '@/data/catalog.json';
import { buildEvidence, diagnoseDeterministically, mergeSemantic } from '@/lib/diagnosis';
import { forgeStages } from '@/lib/forge';
import {
  defaultProfile,
  loadProfile,
  masteryByCourse,
  parseProfile,
  profileCsv,
  saveProfile,
  type LearnerProfile,
} from '@/lib/learner-store';
import type { Catalog, Course, Diagnosis, ForgeStage } from '@/lib/canopy-types';

const catalog = catalogJson as Catalog;
type TabId = 'learn' | 'forge' | 'evidence' | 'profile';
type SemanticReply = {
  requestId: string;
  ok: boolean;
  mode?: 'semantic-webgpu' | 'semantic-wasm';
  scores?: Array<{ id: string; score: number }>;
  message?: string;
};

interface SpeechRecognitionEventLike {
  results: ArrayLike<{ 0: { transcript: string } }>;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  start(): void;
}

interface SpeechWindow extends Window {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
}

function download(name: string, content: string, type: string): void {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

function newId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function metric(value: number | null, suffix = ''): string {
  return value === null || Number.isNaN(value) ? '—' : `${Math.round(value)}${suffix}`;
}

export default function Home() {
  const [profile, setProfile] = useState<LearnerProfile>(() => defaultProfile());
  const [hydrated, setHydrated] = useState(false);
  const [tab, setTab] = useState<TabId>('learn');
  const [stageIndex, setStageIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [engine, setEngine] = useState<'idle' | 'loading' | 'webgpu' | 'wasm' | 'fallback'>('idle');
  const [announcement, setAnnouncement] = useState('Canopy is ready.');
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [notes, setNotes] = useState('');
  const [forgeTitle, setForgeTitle] = useState('My new course');
  const [draft, setDraft] = useState<ForgeStage[]>([]);
  const [importError, setImportError] = useState('');
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const attemptStarted = useRef(0);
  const workerRef = useRef<Worker | null>(null);
  const pendingRef = useRef(new Map<string, (reply: SemanticReply) => void>());

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setProfile(loadProfile());
      setHydrated(true);
      attemptStarted.current = Date.now();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (hydrated) saveProfile(profile);
  }, [hydrated, profile]);

  const locale = catalog.locales[profile.locale] ?? catalog.locales.en;
  const canonicalCourse = catalog.courses.find((item) => item.id === profile.courseId) ?? catalog.courses[0];
  const course = locale.courses[canonicalCourse.id] ?? canonicalCourse;
  const stage = course.stages[Math.min(stageIndex, course.stages.length - 1)];
  const messages = locale.messages;
  const rtl = locale.meta.direction === 'rtl';

  useEffect(() => {
    document.documentElement.lang = locale.meta.bcp47;
    document.documentElement.dir = locale.meta.direction;
    document.body.classList.toggle('high-contrast', profile.preferences.contrast);
    document.body.classList.toggle('dyslexia-friendly', profile.preferences.dyslexia);
    document.body.classList.toggle('reduce-motion', profile.preferences.reduceMotion);
  }, [locale, profile.preferences]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && event.key.toLocaleLowerCase() === 'd') {
        event.preventDefault();
        answerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => () => workerRef.current?.terminate(), []);

  const updateProfile = useCallback((mutate: (current: LearnerProfile) => LearnerProfile) => {
    setProfile((current) => mutate(current));
  }, []);

  const ensureWorker = useCallback((): Worker => {
    if (workerRef.current) return workerRef.current;
    const worker = new Worker(new URL('../workers/semantic.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (event: MessageEvent<SemanticReply>) => {
      const resolve = pendingRef.current.get(event.data.requestId);
      if (resolve) {
        pendingRef.current.delete(event.data.requestId);
        resolve(event.data);
      }
    };
    workerRef.current = worker;
    return worker;
  }, []);

  const requestSemantic = useCallback(async (text: string, activeCourse: Course): Promise<SemanticReply> => {
    const requestId = newId('semantic');
    const evidence = buildEvidence(activeCourse, activeCourse.stages[stageIndex]).map((item) => ({
      id: item.id,
      text: `${item.title}. ${item.text}`,
    }));
    const worker = ensureWorker();
    return new Promise((resolve) => {
      const timer = window.setTimeout(() => {
        pendingRef.current.delete(requestId);
        resolve({ requestId, ok: false, message: 'Model load timed out; local rubric remains active.' });
      }, 60000);
      pendingRef.current.set(requestId, (reply) => {
        window.clearTimeout(timer);
        resolve(reply);
      });
      worker.postMessage({ requestId, answer: text, evidence });
    });
  }, [ensureWorker, stageIndex]);

  const recordDiagnosis = useCallback((result: Diagnosis) => {
    const started = attemptStarted.current || Date.now();
    const elapsedSeconds = Math.max(1, Math.round((Date.now() - started) / 1000));
    updateProfile((current) => ({
      ...current,
      events: [
        ...current.events,
        {
          id: newId('attempt'),
          at: new Date().toISOString(),
          courseId: canonicalCourse.id,
          stageId: stage.id,
          claim: result.allowedClaim,
          confidence: result.confidence,
          mastery: result.masterySignal,
          explanationScore: result.explanationScore,
          misconception: result.hypothesis.includes('misconception') ? course.misconception : '',
          elapsedSeconds,
        },
      ].slice(-500),
    }));
    attemptStarted.current = Date.now();
  }, [canonicalCourse.id, course.misconception, stage.id, updateProfile]);

  const checkReasoning = useCallback(() => {
    if (!answer.trim()) {
      setAnnouncement('Add an explanation before asking for a diagnosis.');
      answerRef.current?.focus();
      return;
    }
    const result = diagnoseDeterministically(answer, course, stage);
    setDiagnosis(result);
    recordDiagnosis(result);
    setAnnouncement(`${result.confidence} confidence. ${result.hypothesis}`);
  }, [answer, course, recordDiagnosis, stage]);

  const enablePrivateAi = useCallback(async () => {
    if (!answer.trim()) {
      setAnnouncement('Write an explanation first, then enable private AI.');
      answerRef.current?.focus();
      return;
    }
    const base = diagnosis ?? diagnoseDeterministically(answer, course, stage);
    setDiagnosis(base);
    setEngine('loading');
    setAnnouncement('Downloading the private multilingual model. Learner text stays in this browser.');
    const reply = await requestSemantic(answer, course);
    if (!reply.ok || !reply.mode || !reply.scores) {
      setEngine('fallback');
      setAnnouncement(reply.message ?? 'Private model unavailable. Inspectable local rubric remains active.');
      return;
    }
    const merged = mergeSemantic(base, { mode: reply.mode, scores: reply.scores });
    setDiagnosis(merged);
    setEngine(reply.mode === 'semantic-webgpu' ? 'webgpu' : 'wasm');
    setAnnouncement(`Private semantic diagnosis ready with ${merged.confidence} confidence.`);
  }, [answer, course, diagnosis, requestSemantic, stage]);

  const startVoice = useCallback(() => {
    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setAnnouncement('Voice input is not supported by this browser. The text field remains available.');
      return;
    }
    const recognition = new Recognition();
    recognition.lang = locale.meta.bcp47;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      setAnswer(event.results[0][0].transcript);
      setAnnouncement('Voice response captured. Review it before diagnosis.');
    };
    recognition.onerror = () => setAnnouncement('Voice input failed. You can continue by typing.');
    recognition.start();
  }, [locale.meta.bcp47]);

  const speakDiagnosis = useCallback(() => {
    if (!diagnosis || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(`${diagnosis.hypothesis} ${diagnosis.nextQuestion}`);
    utterance.lang = locale.meta.bcp47;
    window.speechSynthesis.speak(utterance);
  }, [diagnosis, locale.meta.bcp47]);

  const courseEvents = profile.events.filter((event) => event.courseId === canonicalCourse.id);
  const preScore = courseEvents[0]?.explanationScore ?? null;
  const postScore = courseEvents.at(-1)?.explanationScore ?? null;
  const recovery = (() => {
    const start = courseEvents.find((event) => event.claim === 'partial' || event.claim === 'uncertain');
    if (!start) return null;
    const recovered = courseEvents.find((event) => event.at > start.at && (event.claim === 'aligned' || event.claim === 'correct'));
    return recovered ? (new Date(recovered.at).getTime() - new Date(start.at).getTime()) / 1000 : null;
  })();
  const mastery = masteryByCourse(profile);
  const dueReviews = profile.events.filter((event) => event.mastery < 0.62).slice(-5).reverse();

  const tabLabels: Array<{ id: TabId; label: string; icon: string }> = [
    { id: 'learn', label: messages.coach, icon: '✦' },
    { id: 'forge', label: `${messages.course} · AI`, icon: '⌘' },
    { id: 'evidence', label: messages.evidence, icon: '⌁' },
    { id: 'profile', label: messages.toolkit, icon: '◉' },
  ];

  const constellationStyle = useMemo(() => ({
    transform: profile.preferences.reduceMotion ? undefined : `perspective(900px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
  }), [profile.preferences.reduceMotion, tilt]);

  return (
    <main className="canopy-shell" dir={rtl ? 'rtl' : 'ltr'}>
      <a className="skip-link" href="#main-workspace">Skip to learning workspace</a>
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />

      <header className="topbar">
        <button className="brand" type="button" onClick={() => setTab('learn')} aria-label="Canopy home">
          <span className="brand-mark" aria-hidden="true">⌘</span>
          <span><strong>CANOPY</strong><small>PRIVATE AI LEARNING SYSTEM</small></span>
        </button>
        <nav className="tabs" aria-label="Canopy workspaces">
          {tabLabels.map((item) => (
            <button key={item.id} type="button" className={tab === item.id ? 'tab active' : 'tab'} aria-current={tab === item.id ? 'page' : undefined} onClick={() => setTab(item.id)}>
              <span aria-hidden="true">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="top-actions">
          <label className="language-picker"><span>{messages.language}</span><select value={profile.locale} onChange={(event) => updateProfile((current) => ({ ...current, locale: event.target.value }))}>
            {Object.values(catalog.locales).map((item) => <option key={item.meta.code} value={item.meta.code}>{item.meta.native_name}</option>)}
          </select></label>
          <span className={`engine-pill engine-${engine}`} title="Learner text is never sent to an inference API"><i aria-hidden="true" />{engine === 'webgpu' ? 'PRIVATE AI · WEBGPU' : engine === 'wasm' ? 'PRIVATE AI · WASM' : engine === 'loading' ? 'LOADING PRIVATE AI' : 'LOCAL RUBRIC · READY'}</span>
        </div>
      </header>

      <section className="hero">
        <div><p className="eyebrow">{locale.academyLabels[course.academyId]} · {course.ageBand}</p><h1>{course.subject} <span>/</span> {course.title}</h1><p>{course.bigQuestion}</p></div>
        <ul className="course-switcher" aria-label={messages.subject_routes}>
          {catalog.courses.map((item) => { const localized = locale.courses[item.id] ?? item; return <li key={item.id}><button type="button" className={item.id === canonicalCourse.id ? 'course-chip selected' : 'course-chip'} title={`${localized.subject} · ${localized.title}`} onClick={() => { setProfile((current) => ({ ...current, courseId: item.id })); setStageIndex(0); setDiagnosis(null); }}><span aria-hidden="true">{localized.icon}</span><b>{localized.subject}</b></button></li>; })}
        </ul>
      </section>

      <section id="main-workspace" className="workspace" tabIndex={-1}>
        {tab === 'learn' && <>
          <article className="glass-card constellation-card">
            <div className="card-heading"><div><p className="eyebrow">{messages.learning_map}</p><h2>{stage.label}</h2></div><span className="stage-count">{stageIndex + 1} / {course.stages.length}</span></div>
            <figure className="constellation" style={constellationStyle} onPointerMove={(event) => { const rect = event.currentTarget.getBoundingClientRect(); setTilt({ x: -((event.clientY - rect.top) / rect.height - .5) * 7, y: ((event.clientX - rect.left) / rect.width - .5) * 8 }); }} onPointerLeave={() => setTilt({ x: 0, y: 0 })} aria-label={`Interactive six-stage model for ${course.title}`}>
              <svg viewBox="0 0 600 430" aria-hidden="true" focusable="false">
                <defs><radialGradient id="coreGlow"><stop offset="0" stopColor={course.accent} stopOpacity=".95" /><stop offset="1" stopColor={course.accent} stopOpacity="0" /></radialGradient><filter id="glow"><feGaussianBlur stdDeviation="5" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
                <circle cx="300" cy="215" r="105" fill="url(#coreGlow)" opacity=".22" />
                {course.stages.map((item, index) => { const angle = (Math.PI * 2 * index) / course.stages.length - Math.PI / 2; const nextAngle = (Math.PI * 2 * (index + 1)) / course.stages.length - Math.PI / 2; return <line key={item.id} x1={300 + Math.cos(angle) * 170} y1={215 + Math.sin(angle) * 145} x2={300 + Math.cos(nextAngle) * 170} y2={215 + Math.sin(nextAngle) * 145} className={index < stageIndex ? 'map-link complete' : 'map-link'} />; })}
                <circle cx="300" cy="215" r="58" fill="#071f24" stroke={course.accent} strokeWidth="2" filter="url(#glow)" /><text x="300" y="205" textAnchor="middle" className="core-label">{course.subject}</text><text x="300" y="232" textAnchor="middle" className="core-model">{stage.model.slice(0, 18)}</text>
              </svg>
              {course.stages.map((item, index) => { const angle = (Math.PI * 2 * index) / course.stages.length - Math.PI / 2; const stageMastery = profile.events.filter((event) => event.stageId === item.id).at(-1)?.mastery ?? 0; return <button key={item.id} type="button" className={index === stageIndex ? 'node active' : index < stageIndex ? 'node complete' : 'node'} style={{ left: `${50 + Math.cos(angle) * 34}%`, top: `${50 + Math.sin(angle) * 34}%` }} onClick={() => { setStageIndex(index); setDiagnosis(null); attemptStarted.current = Date.now(); }} aria-label={`${item.label}, mastery ${Math.round(stageMastery * 100)} percent`}><span aria-hidden="true">{item.icon}</span><b>{item.shortLabel}</b><small>{Math.round(stageMastery * 100)}%</small></button>; })}
            </figure>
            <div className="stage-strip"><div><span>{messages.model}</span><b>{stage.model}</b></div><div><span>{messages.question}</span><b>{stage.question}</b></div></div>
          </article>

          <aside className="glass-card coach-card">
            <div className="card-heading"><div><p className="eyebrow">{messages.teacher_read}</p><h2>{messages.your_thinking}</h2></div><button type="button" className="icon-button" onClick={startVoice} aria-label="Start voice input">◉</button></div>
            <p className="prompt">{stage.question}</p><textarea ref={answerRef} value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder={messages.teacher_listening} aria-describedby="answer-help" /><div id="answer-help" className="input-help"><span>Alt+D · focus</span><span>{answer.length} characters</span></div>
            <div className="button-row"><button type="button" className="primary-button" onClick={checkReasoning}>{messages.check_reasoning} →</button><button type="button" className="ai-button" onClick={enablePrivateAi} disabled={engine === 'loading'}>{engine === 'loading' ? 'Loading 118 MB model…' : '✦ Enable private AI'}</button></div>
            <p className="privacy-note">Model files download from Hugging Face. Your answer stays in this browser; no account or API key is used.</p>
            {diagnosis ? <section className="diagnosis" aria-label="Inspectable diagnosis">
              <div className="diagnosis-top"><span className={`claim claim-${diagnosis.allowedClaim}`}>{diagnosis.allowedClaim}</span><span>{diagnosis.confidence.toUpperCase()} CONFIDENCE</span><button type="button" className="speak" onClick={speakDiagnosis} aria-label="Read diagnosis aloud">◖))</button></div>
              <h3>{diagnosis.hypothesis}</h3><div className="diagnosis-grid"><div><span>{messages.learning_signal}</span><b>{diagnosis.explanationScore}/100</b></div><div><span>Mastery signal</span><b>{Math.round(diagnosis.masterySignal * 100)}%</b></div><div><span>Engine</span><b>{diagnosis.mode}</b></div></div>
              <details open><summary>Why this diagnosis</summary><ul>{diagnosis.confidenceReasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>{diagnosis.limitations.map((limit) => <p className="boundary" key={limit}>Boundary · {limit}</p>)}</details>
              <details><summary>{messages.evidence} · retrieved course material</summary>{diagnosis.evidence.map((item) => <article className="evidence-item" key={item.id}><span>{item.score.toFixed(2)}</span><div><b>{item.title}</b><p>{item.text}</p></div></article>)}</details>
              <p className="next-question"><span>{messages.next_question}</span>{diagnosis.nextQuestion}</p>
            </section> : <div className="empty-diagnosis"><span aria-hidden="true">⌁</span><p>Submit a reasoning trace to reveal evidence, confidence, a misconception hypothesis, and the next best action.</p></div>}
          </aside>
        </>}

        {tab === 'forge' && <section className="glass-card wide-card forge-workspace">
          <div className="card-heading"><div><p className="eyebrow">AI COURSE FORGE · ON DEVICE</p><h2>Turn teacher material into a six-stage learning journey</h2></div><span className="honesty-badge">TEACHER REVIEW REQUIRED</span></div>
          <div className="forge-grid"><div><label>Course title<input value={forgeTitle} onChange={(event) => setForgeTitle(event.target.value)} /></label><label>Paste notes, a topic, or source text<textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Paste at least a paragraph. Canopy extracts repeated concepts, prerequisites, questions, transfer tasks, and evidence anchors locally." /></label><button type="button" className="primary-button" onClick={() => { setDraft(forgeStages(notes)); setAnnouncement('Six-stage draft generated locally. Review every stage before saving.'); }} disabled={notes.trim().length < 80}>Generate editable course →</button><p className="privacy-note">This is an extractive teaching draft, not an authority. It never uploads notes and never invents learner-impact results.</p></div>
            <div className="forge-stages">{draft.length ? draft.map((item, index) => <article key={item.id}><span>{String(index + 1).padStart(2, '0')}</span><label>Stage<input value={item.label} onChange={(event) => setDraft((current) => current.map((stageItem) => stageItem.id === item.id ? { ...stageItem, label: event.target.value } : stageItem))} /></label><label>Concept<input value={item.concept} onChange={(event) => setDraft((current) => current.map((stageItem) => stageItem.id === item.id ? { ...stageItem, concept: event.target.value } : stageItem))} /></label><label>Learning question<textarea value={item.question} onChange={(event) => setDraft((current) => current.map((stageItem) => stageItem.id === item.id ? { ...stageItem, question: event.target.value } : stageItem))} /></label></article>) : <div className="forge-empty"><span>⌘</span><p>Your editable concept map will grow here.</p></div>}
              {draft.length > 0 && <button type="button" className="ai-button" onClick={() => { updateProfile((current) => ({ ...current, forgedCourses: [...current.forgedCourses, { id: newId('course'), title: forgeTitle, createdAt: new Date().toISOString(), stages: draft }].slice(-20) })); setAnnouncement(`${forgeTitle} saved to this device.`); }}>Save reviewed draft to this device</button>}
            </div>
          </div>
        </section>}

        {tab === 'evidence' && <section className="evidence-workspace">
          <article className="glass-card evidence-summary"><div className="card-heading"><div><p className="eyebrow">HONEST LEARNING EVIDENCE</p><h2>Observed in this browser</h2></div><span className="honesty-badge">NOT A CONTROLLED STUDY</span></div><div className="metric-grid"><div><span>Pre explanation</span><strong>{metric(preScore, '/100')}</strong><small>first recorded attempt</small></div><div><span>Post explanation</span><strong>{metric(postScore, '/100')}</strong><small>latest recorded attempt</small></div><div><span>Growth</span><strong>{preScore !== null && postScore !== null ? `${postScore - preScore >= 0 ? '+' : ''}${postScore - preScore}` : '—'}</strong><small>within-session difference</small></div><div><span>Recovery time</span><strong>{metric(recovery, 's')}</strong><small>partial → aligned</small></div></div>
            <figure className="spark-chart" aria-label="Explanation quality over attempts">{courseEvents.length ? courseEvents.map((event, index) => <i key={event.id} style={{ height: `${Math.max(8, event.explanationScore)}%` }} title={`Attempt ${index + 1}: ${event.explanationScore}`} />) : <p>Complete two explanations to reveal a learning trajectory.</p>}</figure>
            <div className="rating"><span>Usability rating</span>{[1, 2, 3, 4, 5].map((value) => <button key={value} type="button" className={profile.usabilityRating === value ? 'selected' : ''} onClick={() => updateProfile((current) => ({ ...current, usabilityRating: value }))} aria-label={`Rate ${value} out of 5`}>{value}</button>)}</div><p className="boundary">Canopy reports only measurements created by real interactions on this device. No pilot participants, effect sizes, or learning gains are fabricated.</p>
          </article>
          <article className="glass-card heatmap-card"><p className="eyebrow">TEACHER VIEW · COURSE HEATMAP</p><h2>Where the class of one needs support</h2><div className="heatmap">{catalog.courses.map((item) => { const localized = locale.courses[item.id] ?? item; const value = mastery[item.id] ?? 0; return <div key={item.id}><span>{localized.icon}</span><b>{localized.subject}</b><i style={{ '--mastery': value } as React.CSSProperties}>{Math.round(value * 100)}%</i></div>; })}</div></article>
        </section>}

        {tab === 'profile' && <section className="profile-workspace">
          <article className="glass-card profile-card"><p className="eyebrow">PERSISTENT LEARNER MODEL · DEVICE LOCAL</p><h2>{profile.events.length} learning signals across {Object.keys(mastery).length} courses</h2><div className="preference-grid">{([['contrast', 'High contrast'], ['dyslexia', 'Dyslexia-friendly type'], ['reduceMotion', 'Reduced motion']] as const).map(([key, label]) => <label key={key}><input type="checkbox" checked={profile.preferences[key]} onChange={(event) => updateProfile((current) => ({ ...current, preferences: { ...current.preferences, [key]: event.target.checked } }))} />{label}</label>)}</div>
            <div className="export-row"><button type="button" className="primary-button" onClick={() => download('canopy-profile.json', JSON.stringify(profile, null, 2), 'application/json')}>Export profile JSON</button><button type="button" className="ai-button" onClick={() => download('canopy-evidence.csv', profileCsv(profile), 'text/csv')}>Export evidence CSV</button><label className="import-button">Import profile<input type="file" accept="application/json" onChange={async (event) => { const file = event.target.files?.[0]; if (!file) return; try { setProfile(parseProfile(await file.text())); setImportError(''); setAnnouncement('Profile imported and validated.'); } catch (error) { setImportError(error instanceof Error ? error.message : 'Invalid profile.'); } }} /></label></div>{importError && <p className="error" role="alert">{importError}</p>}<p className="privacy-note">Versioned imports are validated and capped. Nothing syncs to a server.</p>
          </article>
          <article className="glass-card review-card"><p className="eyebrow">SPACED REVIEW QUEUE</p><h2>{dueReviews.length ? `${dueReviews.length} concepts ready for another look` : 'No low-mastery concepts are due'}</h2>{dueReviews.map((event) => { const eventCourse = locale.courses[event.courseId] ?? catalog.courses.find((item) => item.id === event.courseId); const eventStage = eventCourse?.stages.find((item) => item.id === event.stageId); return <button key={event.id} type="button" onClick={() => { setProfile((current) => ({ ...current, courseId: event.courseId })); setStageIndex(Math.max(0, eventCourse?.stages.findIndex((item) => item.id === event.stageId) ?? 0)); setTab('learn'); }}><span>{eventCourse?.icon}</span><div><b>{eventCourse?.subject} · {eventStage?.label}</b><small>{Math.round(event.mastery * 100)}% mastery · {event.claim}</small></div><i>Review →</i></button>; })}<h3>Misconception timeline</h3><ol className="timeline">{profile.events.filter((event) => event.misconception).slice(-5).reverse().map((event) => <li key={event.id}><time>{new Date(event.at).toLocaleString()}</time><p>{event.misconception}</p></li>)}</ol></article>
        </section>}
      </section>

      <footer><span>CANOPY · ACCOUNT-FREE JUDGE BUILD</span><span>9 COURSES · 20 LANGUAGES · PRIVATE ON-DEVICE AI</span><a href="https://github.com/moscraciunxxx/canopy-ai-teacher">SOURCE ↗</a></footer>
      <div className="sr-only" aria-live="polite" aria-atomic="true">{announcement}</div>
    </main>
  );
}
