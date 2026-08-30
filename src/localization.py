"""Deterministic multilingual presentation for the Canopy academy.

The source curriculum remains the canonical evidence layer.  This module
creates a localized presentation copy while preserving identifiers, equations,
lab kinds, and source URLs.  The phrase packs are intentionally offline-first
and labelled beta in the UI so schools can add native-speaker review before a
production rollout.
"""

from __future__ import annotations

import copy
import unicodedata
from typing import Any, Literal, Mapping, TypedDict, cast


Direction = Literal["ltr", "rtl"]


class Language(TypedDict):
    code: str
    bcp47: str
    english_name: str
    native_name: str
    direction: Direction
    script: str


class CourseTranslation(TypedDict):
    subject: str
    title: str
    question: str


_LANGUAGES: tuple[Language, ...] = (
    {"code": "en", "bcp47": "en", "english_name": "English", "native_name": "English", "direction": "ltr", "script": "Latin"},
    {"code": "zh", "bcp47": "zh-Hans", "english_name": "Mandarin Chinese", "native_name": "简体中文", "direction": "ltr", "script": "Hans"},
    {"code": "hi", "bcp47": "hi", "english_name": "Hindi", "native_name": "हिन्दी", "direction": "ltr", "script": "Devanagari"},
    {"code": "es", "bcp47": "es", "english_name": "Spanish", "native_name": "Español", "direction": "ltr", "script": "Latin"},
    {"code": "ar", "bcp47": "ar", "english_name": "Modern Standard Arabic", "native_name": "العربية", "direction": "rtl", "script": "Arabic"},
    {"code": "fr", "bcp47": "fr", "english_name": "French", "native_name": "Français", "direction": "ltr", "script": "Latin"},
    {"code": "bn", "bcp47": "bn", "english_name": "Bengali", "native_name": "বাংলা", "direction": "ltr", "script": "Bengali"},
    {"code": "pt", "bcp47": "pt", "english_name": "Portuguese", "native_name": "Português", "direction": "ltr", "script": "Latin"},
    {"code": "ru", "bcp47": "ru", "english_name": "Russian", "native_name": "Русский", "direction": "ltr", "script": "Cyrillic"},
    {"code": "id", "bcp47": "id", "english_name": "Indonesian", "native_name": "Bahasa Indonesia", "direction": "ltr", "script": "Latin"},
    {"code": "ur", "bcp47": "ur", "english_name": "Urdu", "native_name": "اردو", "direction": "rtl", "script": "Arabic"},
    {"code": "de", "bcp47": "de", "english_name": "German", "native_name": "Deutsch", "direction": "ltr", "script": "Latin"},
    {"code": "ja", "bcp47": "ja", "english_name": "Japanese", "native_name": "日本語", "direction": "ltr", "script": "Jpan"},
    {"code": "pcm", "bcp47": "pcm", "english_name": "Nigerian Pidgin", "native_name": "Naijá", "direction": "ltr", "script": "Latin"},
    {"code": "mr", "bcp47": "mr", "english_name": "Marathi", "native_name": "मराठी", "direction": "ltr", "script": "Devanagari"},
    {"code": "vi", "bcp47": "vi", "english_name": "Vietnamese", "native_name": "Tiếng Việt", "direction": "ltr", "script": "Latin"},
    {"code": "te", "bcp47": "te", "english_name": "Telugu", "native_name": "తెలుగు", "direction": "ltr", "script": "Telugu"},
    {"code": "tr", "bcp47": "tr", "english_name": "Turkish", "native_name": "Türkçe", "direction": "ltr", "script": "Latin"},
    {"code": "ro", "bcp47": "ro", "english_name": "Romanian", "native_name": "Română", "direction": "ltr", "script": "Latin"},
    {"code": "yue", "bcp47": "yue-Hant", "english_name": "Cantonese", "native_name": "粵語", "direction": "ltr", "script": "Hant"},
)


_MESSAGE_KEYS: tuple[str, ...] = (
    "choose_language", "academy", "course", "show_english", "translation_beta",
    "interactive_lab", "lab_title", "course_invite", "transfer", "teacher_watch",
    "roleplay", "node_question", "node_description", "node_hint", "practice_question",
    "feedback_strong", "feedback_developing", "feedback_start", "check_reasoning",
    "your_thinking", "sources", "english_reference", "parameter", "result", "inquiry",
    "learning_map", "coach", "learn", "remix", "apply", "toolkit", "current_focus",
    "teacher_read", "learning_signal", "next_question", "teacher_listening", "reset_model",
    "prediction", "subject_routes", "language", "beta_short", "evidence", "model",
    "explanation", "question", "teacher_ready", "experiment",
)


def _pack(*values: str) -> dict[str, str]:
    if len(values) != len(_MESSAGE_KEYS):
        raise ValueError(f"Locale pack has {len(values)} values; expected {len(_MESSAGE_KEYS)}")
    return dict(zip(_MESSAGE_KEYS, values, strict=True))


_PACKS: dict[str, dict[str, str]] = {
    "en": _pack(
        "Choose your learning language", "Academy", "Course", "Show English reference",
        "Community translation beta · native-speaker review recommended",
        "INTERACTIVE WORLD LAB", "Manipulate the model. Then defend what changed.",
        "Enter {title} through a question, a model, and evidence.",
        "Transfer your understanding of {title} to a new situation.",
        "I am watching for assumptions and evidence in {subject}, not only a final answer.",
        "Coach a classmate through {title}; ask for evidence and a boundary.",
        "At the {stage} stage, what does the model reveal about {title}?",
        "Use {stage} to connect the visual model, the evidence, and the course question.",
        "Change one thing at a time. State what you expect before you test it.",
        "Practice mission", "Strong reasoning signal", "Developing reasoning signal",
        "Give the teacher a trace of your thinking", "Check my reasoning", "Your thinking",
        "Sources", "English reference", "Parameter", "Result", "Inquiry cycle",
        "Learning constellation", "Coach · Socratic", "Learn · Visual", "Remix · Practice",
        "Apply · Roleplay", "Learning toolkit", "CURRENT FOCUS", "TEACHER'S READ",
        "LEARNING SIGNAL", "Next question", "The teacher is listening.",
        "Reset visual model", "My prediction", "SUBJECT ROUTES", "Language", "translation beta",
        "evidence", "model", "Explanation", "Question", "Teacher ready", "Experiment",
    ),
    "zh": _pack(
        "选择学习语言", "学院", "课程", "显示英文参考",
        "社区翻译测试版 · 建议由母语者审核", "互动世界实验室", "操控模型，然后用证据说明变化。",
        "通过问题、模型和证据进入《{title}》。", "把你对《{title}》的理解迁移到新情境。",
        "我会关注你在{subject}中的假设与证据，而不只看最终答案。", "围绕《{title}》辅导同学；追问证据和适用边界。",
        "在“{stage}”阶段，模型揭示了《{title}》的什么？", "用“{stage}”连接可视模型、证据和课程问题。",
        "一次只改变一个条件；测试前先写下预测。", "练习任务", "推理信号很强", "推理正在发展",
        "给老师看看你的思考过程", "检查我的推理", "你的思考", "资料来源", "英文参考",
        "参数", "结果", "探究循环", "学习星图", "教练 · 苏格拉底式", "学习 · 可视化",
        "变式 · 练习", "应用 · 角色扮演", "学习工具箱", "当前重点", "老师的观察",
        "学习信号", "下一个问题", "老师正在倾听。", "重置可视模型", "我的预测", "学科路线",
        "语言", "翻译测试版", "证据", "模型", "解释", "问题", "老师已就绪", "实验",
    ),
    "hi": _pack(
        "सीखने की भाषा चुनें", "अकादमी", "पाठ्यक्रम", "अंग्रेज़ी संदर्भ दिखाएँ",
        "सामुदायिक अनुवाद बीटा · मातृभाषी समीक्षा सुझाई गई", "इंटरैक्टिव विश्व प्रयोगशाला",
        "मॉडल बदलें, फिर प्रमाण से बताएं कि क्या बदला।", "प्रश्न, मॉडल और प्रमाण से {title} में प्रवेश करें।",
        "{title} की समझ को नई स्थिति में लागू करें।", "मैं {subject} में केवल उत्तर नहीं, धारणाएँ और प्रमाण देख रहा हूँ।",
        "{title} पर सहपाठी को सिखाएँ; प्रमाण और सीमा पूछें।", "{stage} चरण में मॉडल {title} के बारे में क्या दिखाता है?",
        "दृश्य मॉडल, प्रमाण और पाठ्यक्रम प्रश्न को {stage} से जोड़ें।", "एक बार में एक चीज़ बदलें; जाँच से पहले अनुमान लिखें।",
        "अभ्यास मिशन", "मज़बूत तर्क संकेत", "विकसित होता तर्क संकेत", "शिक्षक को अपनी सोच की झलक दें",
        "मेरे तर्क की जाँच करें", "आपकी सोच", "स्रोत", "अंग्रेज़ी संदर्भ", "पैरामीटर", "परिणाम",
        "जाँच चक्र", "सीखने का तारामंडल", "कोच · सुकराती", "सीखें · दृश्य", "रीमिक्स · अभ्यास",
        "लागू करें · भूमिका", "सीखने की टूलकिट", "वर्तमान केंद्र", "शिक्षक की नज़र", "सीखने का संकेत",
        "अगला प्रश्न", "शिक्षक सुन रहा है।", "दृश्य मॉडल रीसेट करें", "मेरा अनुमान", "विषय मार्ग",
        "भाषा", "अनुवाद बीटा", "प्रमाण", "मॉडल", "व्याख्या", "प्रश्न", "शिक्षक तैयार", "प्रयोग",
    ),
    "es": _pack(
        "Elige el idioma de aprendizaje", "Academia", "Curso", "Mostrar referencia en inglés",
        "Traducción comunitaria beta · se recomienda revisión nativa", "LABORATORIO INTERACTIVO",
        "Manipula el modelo y defiende con evidencia qué cambió.", "Entra en {title} mediante una pregunta, un modelo y evidencia.",
        "Transfiere tu comprensión de {title} a una situación nueva.", "Observo supuestos y evidencia en {subject}, no solo la respuesta final.",
        "Guía a un compañero en {title}; pide evidencia y límites.", "En la etapa {stage}, ¿qué revela el modelo sobre {title}?",
        "Usa {stage} para conectar el modelo visual, la evidencia y la pregunta del curso.",
        "Cambia una cosa cada vez. Predice antes de probar.", "Misión de práctica", "Señal de razonamiento sólida",
        "Señal de razonamiento en desarrollo", "Dale al docente una pista de tu razonamiento", "Comprobar mi razonamiento",
        "Tu razonamiento", "Fuentes", "Referencia en inglés", "Parámetro", "Resultado", "Ciclo de indagación",
        "Constelación de aprendizaje", "Guía · Socrático", "Aprender · Visual", "Remix · Práctica",
        "Aplicar · Rol", "Kit de aprendizaje", "ENFOQUE ACTUAL", "LECTURA DEL DOCENTE", "SEÑAL DE APRENDIZAJE",
        "Siguiente pregunta", "El docente está escuchando.", "Reiniciar modelo visual", "Mi predicción",
        "RUTAS DE MATERIAS", "Idioma", "traducción beta", "evidencia", "modelo", "Explicación", "Pregunta",
        "Docente listo", "Experimento",
    ),
    "ar": _pack(
        "اختر لغة التعلّم", "الأكاديمية", "المقرر", "إظهار المرجع الإنجليزي",
        "ترجمة مجتمعية تجريبية · يُنصح بمراجعة متحدث أصلي", "مختبر العالم التفاعلي",
        "غيّر النموذج ثم فسّر ما تغيّر بالأدلة.", "ادخل إلى {title} عبر سؤال ونموذج ودليل.",
        "انقل فهمك لـ {title} إلى موقف جديد.", "أراقب الافتراضات والأدلة في {subject}، لا الإجابة النهائية فقط.",
        "درّب زميلًا في {title} واطلب الدليل وحدود الفكرة.", "في مرحلة {stage}، ماذا يكشف النموذج عن {title}؟",
        "استخدم {stage} لربط النموذج المرئي والدليل وسؤال المقرر.", "غيّر شيئًا واحدًا كل مرة، واكتب توقعك قبل الاختبار.",
        "مهمة تدريب", "إشارة استدلال قوية", "إشارة استدلال قيد التطور", "أعطِ المعلّم أثرًا من تفكيرك",
        "تحقق من استدلالي", "تفكيرك", "المصادر", "المرجع الإنجليزي", "المعامل", "النتيجة",
        "دورة الاستقصاء", "كوكبة التعلّم", "مدرّب · سقراطي", "تعلّم · بصري", "تنويع · تدريب",
        "تطبيق · لعب أدوار", "أدوات التعلّم", "التركيز الحالي", "قراءة المعلّم", "إشارة التعلّم",
        "السؤال التالي", "المعلّم يستمع.", "إعادة ضبط النموذج المرئي", "توقعي", "مسارات المواد",
        "اللغة", "ترجمة تجريبية", "دليل", "نموذج", "شرح", "سؤال", "المعلّم جاهز", "تجربة",
    ),
    "fr": _pack(
        "Choisir la langue d’apprentissage", "Académie", "Cours", "Afficher la référence anglaise",
        "Traduction communautaire bêta · révision native recommandée", "LABORATOIRE INTERACTIF",
        "Manipulez le modèle, puis justifiez le changement par des preuves.", "Entrez dans {title} par une question, un modèle et des preuves.",
        "Transférez votre compréhension de {title} à une nouvelle situation.", "J’observe les hypothèses et les preuves en {subject}, pas seulement la réponse finale.",
        "Guidez un camarade dans {title} ; demandez des preuves et des limites.", "À l’étape {stage}, que révèle le modèle sur {title} ?",
        "Utilisez {stage} pour relier le modèle visuel, les preuves et la question du cours.",
        "Ne changez qu’un élément à la fois. Prédisez avant de tester.", "Mission d’entraînement", "Signal de raisonnement solide",
        "Signal de raisonnement en progrès", "Donnez au professeur une trace de votre réflexion", "Vérifier mon raisonnement",
        "Votre réflexion", "Sources", "Référence anglaise", "Paramètre", "Résultat", "Cycle d’enquête",
        "Constellation d’apprentissage", "Coach · Socratique", "Apprendre · Visuel", "Remix · Entraînement",
        "Appliquer · Jeu de rôle", "Boîte à outils", "FOCUS ACTUEL", "REGARD DU PROFESSEUR", "SIGNAL D’APPRENTISSAGE",
        "Question suivante", "Le professeur écoute.", "Réinitialiser le modèle", "Ma prédiction", "PARCOURS DE MATIÈRES",
        "Langue", "traduction bêta", "preuve", "modèle", "Explication", "Question", "Professeur prêt", "Expérience",
    ),
}


_PACKS.update({
    "bn": _pack(
        "শেখার ভাষা বেছে নিন", "একাডেমি", "কোর্স", "ইংরেজি রেফারেন্স দেখান",
        "কমিউনিটি অনুবাদ বেটা · মাতৃভাষীর পর্যালোচনা সুপারিশ করা হয়", "ইন্টার‌্যাক্টিভ বিশ্ব ল্যাব",
        "মডেলটি বদলান, তারপর প্রমাণ দিয়ে পরিবর্তনটি ব্যাখ্যা করুন।", "প্রশ্ন, মডেল ও প্রমাণ দিয়ে {title}-এ প্রবেশ করুন।",
        "{title} সম্পর্কে আপনার বোঝাপড়া নতুন পরিস্থিতিতে প্রয়োগ করুন।", "আমি {subject}-এ শুধু উত্তর নয়, অনুমান ও প্রমাণ দেখছি।",
        "{title} নিয়ে সহপাঠীকে শেখান; প্রমাণ ও সীমা জানতে চান।", "{stage} ধাপে মডেলটি {title} সম্পর্কে কী প্রকাশ করে?",
        "দৃশ্য মডেল, প্রমাণ ও কোর্সের প্রশ্নকে {stage} দিয়ে যুক্ত করুন।", "একবারে একটি জিনিস বদলান; পরীক্ষার আগে পূর্বানুমান লিখুন।",
        "অনুশীলন মিশন", "শক্তিশালী যুক্তির সংকেত", "বিকাশমান যুক্তির সংকেত", "শিক্ষককে আপনার চিন্তার একটি চিহ্ন দিন",
        "আমার যুক্তি যাচাই করুন", "আপনার চিন্তা", "উৎস", "ইংরেজি রেফারেন্স", "প্যারামিটার", "ফলাফল",
        "অনুসন্ধান চক্র", "শেখার নক্ষত্রমণ্ডল", "কোচ · সক্রেটীয়", "শিখুন · দৃশ্যমান", "রিমিক্স · অনুশীলন",
        "প্রয়োগ · ভূমিকাভিনয়", "শেখার টুলকিট", "বর্তমান ফোকাস", "শিক্ষকের পর্যবেক্ষণ", "শেখার সংকেত",
        "পরবর্তী প্রশ্ন", "শিক্ষক শুনছেন।", "দৃশ্য মডেল রিসেট করুন", "আমার পূর্বানুমান", "বিষয়ভিত্তিক পথ",
        "ভাষা", "অনুবাদ বেটা", "প্রমাণ", "মডেল", "ব্যাখ্যা", "প্রশ্ন", "শিক্ষক প্রস্তুত", "পরীক্ষা",
    ),
    "pt": _pack(
        "Escolha o idioma de aprendizagem", "Academia", "Curso", "Mostrar referência em inglês",
        "Tradução comunitária beta · recomenda-se revisão nativa", "LABORATÓRIO INTERATIVO",
        "Manipule o modelo e defenda com evidências o que mudou.", "Entre em {title} por uma pergunta, um modelo e evidências.",
        "Transfira sua compreensão de {title} para uma nova situação.", "Observo hipóteses e evidências em {subject}, não apenas a resposta final.",
        "Oriente um colega em {title}; peça evidências e limites.", "Na etapa {stage}, o que o modelo revela sobre {title}?",
        "Use {stage} para ligar o modelo visual, as evidências e a pergunta do curso.", "Mude uma coisa de cada vez. Preveja antes de testar.",
        "Missão de prática", "Sinal de raciocínio forte", "Sinal de raciocínio em desenvolvimento",
        "Dê ao professor um rastro do seu pensamento", "Verificar meu raciocínio", "Seu pensamento", "Fontes",
        "Referência em inglês", "Parâmetro", "Resultado", "Ciclo de investigação", "Constelação de aprendizagem",
        "Mentor · Socrático", "Aprender · Visual", "Remix · Prática", "Aplicar · Dramatização", "Kit de aprendizagem",
        "FOCO ATUAL", "LEITURA DO PROFESSOR", "SINAL DE APRENDIZAGEM", "Próxima pergunta", "O professor está ouvindo.",
        "Redefinir modelo visual", "Minha previsão", "ROTAS DE DISCIPLINAS", "Idioma", "tradução beta",
        "evidência", "modelo", "Explicação", "Pergunta", "Professor pronto", "Experimento",
    ),
    "ru": _pack(
        "Выберите язык обучения", "Академия", "Курс", "Показать справку на английском",
        "Бета-перевод сообщества · рекомендуется проверка носителем", "ИНТЕРАКТИВНАЯ ЛАБОРАТОРИЯ",
        "Измените модель и докажите, что именно изменилось.", "Войдите в тему «{title}» через вопрос, модель и доказательства.",
        "Перенесите понимание темы «{title}» в новую ситуацию.", "В {subject} я слежу за допущениями и доказательствами, а не только за ответом.",
        "Помогите однокласснику с темой «{title}»; спросите о доказательствах и границах.",
        "На этапе «{stage}» что модель показывает о теме «{title}»?", "Свяжите на этапе «{stage}» визуальную модель, доказательства и вопрос курса.",
        "Меняйте по одному условию. До проверки запишите прогноз.", "Практическая миссия", "Сильный сигнал рассуждения",
        "Развивающийся сигнал рассуждения", "Покажите учителю ход своей мысли", "Проверить моё рассуждение",
        "Ваши мысли", "Источники", "Справка на английском", "Параметр", "Результат", "Цикл исследования",
        "Созвездие обучения", "Наставник · Сократический", "Изучение · Наглядно", "Ремикс · Практика",
        "Применение · Ролевая игра", "Набор инструментов", "ТЕКУЩИЙ ФОКУС", "ВЗГЛЯД УЧИТЕЛЯ",
        "СИГНАЛ ОБУЧЕНИЯ", "Следующий вопрос", "Учитель слушает.", "Сбросить визуальную модель", "Мой прогноз",
        "МАРШРУТЫ ПРЕДМЕТОВ", "Язык", "бета-перевод", "доказательство", "модель", "Объяснение", "Вопрос",
        "Учитель готов", "Эксперимент",
    ),
    "id": _pack(
        "Pilih bahasa belajar", "Akademi", "Kursus", "Tampilkan rujukan bahasa Inggris",
        "Terjemahan komunitas beta · disarankan tinjauan penutur asli", "LAB DUNIA INTERAKTIF",
        "Ubah model, lalu buktikan apa yang berubah.", "Masuki {title} melalui pertanyaan, model, dan bukti.",
        "Terapkan pemahaman {title} pada situasi baru.", "Saya mengamati asumsi dan bukti dalam {subject}, bukan hanya jawaban akhir.",
        "Bimbing teman dalam {title}; mintalah bukti dan batasannya.", "Pada tahap {stage}, apa yang diungkap model tentang {title}?",
        "Gunakan {stage} untuk menghubungkan model visual, bukti, dan pertanyaan kursus.", "Ubah satu hal setiap kali; tulis prediksi sebelum menguji.",
        "Misi latihan", "Sinyal penalaran kuat", "Sinyal penalaran berkembang", "Berikan jejak pemikiranmu kepada guru",
        "Periksa penalaran saya", "Pemikiranmu", "Sumber", "Rujukan bahasa Inggris", "Parameter", "Hasil",
        "Siklus penyelidikan", "Konstelasi belajar", "Pelatih · Sokratik", "Belajar · Visual", "Remix · Latihan",
        "Terapkan · Bermain peran", "Perangkat belajar", "FOKUS SAAT INI", "PANDANGAN GURU", "SINYAL BELAJAR",
        "Pertanyaan berikutnya", "Guru sedang mendengarkan.", "Atur ulang model visual", "Prediksi saya", "RUTE MATA PELAJARAN",
        "Bahasa", "terjemahan beta", "bukti", "model", "Penjelasan", "Pertanyaan", "Guru siap", "Eksperimen",
    ),
    "ur": _pack(
        "سیکھنے کی زبان منتخب کریں", "اکیڈمی", "کورس", "انگریزی حوالہ دکھائیں",
        "کمیونٹی ترجمہ بیٹا · مادری زبان کے ماہر سے جائزہ تجویز کیا جاتا ہے", "تعاملی عالمی تجربہ گاہ",
        "ماڈل بدلیں، پھر ثبوت سے بتائیں کہ کیا بدلا۔", "سوال، ماڈل اور ثبوت کے ذریعے {title} میں داخل ہوں۔",
        "{title} کی سمجھ کو نئی صورتِ حال میں منتقل کریں۔", "میں {subject} میں صرف آخری جواب نہیں، مفروضے اور ثبوت دیکھ رہا ہوں۔",
        "{title} میں ہم جماعت کی رہنمائی کریں؛ ثبوت اور حدود پوچھیں۔", "{stage} مرحلے میں ماڈل {title} کے بارے میں کیا دکھاتا ہے؟",
        "{stage} کے ذریعے بصری ماڈل، ثبوت اور کورس کے سوال کو جوڑیں۔", "ایک وقت میں ایک چیز بدلیں؛ آزمائش سے پہلے پیش گوئی لکھیں۔",
        "مشق کا مشن", "مضبوط استدلالی اشارہ", "ترقی پذیر استدلالی اشارہ", "استاد کو اپنی سوچ کا سراغ دیں",
        "میرے استدلال کی جانچ کریں", "آپ کی سوچ", "ذرائع", "انگریزی حوالہ", "پیرامیٹر", "نتیجہ",
        "تحقیقی چکر", "سیکھنے کا جھرمٹ", "کوچ · سقراطی", "سیکھیں · بصری", "ری مکس · مشق",
        "اطلاق · کردار", "سیکھنے کے اوزار", "موجودہ توجہ", "استاد کی نظر", "سیکھنے کا اشارہ",
        "اگلا سوال", "استاد سن رہا ہے۔", "بصری ماڈل دوبارہ سیٹ کریں", "میری پیش گوئی", "مضامین کے راستے",
        "زبان", "ترجمہ بیٹا", "ثبوت", "ماڈل", "وضاحت", "سوال", "استاد تیار", "تجربہ",
    ),
    "de": _pack(
        "Lernsprache wählen", "Akademie", "Kurs", "Englische Referenz anzeigen",
        "Community-Übersetzung Beta · Prüfung durch Muttersprachler empfohlen", "INTERAKTIVES WELTLABOR",
        "Verändere das Modell und belege, was sich geändert hat.", "Erschließe {title} durch eine Frage, ein Modell und Belege.",
        "Übertrage dein Verständnis von {title} auf eine neue Situation.", "Ich achte in {subject} auf Annahmen und Belege, nicht nur auf die Endantwort.",
        "Begleite einen Mitschüler durch {title}; frage nach Belegen und Grenzen.", "Was zeigt das Modell in der Phase {stage} über {title}?",
        "Verbinde mit {stage} das visuelle Modell, die Belege und die Kursfrage.", "Ändere immer nur eine Sache. Sage vor dem Test voraus, was passiert.",
        "Übungsmission", "Starkes Denksignal", "Sich entwickelndes Denksignal", "Gib der Lehrkraft eine Spur deines Denkens",
        "Meine Überlegung prüfen", "Deine Gedanken", "Quellen", "Englische Referenz", "Parameter", "Ergebnis",
        "Forschungszyklus", "Lernkonstellation", "Coach · Sokratisch", "Lernen · Visuell", "Remix · Übung",
        "Anwenden · Rollenspiel", "Lernwerkzeuge", "AKTUELLER FOKUS", "BLICK DER LEHRKRAFT", "LERNSIGNAL",
        "Nächste Frage", "Die Lehrkraft hört zu.", "Visuelles Modell zurücksetzen", "Meine Vorhersage", "FÄCHERROUTEN",
        "Sprache", "Übersetzung Beta", "Beleg", "Modell", "Erklärung", "Frage", "Lehrkraft bereit", "Experiment",
    ),
    "ja": _pack(
        "学習言語を選ぶ", "アカデミー", "コース", "英語の参照を表示",
        "コミュニティ翻訳ベータ · 母語話者による確認を推奨", "インタラクティブ世界ラボ",
        "モデルを操作し、何が変わったかを証拠で説明しよう。", "問い・モデル・証拠から「{title}」を探究しよう。",
        "「{title}」の理解を新しい状況に応用しよう。", "{subject}では最終回答だけでなく、仮定と証拠に注目します。",
        "「{title}」について仲間を導き、証拠と限界を尋ねよう。", "「{stage}」の段階で、モデルは「{title}」について何を示す？",
        "「{stage}」を使って視覚モデル、証拠、コースの問いを結びつけよう。", "一度に一つだけ変え、試す前に予測を書こう。",
        "練習ミッション", "強い推論のシグナル", "発展中の推論シグナル", "先生に思考の跡を見せよう",
        "推論を確認する", "あなたの考え", "出典", "英語の参照", "パラメータ", "結果",
        "探究サイクル", "学習コンステレーション", "コーチ · 問答式", "学ぶ · ビジュアル", "リミックス · 練習",
        "応用 · ロールプレイ", "学習ツールキット", "現在の焦点", "先生の見立て", "学習シグナル",
        "次の問い", "先生が聞いています。", "視覚モデルをリセット", "私の予測", "教科ルート",
        "言語", "翻訳ベータ", "証拠", "モデル", "説明", "問い", "先生の準備完了", "実験",
    ),
})


_COURSE_ORDER: tuple[str, ...] = (
    "math-patterns", "physics-flight", "biology-code", "earth-carbon", "cs-networks",
    "history-sources", "literature-motifs", "civics-information", "ethics-decisions",
)


def _labels(*values: tuple[str, str]) -> tuple[tuple[str, str], ...]:
    if len(values) != len(_COURSE_ORDER):
        raise ValueError(f"Course label pack has {len(values)} values; expected {len(_COURSE_ORDER)}")
    return values


_COURSE_LABELS: dict[str, tuple[tuple[str, str], ...]] = {
    "en": _labels(
        ("Mathematics", "Functions in Motion"), ("Physics", "Motion in 3D"),
        ("Biology", "DNA → Protein"), ("Earth & Climate Science", "The Living Carbon Cycle"),
        ("Computer Science", "Algorithms as Paths"), ("History", "History as Evidence"),
        ("Literature", "Narrative & Motif"), ("Civics & Media Literacy", "Civic Claims Lab"),
        ("Philosophy & Ethics", "Ethical Trade-offs"),
    ),
    "zh": _labels(
        ("数学", "运动中的函数"), ("物理", "三维运动"), ("生物学", "DNA → 蛋白质"),
        ("地球与气候科学", "鲜活的碳循环"), ("计算机科学", "作为路径的算法"),
        ("历史", "作为证据的历史"), ("文学", "叙事与母题"), ("公民与媒体素养", "公共主张实验室"),
        ("哲学与伦理", "伦理权衡"),
    ),
    "hi": _labels(
        ("गणित", "गतिशील फलन"), ("भौतिकी", "त्रिविमीय गति"), ("जीवविज्ञान", "DNA → प्रोटीन"),
        ("पृथ्वी और जलवायु विज्ञान", "सजीव कार्बन चक्र"), ("कंप्यूटर विज्ञान", "पथ के रूप में एल्गोरिदम"),
        ("इतिहास", "प्रमाण के रूप में इतिहास"), ("साहित्य", "कथा और रूपक"),
        ("नागरिक शास्त्र और मीडिया साक्षरता", "नागरिक दावे प्रयोगशाला"), ("दर्शन और नैतिकता", "नैतिक समझौते"),
    ),
    "es": _labels(
        ("Matemáticas", "Funciones en movimiento"), ("Física", "Movimiento en 3D"),
        ("Biología", "ADN → Proteína"), ("Ciencias de la Tierra y el clima", "El ciclo vivo del carbono"),
        ("Informática", "Algoritmos como caminos"), ("Historia", "La historia como evidencia"),
        ("Literatura", "Narrativa y motivo"), ("Cívica y alfabetización mediática", "Laboratorio de afirmaciones cívicas"),
        ("Filosofía y ética", "Dilemas éticos"),
    ),
    "ar": _labels(
        ("الرياضيات", "الدوال في حركة"), ("الفيزياء", "الحركة ثلاثية الأبعاد"),
        ("الأحياء", "DNA → البروتين"), ("علوم الأرض والمناخ", "دورة الكربون الحية"),
        ("علوم الحاسوب", "الخوارزميات بوصفها مسارات"), ("التاريخ", "التاريخ بوصفه دليلًا"),
        ("الأدب", "السرد والثيمة"), ("التربية المدنية ومحو الأمية الإعلامية", "مختبر الادعاءات المدنية"),
        ("الفلسفة والأخلاق", "المفاضلات الأخلاقية"),
    ),
    "fr": _labels(
        ("Mathématiques", "Fonctions en mouvement"), ("Physique", "Mouvement en 3D"),
        ("Biologie", "ADN → Protéine"), ("Sciences de la Terre et du climat", "Le cycle vivant du carbone"),
        ("Informatique", "Les algorithmes comme chemins"), ("Histoire", "L’histoire comme preuve"),
        ("Littérature", "Récit et motif"), ("Éducation civique et médias", "Laboratoire des affirmations civiques"),
        ("Philosophie et éthique", "Arbitrages éthiques"),
    ),
    "bn": _labels(
        ("গণিত", "গতিশীল ফাংশন"), ("পদার্থবিজ্ঞান", "ত্রিমাত্রিক গতি"), ("জীববিজ্ঞান", "DNA → প্রোটিন"),
        ("পৃথিবী ও জলবায়ু বিজ্ঞান", "জীবন্ত কার্বন চক্র"), ("কম্পিউটার বিজ্ঞান", "পথ হিসেবে অ্যালগরিদম"),
        ("ইতিহাস", "প্রমাণ হিসেবে ইতিহাস"), ("সাহিত্য", "আখ্যান ও মোটিফ"),
        ("নাগরিকতা ও গণমাধ্যম সাক্ষরতা", "নাগরিক দাবি ল্যাব"), ("দর্শন ও নৈতিকতা", "নৈতিক সমঝোতা"),
    ),
    "pt": _labels(
        ("Matemática", "Funções em movimento"), ("Física", "Movimento em 3D"),
        ("Biologia", "DNA → Proteína"), ("Ciências da Terra e do clima", "O ciclo vivo do carbono"),
        ("Ciência da computação", "Algoritmos como caminhos"), ("História", "História como evidência"),
        ("Literatura", "Narrativa e motivo"), ("Cidadania e letramento midiático", "Laboratório de alegações cívicas"),
        ("Filosofia e ética", "Escolhas éticas"),
    ),
    "ru": _labels(
        ("Математика", "Функции в движении"), ("Физика", "Движение в 3D"),
        ("Биология", "ДНК → Белок"), ("Науки о Земле и климате", "Живой цикл углерода"),
        ("Информатика", "Алгоритмы как пути"), ("История", "История как доказательство"),
        ("Литература", "Повествование и мотив"), ("Граждановедение и медиаграмотность", "Лаборатория гражданских утверждений"),
        ("Философия и этика", "Этические компромиссы"),
    ),
    "id": _labels(
        ("Matematika", "Fungsi dalam gerak"), ("Fisika", "Gerak 3D"), ("Biologi", "DNA → Protein"),
        ("Ilmu bumi dan iklim", "Siklus karbon yang hidup"), ("Ilmu komputer", "Algoritma sebagai jalur"),
        ("Sejarah", "Sejarah sebagai bukti"), ("Sastra", "Narasi dan motif"),
        ("Kewarganegaraan dan literasi media", "Lab klaim sipil"), ("Filsafat dan etika", "Pertukaran etis"),
    ),
}


_COURSE_LABELS.update({
    "ur": _labels(
        ("ریاضی", "متحرک افعال"), ("طبیعیات", "تین جہتی حرکت"), ("حیاتیات", "DNA → پروٹین"),
        ("ارضی و موسمیاتی سائنس", "زندہ کاربن چکر"), ("کمپیوٹر سائنس", "راستوں کی صورت الگورتھم"),
        ("تاریخ", "ثبوت کی صورت تاریخ"), ("ادب", "بیانیہ اور علامتی نمونہ"),
        ("شہریات اور میڈیا خواندگی", "شہری دعووں کی تجربہ گاہ"), ("فلسفہ اور اخلاقیات", "اخلاقی سمجھوتے"),
    ),
    "de": _labels(
        ("Mathematik", "Funktionen in Bewegung"), ("Physik", "Bewegung in 3D"),
        ("Biologie", "DNA → Protein"), ("Erd- und Klimawissenschaft", "Der lebendige Kohlenstoffkreislauf"),
        ("Informatik", "Algorithmen als Wege"), ("Geschichte", "Geschichte als Beleg"),
        ("Literatur", "Erzählung und Motiv"), ("Politische Bildung und Medienkompetenz", "Labor für gesellschaftliche Behauptungen"),
        ("Philosophie und Ethik", "Ethische Abwägungen"),
    ),
    "ja": _labels(
        ("数学", "動く関数"), ("物理", "3次元の運動"), ("生物学", "DNA → タンパク質"),
        ("地球・気候科学", "生きた炭素循環"), ("コンピュータ科学", "経路としてのアルゴリズム"),
        ("歴史", "証拠としての歴史"), ("文学", "物語とモチーフ"),
        ("公民・メディアリテラシー", "市民的主張ラボ"), ("哲学・倫理", "倫理的なトレードオフ"),
    ),
    "pcm": _labels(
        ("Mathematics", "Functions Wey Dey Move"), ("Physics", "Movement for 3D"),
        ("Biology", "DNA → Protein"), ("Earth and Climate Science", "Di Living Carbon Cycle"),
        ("Computer Science", "Algorithms as Road"), ("History", "History as Evidence"),
        ("Literature", "Story and Motif"), ("Civics and Media Literacy", "Civic Claims Lab"),
        ("Philosophy and Ethics", "Ethical Trade-offs"),
    ),
    "mr": _labels(
        ("गणित", "गतिमान फलने"), ("भौतिकशास्त्र", "त्रिमितीय गती"), ("जीवशास्त्र", "DNA → प्रथिन"),
        ("पृथ्वी आणि हवामान विज्ञान", "सजीव कार्बन चक्र"), ("संगणक विज्ञान", "मार्ग म्हणून अल्गोरिदम"),
        ("इतिहास", "पुरावा म्हणून इतिहास"), ("साहित्य", "कथन आणि आकृतिबंध"),
        ("नागरिकशास्त्र आणि माध्यम साक्षरता", "नागरिक दावे प्रयोगशाळा"), ("तत्त्वज्ञान आणि नीतिशास्त्र", "नैतिक तडजोडी"),
    ),
    "vi": _labels(
        ("Toán học", "Hàm số chuyển động"), ("Vật lý", "Chuyển động 3D"),
        ("Sinh học", "DNA → Protein"), ("Khoa học Trái Đất và khí hậu", "Chu trình carbon sống"),
        ("Khoa học máy tính", "Thuật toán như những con đường"), ("Lịch sử", "Lịch sử như bằng chứng"),
        ("Văn học", "Tự sự và mô-típ"), ("Giáo dục công dân và truyền thông", "Phòng lab tuyên bố công dân"),
        ("Triết học và đạo đức", "Đánh đổi đạo đức"),
    ),
    "te": _labels(
        ("గణితం", "చలనంలో ప్రమేయాలు"), ("భౌతిక శాస్త్రం", "త్రిమితీయ చలనం"),
        ("జీవశాస్త్రం", "DNA → ప్రోటీన్"), ("భూ మరియు వాతావరణ శాస్త్రం", "సజీవ కార్బన్ చక్రం"),
        ("కంప్యూటర్ శాస్త్రం", "మార్గాలుగా అల్గోరిథంలు"), ("చరిత్ర", "ఆధారంగా చరిత్ర"),
        ("సాహిత్యం", "కథనం మరియు మూలాంశం"), ("పౌరశాస్త్రం మరియు మీడియా అక్షరాస్యత", "పౌర వాదనల ప్రయోగశాల"),
        ("తత్వశాస్త్రం మరియు నైతికత", "నైతిక మార్పిడులు"),
    ),
    "tr": _labels(
        ("Matematik", "Hareket hâlindeki fonksiyonlar"), ("Fizik", "3B hareket"),
        ("Biyoloji", "DNA → Protein"), ("Yer ve iklim bilimi", "Yaşayan karbon döngüsü"),
        ("Bilgisayar bilimi", "Yollar olarak algoritmalar"), ("Tarih", "Kanıt olarak tarih"),
        ("Edebiyat", "Anlatı ve motif"), ("Yurttaşlık ve medya okuryazarlığı", "Kamusal iddialar laboratuvarı"),
        ("Felsefe ve etik", "Etik ödünleşimler"),
    ),
    "ro": _labels(
        ("Matematică", "Funcții în mișcare"), ("Fizică", "Mișcare în 3D"),
        ("Biologie", "ADN → Proteină"), ("Științele Pământului și ale climei", "Ciclul viu al carbonului"),
        ("Informatică", "Algoritmi ca trasee"), ("Istorie", "Istoria ca dovadă"),
        ("Literatură", "Narațiune și motiv"), ("Educație civică și alfabetizare media", "Laboratorul afirmațiilor civice"),
        ("Filosofie și etică", "Compromisuri etice"),
    ),
    "yue": _labels(
        ("數學", "郁動中嘅函數"), ("物理", "三維運動"), ("生物學", "DNA → 蛋白質"),
        ("地球同氣候科學", "活生生嘅碳循環"), ("電腦科學", "作為路徑嘅演算法"),
        ("歷史", "作為證據嘅歷史"), ("文學", "敘事同母題"),
        ("公民同媒體素養", "公共主張實驗室"), ("哲學同倫理", "倫理取捨"),
    ),
})


def _six(*values: str) -> tuple[str, ...]:
    if len(values) != 6:
        raise ValueError(f"Stage pack has {len(values)} values; expected 6")
    return values


_STAGES: dict[str, tuple[str, ...]] = {
    "en": _six("Observe", "Investigate", "Model", "Test", "Explain", "Transfer"),
    "zh": _six("观察", "探究", "建模", "测试", "解释", "迁移"),
    "hi": _six("निरीक्षण", "जाँच", "मॉडल", "परीक्षण", "व्याख्या", "अनुप्रयोग"),
    "es": _six("Observar", "Investigar", "Modelar", "Probar", "Explicar", "Transferir"),
    "ar": _six("لاحظ", "استقصِ", "نمذج", "اختبر", "فسّر", "انقل"),
    "fr": _six("Observer", "Explorer", "Modéliser", "Tester", "Expliquer", "Transférer"),
    "bn": _six("পর্যবেক্ষণ", "অনুসন্ধান", "মডেল", "পরীক্ষা", "ব্যাখ্যা", "প্রয়োগ"),
    "pt": _six("Observar", "Investigar", "Modelar", "Testar", "Explicar", "Transferir"),
    "ru": _six("Наблюдение", "Исследование", "Модель", "Проверка", "Объяснение", "Перенос"),
    "id": _six("Amati", "Selidiki", "Modelkan", "Uji", "Jelaskan", "Terapkan"),
    "ur": _six("مشاہدہ", "تحقیق", "ماڈل", "آزمائش", "وضاحت", "منتقلی"),
    "de": _six("Beobachten", "Untersuchen", "Modellieren", "Testen", "Erklären", "Übertragen"),
    "ja": _six("観察", "探究", "モデル化", "検証", "説明", "応用"),
    "pcm": _six("Observe", "Check", "Model", "Test", "Explain", "Carry go"),
    "mr": _six("निरीक्षण", "तपासणी", "प्रतिरूप", "चाचणी", "स्पष्टीकरण", "उपयोजन"),
    "vi": _six("Quan sát", "Khám phá", "Mô hình hóa", "Kiểm thử", "Giải thích", "Vận dụng"),
    "te": _six("గమనించు", "పరిశోధించు", "నమూనా", "పరీక్షించు", "వివరించు", "వర్తించు"),
    "tr": _six("Gözle", "İncele", "Modelle", "Test et", "Açıkla", "Aktar"),
    "ro": _six("Observă", "Investighează", "Modelează", "Testează", "Explică", "Transferă"),
    "yue": _six("觀察", "探究", "建模", "測試", "解釋", "遷移"),
}


_ACADEMY_LABELS: dict[str, tuple[str, str]] = {
    "en": ("STEM Studio", "Human Worlds · Humanities & Society"),
    "zh": ("STEM 探究工坊", "人文世界 · 人文与社会"),
    "hi": ("STEM स्टूडियो", "मानव जगत · मानविकी और समाज"),
    "es": ("Estudio STEM", "Mundos humanos · Humanidades y sociedad"),
    "ar": ("استوديو STEM", "عوالم الإنسان · الإنسانيات والمجتمع"),
    "fr": ("Studio STEM", "Mondes humains · Humanités et société"),
    "bn": ("STEM স্টুডিও", "মানবজগৎ · মানবিক ও সমাজ"),
    "pt": ("Estúdio STEM", "Mundos humanos · Humanidades e sociedade"),
    "ru": ("STEM-студия", "Мир людей · Гуманитарные науки и общество"),
    "id": ("Studio STEM", "Dunia manusia · Humaniora dan masyarakat"),
    "ur": ("STEM اسٹوڈیو", "انسانی دنیا · علومِ انسانی و معاشرہ"),
    "de": ("STEM-Studio", "Menschenwelten · Geisteswissenschaften und Gesellschaft"),
    "ja": ("STEMスタジオ", "人間の世界 · 人文と社会"),
    "pcm": ("STEM Studio", "Human Worlds · Humanities and Society"),
    "mr": ("STEM स्टुडिओ", "मानवी विश्व · मानवविद्या आणि समाज"),
    "vi": ("Studio STEM", "Thế giới con người · Nhân văn và xã hội"),
    "te": ("STEM స్టూడియో", "మానవ ప్రపంచాలు · మానవీయ శాస్త్రాలు మరియు సమాజం"),
    "tr": ("STEM Stüdyosu", "İnsan dünyaları · Beşerî bilimler ve toplum"),
    "ro": ("Studioul STEM", "Lumi umane · Științe umaniste și societate"),
    "yue": ("STEM 探究工房", "人文世界 · 人文同社會"),
}


_REASONING_MARKERS: dict[str, tuple[str, ...]] = {
    "en": ("because", "evidence", "model", "change", "source", "however"),
    "zh": ("因为", "所以", "证据", "模型", "变化", "来源"),
    "hi": ("क्योंकि", "इसलिए", "प्रमाण", "मॉडल", "बदल", "स्रोत"),
    "es": ("porque", "por eso", "evidencia", "modelo", "cambia", "fuente"),
    "ar": ("لأن", "لذلك", "دليل", "نموذج", "تغي", "مصدر"),
    "fr": ("parce que", "donc", "preuve", "modèle", "change", "source"),
    "bn": ("কারণ", "তাই", "প্রমাণ", "মডেল", "পরিবর্ত", "উৎস"),
    "pt": ("porque", "portanto", "evidência", "modelo", "muda", "fonte"),
    "ru": ("потому", "поэтому", "доказ", "модел", "измен", "источник"),
    "id": ("karena", "maka", "bukti", "model", "berubah", "sumber"),
    "ur": ("کیونکہ", "اس لیے", "ثبوت", "ماڈل", "تبدیل", "ذریعہ"),
    "de": ("weil", "deshalb", "beleg", "modell", "änder", "quelle"),
    "ja": ("なぜなら", "だから", "証拠", "モデル", "変化", "出典"),
    "pcm": ("because", "so", "evidence", "model", "change", "source"),
    "mr": ("कारण", "म्हणून", "पुरावा", "मॉडेल", "बदल", "स्रोत"),
    "vi": ("bởi vì", "vì vậy", "bằng chứng", "mô hình", "thay đổi", "nguồn"),
    "te": ("ఎందుకంటే", "అందువల్ల", "ఆధారం", "మోడల్", "మార", "మూలం"),
    "tr": ("çünkü", "bu yüzden", "kanıt", "model", "değiş", "kaynak"),
    "ro": ("deoarece", "pentru că", "dovezi", "model", "schimb", "sursă"),
    "yue": ("因為", "所以", "證據", "模型", "改變", "來源"),
}


def get_languages() -> list[Language]:
    """Return the supported locale catalogue in product display order."""

    return [cast(Language, dict(item)) for item in _LANGUAGES]


def get_language(code: str) -> Language:
    """Resolve a locale code with a safe English fallback."""

    normalized = code.strip().lower().replace("_", "-")
    for item in _LANGUAGES:
        if normalized in {item["code"].lower(), item["bcp47"].lower()}:
            return cast(Language, dict(item))
    return cast(Language, dict(_LANGUAGES[0]))


def language_option(language: Language) -> str:
    """Format one selector option without making English the primary label."""

    native = str(language.get("native_name", "English"))
    english = str(language.get("english_name", native))
    return native if native == english else f"{native} · {english}"


def tr(key: str, code: str = "en") -> str:
    """Translate one stable UI key, falling back to English."""

    locale = get_language(code)["code"]
    return _PACKS.get(locale, _PACKS["en"]).get(key, _PACKS["en"].get(key, key))


def message_keys() -> tuple[str, ...]:
    """Expose the localization contract for coverage tests and extensions."""

    return _MESSAGE_KEYS


def get_stages(code: str = "en") -> tuple[str, ...]:
    locale = get_language(code)["code"]
    return _STAGES.get(locale, _STAGES["en"])


def course_label(course_id: str, code: str = "en") -> tuple[str, str]:
    """Return the localized subject and title for a canonical course ID."""

    locale = get_language(code)["code"]
    try:
        index = _COURSE_ORDER.index(course_id)
    except ValueError:
        return ("", course_id)
    labels = _COURSE_LABELS.get(locale, _COURSE_LABELS["en"])
    return labels[index]


def academy_label(academy_id: str, code: str = "en") -> str:
    locale = get_language(code)["code"]
    labels = _ACADEMY_LABELS.get(locale, _ACADEMY_LABELS["en"])
    return labels[0] if academy_id == "stem" else labels[1]


def academy_description(academy_id: str, code: str = "en") -> str:
    """Create a compact localized description from inspectable concepts."""

    if academy_id == "stem":
        concepts = (tr("model", code), tr("experiment", code), tr("evidence", code))
    else:
        concepts = (tr("question", code), tr("sources", code), tr("explanation", code))
    return " · ".join(concepts)


def get_course_translation(course_id: str, code: str = "en") -> CourseTranslation:
    subject, title = course_label(course_id, code)
    stage = get_stages(code)[0]
    question = tr("node_question", code).format(stage=stage, title=title)
    return {"subject": subject, "title": title, "question": question}


def _localized_steps(
    equation: str,
    description: str,
    question: str,
    hint: str,
    code: str,
) -> tuple[tuple[str, str, str], ...]:
    return (
        (tr("model", code), equation, description),
        (tr("evidence", code), question, hint),
        (tr("experiment", code), equation, tr("node_hint", code)),
    )


_LOCALIZED_NODE_SCHEMATICS: dict[str, tuple[str, ...]] = {
    "math-patterns": (
        "z = A·sin(fx)·cos(fy)",
        "y = 0 ⇒ z = A·sin(fx)",
        "A ↑ ⇒ |z|ₘₐₓ ↑",
        "T = 2π/f",
        "z/A = sin(fx)·cos(fy)",
        "Σ → f(x,y) → ŷ",
    ),
    "physics-flight": (
        "r(t) = ⟨x(t), y(t), z(t)⟩",
        "v₀ = ⟨v·cosθ, w, v·sinθ⟩",
        "z(t) = v₀z·t − ½gt²",
        "θ × ‖v₀‖ × g",
        "Fᵣ ≈ 0",
        "C → M → Δ",
    ),
    "biology-code": (
        "A↔T   C↔G",
        "D₁ → D₂",
        "D → R",
        "R → P",
        "Δb → Δc → ΔP",
        "3D ↔ {D,R} ↔ P",
    ),
    "earth-carbon": (
        "Cₐ ↔ Cₗ ↔ Cₒ ↔ Cᵣ",
        "C₁ → Φ → C₂",
        "ΔC = ΣΦᵢₙ − ΣΦₒᵤₜ",
        "τ₁ ≪ τ₂",
        "ΔT ↑ → Φₒ ↑ → ΔT ↑",
        "I × S × τ × κ",
    ),
    "cs-networks": (
        "G = (V, E)",
        "Fₜ = {v₁, …, vₙ}",
        "Q = [v₁, v₂, …, vₙ] → v₁",
        "S = [v₁, v₂, …, vₙ] → vₙ",
        "V✓ ⊆ V",
        "A* = argmin C(A | G)",
    ),
    "history-sources": (
        "⌕ → ?",
        "S = (c, a, t)",
        "p(S) ≠ ¬S",
        "S₁ ⇄ S₂ ⇄ S₃",
        "t₀ + Δ + Ω → t₁",
        "∴ ⇐ {S₁, S₂, …, Sₙ}",
    ),
    "literature-motifs": (
        "{x₁, x₂, x₃} → M(t)",
        "M₁ → M₂ → … → Mₙ",
        "L(t) ↔ A(t) ↔ O(t)",
        "M₁ ≠ M₂",
        "M(t) + ΔM + Ω",
        "E | L₁ ⇄ L₂",
    ),
    "civics-information": (
        "C → E?",
        "P → R → D",
        "S = (a, t, m, n)",
        "E₁ ⫫ E₂",
        "✓ / ? / ×",
        "C + S + K + U",
    ),
    "ethics-decisions": (
        "D → {Pᵢ} → {Iᵢ}",
        "Σ pᵢ·mᵢ·dᵢ",
        "∃C: D ∉ C",
        "Ω ↔ □ ↔ ◇",
        "K + ¬K + R",
        "D + R + O + L",
    ),
}


_LOCALIZED_PRACTICE_SCHEMATICS: dict[str, tuple[str, ...]] = {
    "math-patterns": ("z = 2sin(3x)cos(3y)", "z/A = sin(fx)cos(fy)", "A=?, f=?"),
    "physics-flight": ("v=20 m/s, θ=30°", "g₁=9.81; g₂=1.62", "hᵦ=8 m; 28 m≤xₜ≤34 m"),
    "biology-code": ("D: A C T G", "D → R → P", "GAA → GAG"),
    "earth-carbon": ("C₁ ⇄ C₂", "τ₁ ≪ τ₂", "Φₑ ↓ + Φₛ ↑"),
    "cs-networks": ("A→{B,C}; B→D; C→E", "A→B→C→A", "argmin d(s,g), w(e)=1"),
    "history-sources": ("S₁(t₀)", "S₁ + S₂ + S₃", "{Sᵢ | 1848≤tᵢ≤1920}"),
    "literature-motifs": ("M₁(t)", "M₂(t)", "H: M=f(p)"),
    "civics-information": ("∀x: P(x)", "P₁…P₅ → E₁", "Eₚ + ΔS"),
    "ethics-decisions": ("D: {P₁, …, Pₙ}", "U↑ ∧ C✕", "p≪1; |H|≫1; ρ=0"),
}


def _localized_schematic(course_id: str, index: int, *, practice: bool = False) -> str:
    """Return notation that remains useful without leaking one spoken language."""

    catalogue = _LOCALIZED_PRACTICE_SCHEMATICS if practice else _LOCALIZED_NODE_SCHEMATICS
    schematics = catalogue.get(course_id, ())
    if index < len(schematics):
        return schematics[index]
    return f"M{index + 1}"


def localize_course(course: Mapping[str, Any], code: str = "en") -> dict[str, Any]:
    """Build a localized presentation copy without mutating canonical data.

    Non-English learning prompts use course-specific names plus a common
    evidence cycle.  Canonical equations, identifiers, answer keys, visual-lab
    kinds, and URLs stay untouched and can be shown as an English reference.
    """

    localized = copy.deepcopy(dict(course))
    locale = get_language(code)["code"]
    if locale == "en":
        return localized

    course_id = str(course.get("id", ""))
    translation = get_course_translation(course_id, locale)
    subject = translation["subject"]
    title = translation["title"]
    stages = get_stages(locale)
    localized["subject"] = subject
    localized["title"] = title
    localized["subtitle"] = tr("course_invite", locale).format(title=title)
    localized["big_question"] = translation["question"]
    localized["misconception"] = tr("teacher_watch", locale).format(subject=subject)
    localized["transfer_prompt"] = tr("transfer", locale).format(title=title)
    localized["roleplay_prompt"] = tr("roleplay", locale).format(title=title)

    localized_path: list[dict[str, Any]] = []
    raw_path = course.get("path", [])
    if isinstance(raw_path, (list, tuple)):
        for index, item in enumerate(raw_path):
            if not isinstance(item, Mapping):
                continue
            node = copy.deepcopy(dict(item))
            stage = stages[index % len(stages)]
            question = tr("node_question", locale).format(stage=stage, title=title)
            description = tr("node_description", locale).format(stage=stage, title=title)
            hint = tr("node_hint", locale)
            equation = _localized_schematic(course_id, index)
            node["short"] = stage
            node["label"] = stage
            node["equation"] = equation
            node["question"] = question
            node["description"] = description
            node["hint"] = hint
            node["explain_steps"] = _localized_steps(
                equation, description, question, hint, locale
            )
            localized_path.append(node)
    localized["path"] = localized_path

    localized_practice: list[dict[str, Any]] = []
    raw_practice = course.get("practice", [])
    if isinstance(raw_practice, (list, tuple)):
        for index, item in enumerate(raw_practice):
            if not isinstance(item, Mapping):
                continue
            practice = copy.deepcopy(dict(item))
            stage = stages[(index + 2) % len(stages)]
            practice["title"] = f"{tr('practice_question', locale)} {index + 1} · {stage}"
            practice["equation"] = _localized_schematic(course_id, index, practice=True)
            practice["question"] = tr("node_question", locale).format(stage=stage, title=title)
            practice["skill"] = stage
            practice["transfer"] = tr("transfer", locale).format(title=title)
            practice["hint_ladder"] = [
                tr("node_hint", locale),
                tr("node_description", locale).format(stage=stage, title=title),
                tr("course_invite", locale).format(title=title),
            ]
            practice["explanation"] = tr("node_description", locale).format(stage=stage, title=title)
            localized_practice.append(practice)
    localized["practice"] = localized_practice

    localized_cards: list[dict[str, str]] = []
    raw_cards = course.get("flashcards", [])
    if isinstance(raw_cards, (list, tuple)):
        for index, item in enumerate(raw_cards):
            if not isinstance(item, Mapping):
                continue
            stage = stages[index % len(stages)]
            localized_cards.append(
                {
                    "front": f"{tr('question', locale)} · {stage} · {title}",
                    "back": tr("node_description", locale).format(stage=stage, title=title),
                }
            )
    localized["flashcards"] = localized_cards

    localized_sources: list[dict[str, str]] = []
    raw_sources = course.get("sources", [])
    if isinstance(raw_sources, (list, tuple)):
        for index, item in enumerate(raw_sources, start=1):
            if not isinstance(item, Mapping):
                continue
            source = {str(key): str(value) for key, value in item.items()}
            source["label"] = f"{tr('sources', locale)} {index} · {title}"
            source["supports"] = f"{tr('evidence', locale).capitalize()} · {title}"
            localized_sources.append(source)
    localized["sources"] = localized_sources
    return localized


def reasoning_signals(answer: str, code: str = "en") -> list[str]:
    """Find visible reasoning connectors without claiming semantic correctness."""

    locale = get_language(code)["code"]
    text = answer.casefold()
    return [marker for marker in _REASONING_MARKERS.get(locale, _REASONING_MARKERS["en"]) if marker.casefold() in text]


def answer_extent(answer: str, code: str = "en") -> int:
    """Measure response effort fairly across spaced and unspaced scripts."""

    locale = get_language(code)["code"]
    if locale in {"zh", "ja", "yue"}:
        return sum(1 for char in answer if not char.isspace() and not unicodedata.category(char).startswith(("P", "S")))
    return len([token for token in answer.strip().split() if token])


def is_rtl(code: str = "en") -> bool:
    return get_language(code)["direction"] == "rtl"


__all__ = [
    "Language",
    "academy_description",
    "academy_label",
    "answer_extent",
    "course_label",
    "get_course_translation",
    "get_language",
    "get_languages",
    "get_stages",
    "is_rtl",
    "language_option",
    "localize_course",
    "message_keys",
    "reasoning_signals",
    "tr",
]


_PACKS.update({
    "pcm": _pack(
        "Choose language wey you wan take learn", "Akademi", "Kos", "Show English reference",
        "Community translation beta · make native speaker review am", "INTERACTIVE WORLD LAB",
        "Change di model, den use evidence explain wetin change.", "Enter {title} through question, model and evidence.",
        "Carry wetin you understand for {title} enter new situation.", "I dey check assumption and evidence for {subject}, no be only final answer.",
        "Coach your classmate for {title}; ask for evidence and where di idea stop.", "For {stage} stage, wetin di model show about {title}?",
        "Use {stage} join visual model, evidence and di course question.", "Change one thing at a time; write your prediction before you test am.",
        "Practice mission", "Strong reasoning signal", "Reasoning signal dey grow", "Show di teacher small trace of your thinking",
        "Check my reasoning", "Your thinking", "Sources", "English reference", "Parameter", "Result",
        "Inquiry cycle", "Learning constellation", "Coach · Socratic", "Learn · Visual", "Remix · Practice",
        "Apply · Roleplay", "Learning toolkit", "CURRENT FOCUS", "TEACHER READ", "LEARNING SIGNAL",
        "Next question", "Di teacher dey listen.", "Reset visual model", "My prediction", "SUBJECT ROUTES",
        "Language", "translation beta", "evidence", "model", "Explanation", "Question", "Teacher ready", "Experiment",
    ),
    "mr": _pack(
        "शिकण्याची भाषा निवडा", "अकादमी", "अभ्यासक्रम", "इंग्रजी संदर्भ दाखवा",
        "समुदाय अनुवाद बीटा · मातृभाषिक पुनरावलोकन सुचविले आहे", "परस्परसंवादी विश्व प्रयोगशाळा",
        "मॉडेल बदला आणि पुराव्याने काय बदलले ते स्पष्ट करा.", "प्रश्न, मॉडेल आणि पुराव्यांद्वारे {title} मध्ये प्रवेश करा.",
        "{title} चे आकलन नवीन परिस्थितीत वापरा.", "मी {subject} मध्ये फक्त अंतिम उत्तर नव्हे, तर गृहितके आणि पुरावे पाहतो.",
        "{title} मध्ये वर्गमित्राला मार्गदर्शन करा; पुरावा आणि मर्यादा विचारा.", "{stage} टप्प्यावर मॉडेल {title} बद्दल काय दाखवते?",
        "दृश्य मॉडेल, पुरावा आणि अभ्यासक्रमाचा प्रश्न {stage} द्वारे जोडा.", "एका वेळी एकच गोष्ट बदला; चाचणीपूर्वी अंदाज लिहा.",
        "सराव मोहीम", "मजबूत तर्क संकेत", "विकसित होणारा तर्क संकेत", "शिक्षकाला तुमच्या विचारांची खूण द्या",
        "माझा तर्क तपासा", "तुमचे विचार", "स्रोत", "इंग्रजी संदर्भ", "परिमाण", "परिणाम",
        "चौकशी चक्र", "शिकण्याचे तारामंडळ", "मार्गदर्शक · सॉक्रेटिक", "शिका · दृश्य", "रीमिक्स · सराव",
        "लागू करा · भूमिकानाट्य", "शिकण्याची साधने", "सध्याचा केंद्रबिंदू", "शिक्षकाचे निरीक्षण", "शिकण्याचा संकेत",
        "पुढचा प्रश्न", "शिक्षक ऐकत आहेत.", "दृश्य मॉडेल रीसेट करा", "माझा अंदाज", "विषय मार्ग",
        "भाषा", "अनुवाद बीटा", "पुरावा", "मॉडेल", "स्पष्टीकरण", "प्रश्न", "शिक्षक तयार", "प्रयोग",
    ),
    "vi": _pack(
        "Chọn ngôn ngữ học", "Học viện", "Khóa học", "Hiện tham chiếu tiếng Anh",
        "Bản dịch cộng đồng beta · nên được người bản ngữ duyệt", "PHÒNG THÍ NGHIỆM TƯƠNG TÁC",
        "Thay đổi mô hình rồi dùng bằng chứng để bảo vệ kết luận.", "Bước vào {title} bằng một câu hỏi, mô hình và bằng chứng.",
        "Chuyển hiểu biết về {title} sang một tình huống mới.", "Tôi theo dõi giả định và bằng chứng trong {subject}, không chỉ đáp án cuối.",
        "Hướng dẫn một bạn học về {title}; hỏi về bằng chứng và giới hạn.", "Ở giai đoạn {stage}, mô hình cho thấy gì về {title}?",
        "Dùng {stage} để nối mô hình trực quan, bằng chứng và câu hỏi khóa học.", "Mỗi lần chỉ đổi một yếu tố; hãy dự đoán trước khi thử.",
        "Nhiệm vụ luyện tập", "Tín hiệu lập luận mạnh", "Tín hiệu lập luận đang phát triển", "Cho giáo viên thấy dấu vết suy nghĩ của bạn",
        "Kiểm tra lập luận", "Suy nghĩ của bạn", "Nguồn", "Tham chiếu tiếng Anh", "Tham số", "Kết quả",
        "Chu trình khám phá", "Chòm sao học tập", "Huấn luyện · Socrates", "Học · Trực quan", "Biến thể · Luyện tập",
        "Áp dụng · Nhập vai", "Bộ công cụ học tập", "TRỌNG TÂM HIỆN TẠI", "GÓC NHÌN GIÁO VIÊN", "TÍN HIỆU HỌC TẬP",
        "Câu hỏi tiếp theo", "Giáo viên đang lắng nghe.", "Đặt lại mô hình trực quan", "Dự đoán của tôi", "LỘ TRÌNH MÔN HỌC",
        "Ngôn ngữ", "bản dịch beta", "bằng chứng", "mô hình", "Giải thích", "Câu hỏi", "Giáo viên sẵn sàng", "Thí nghiệm",
    ),
    "te": _pack(
        "నేర్చుకునే భాషను ఎంచుకోండి", "అకాడమీ", "కోర్సు", "ఆంగ్ల సూచనను చూపించు",
        "సముదాయ అనువాద బీటా · మాతృభాషా సమీక్ష సూచించబడింది", "ఇంటరాక్టివ్ ప్రపంచ ప్రయోగశాల",
        "మోడల్‌ను మార్చి, ఏమి మారిందో ఆధారాలతో వివరించండి.", "ప్రశ్న, మోడల్ మరియు ఆధారాల ద్వారా {title} లోకి ప్రవేశించండి.",
        "{title} పై మీ అవగాహనను కొత్త పరిస్థితికి వర్తింపజేయండి.", "నేను {subject} లో తుది జవాబు మాత్రమే కాక, ఊహలు మరియు ఆధారాలను చూస్తాను.",
        "{title} లో సహవిద్యార్థికి మార్గనిర్దేశం చేయండి; ఆధారం మరియు పరిమితి అడగండి.", "{stage} దశలో మోడల్ {title} గురించి ఏమి చూపుతుంది?",
        "దృశ్య మోడల్, ఆధారం మరియు కోర్సు ప్రశ్నను {stage} తో కలపండి.", "ఒకసారి ఒక అంశమే మార్చండి; పరీక్షకు ముందు అంచనా రాయండి.",
        "అభ్యాస మిషన్", "బలమైన తార్కిక సంకేతం", "అభివృద్ధి చెందుతున్న తార్కిక సంకేతం", "ఉపాధ్యాయుడికి మీ ఆలోచన జాడను చూపండి",
        "నా తర్కాన్ని తనిఖీ చేయండి", "మీ ఆలోచన", "మూలాలు", "ఆంగ్ల సూచన", "పరామితి", "ఫలితం",
        "విచారణ చక్రం", "అభ్యాస నక్షత్ర సమూహం", "కోచ్ · సోక్రటిక్", "నేర్చుకోండి · దృశ్య", "రీమిక్స్ · అభ్యాసం",
        "వర్తించు · పాత్రాభినయం", "అభ్యాస సాధనాలు", "ప్రస్తుత దృష్టి", "ఉపాధ్యాయుని పరిశీలన", "అభ్యాస సంకేతం",
        "తదుపరి ప్రశ్న", "ఉపాధ్యాయుడు వింటున్నారు.", "దృశ్య మోడల్‌ను రీసెట్ చేయండి", "నా అంచనా", "విషయ మార్గాలు",
        "భాష", "అనువాద బీటా", "ఆధారం", "మోడల్", "వివరణ", "ప్రశ్న", "ఉపాధ్యాయుడు సిద్ధం", "ప్రయోగం",
    ),
    "tr": _pack(
        "Öğrenme dilini seç", "Akademi", "Ders", "İngilizce başvuruyu göster",
        "Topluluk çevirisi beta · ana dil konuşuru incelemesi önerilir", "ETKİLEŞİMLİ DÜNYA LABORATUVARI",
        "Modeli değiştir, sonra neyin değiştiğini kanıtlarla savun.", "{title} konusuna bir soru, model ve kanıtla gir.",
        "{title} anlayışını yeni bir duruma aktar.", "{subject} alanında yalnızca sonuca değil, varsayımlara ve kanıtlara bakıyorum.",
        "Bir arkadaşına {title} konusunda rehberlik et; kanıt ve sınır iste.", "{stage} aşamasında model {title} hakkında ne gösteriyor?",
        "Görsel modeli, kanıtı ve ders sorusunu {stage} ile bağla.", "Her seferinde tek şeyi değiştir; denemeden önce tahminini yaz.",
        "Alıştırma görevi", "Güçlü akıl yürütme sinyali", "Gelişen akıl yürütme sinyali", "Öğretmene düşüncenden bir iz ver",
        "Akıl yürütmemi kontrol et", "Düşüncen", "Kaynaklar", "İngilizce başvuru", "Parametre", "Sonuç",
        "Araştırma döngüsü", "Öğrenme takımyıldızı", "Koç · Sokratik", "Öğren · Görsel", "Remiks · Alıştırma",
        "Uygula · Rol yapma", "Öğrenme araçları", "GÜNCEL ODAK", "ÖĞRETMENİN BAKIŞI", "ÖĞRENME SİNYALİ",
        "Sonraki soru", "Öğretmen dinliyor.", "Görsel modeli sıfırla", "Tahminim", "DERS ROTALARI",
        "Dil", "çeviri beta", "kanıt", "model", "Açıklama", "Soru", "Öğretmen hazır", "Deney",
    ),
    "ro": _pack(
        "Alege limba de învățare", "Academie", "Curs", "Arată referința în engleză",
        "Traducere comunitară beta · se recomandă revizuirea de către un vorbitor nativ", "LABORATOR INTERACTIV",
        "Modifică modelul, apoi argumentează cu dovezi ce s-a schimbat.", "Explorează {title} printr-o întrebare, un model și dovezi.",
        "Transferă înțelegerea despre {title} într-o situație nouă.", "Urmăresc ipotezele și dovezile din {subject}, nu doar răspunsul final.",
        "Ghidează un coleg prin {title}; cere dovezi și limite.", "În etapa {stage}, ce dezvăluie modelul despre {title}?",
        "Folosește etapa {stage} pentru a conecta modelul vizual, dovezile și întrebarea cursului.", "Schimbă câte un singur lucru. Scrie predicția înainte de testare.",
        "Misiune de practică", "Semnal de raționament puternic", "Semnal de raționament în dezvoltare", "Oferă profesorului o urmă a gândirii tale",
        "Verifică-mi raționamentul", "Gândirea ta", "Surse", "Referință în engleză", "Parametru", "Rezultat",
        "Ciclu de investigație", "Constelație de învățare", "Antrenor · Socratic", "Învață · Vizual", "Variații · Practică",
        "Aplică · Joc de rol", "Instrumente de învățare", "OBIECTIV CURENT", "OBSERVAȚIA PROFESORULUI", "SEMNAL DE ÎNVĂȚARE",
        "Întrebarea următoare", "Profesorul ascultă.", "Resetează modelul vizual", "Predicția mea", "TRASEE DE MATERII",
        "Limbă", "traducere beta", "dovezi", "model", "Explicație", "Întrebare", "Profesor pregătit", "Experiment",
    ),
    "yue": _pack(
        "揀學習語言", "學院", "課程", "顯示英文參考",
        "社群翻譯測試版 · 建議由母語使用者審閱", "互動世界實驗室",
        "郁動個模型，再用證據解釋有咩改變。", "由問題、模型同證據進入《{title}》。",
        "將你對《{title}》嘅理解搬去新情境。", "我會留意你喺{subject}嘅假設同證據，唔只係最後答案。",
        "帶同學學《{title}》；追問證據同適用界線。", "去到「{stage}」階段，模型揭示《{title}》啲咩？",
        "用「{stage}」連接視覺模型、證據同課程問題。", "每次只改一樣；測試之前先寫低預測。",
        "練習任務", "推理訊號好強", "推理訊號發展中", "畀老師睇到你嘅思考痕跡",
        "檢查我嘅推理", "你嘅思考", "資料來源", "英文參考", "參數", "結果",
        "探究循環", "學習星圖", "教練 · 蘇格拉底式", "學習 · 視覺", "變式 · 練習",
        "應用 · 角色扮演", "學習工具箱", "目前重點", "老師嘅觀察", "學習訊號",
        "下一條問題", "老師聽緊。", "重設視覺模型", "我嘅預測", "學科路線",
        "語言", "翻譯測試版", "證據", "模型", "解釋", "問題", "老師準備好", "實驗",
    ),
})
