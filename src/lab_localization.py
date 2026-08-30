"""Locale-complete vocabulary for Canopy's browser-rendered laboratories.

The simulation layer keeps stable English identifiers for deterministic math
and control state.  This module supplies only presentation labels, so changing
language never changes the model itself.
"""

from __future__ import annotations

from src.localization import get_language


_LAB_KEYS: tuple[str, ...] = (
    "original",
    "variant",
    "breadth_first",
    "depth_first",
    "context",
    "purpose",
    "corroboration",
    "include_disagreement",
    "only_supportive",
    "ambition",
    "guilt",
    "disorder",
    "located",
    "missing",
    "predicted_path",
    "landing_point",
    "barrier",
    "target_zone",
    "strand_1",
    "strand_2",
    "complement",
    "selected_pair",
    "atmosphere",
    "plants",
    "soils",
    "surface_ocean",
    "deep_ocean",
    "fossil_stores",
    "rocks_sediments",
    "public_claim",
    "repeated_posts",
    "original_evidence",
    "independent_sources",
    "context_check",
    "supported",
    "uncertain",
    "contradicted",
    "verification_pipeline",
    "broad_deployment",
    "limited_pilot",
    "do_not_deploy",
    "policy_options",
)


def _pack(*values: str) -> dict[str, str]:
    if len(values) != len(_LAB_KEYS):
        raise ValueError(f"Lab locale pack has {len(values)} values; expected {len(_LAB_KEYS)}")
    return dict(zip(_LAB_KEYS, values, strict=True))


_LAB_PACKS: dict[str, dict[str, str]] = {
    "en": _pack(
        "Original", "Variant", "Breadth-first", "Depth-first", "Context", "Purpose", "Corroboration",
        "Include disagreement", "Only supportive", "Ambition", "Guilt", "Disorder", "Located", "Missing",
        "Predicted path", "Landing point", "Barrier", "Target zone", "Strand 1", "Strand 2", "Complement",
        "Selected base pair", "Atmosphere", "Plants", "Soils", "Surface ocean", "Deep ocean", "Fossil stores",
        "Rocks & sediments", "Public claim", "Repeated posts", "Original evidence", "Independent sources",
        "Context check", "Supported", "Uncertain", "Contradicted", "Verification pipeline", "Broad deployment",
        "Limited pilot", "Do not deploy", "Policy options",
    ),
    "zh": _pack(
        "原始", "变体", "广度优先", "深度优先", "背景", "目的", "互证", "包含分歧", "仅保留支持观点", "野心", "罪疚", "失序", "已找到", "缺失",
        "预测路径", "落点", "障碍", "目标区", "链 1", "链 2", "互补链", "选定碱基对", "大气", "植物", "土壤", "表层海洋", "深海", "化石储库",
        "岩石与沉积物", "公共主张", "重复帖文", "原始证据", "独立来源", "背景核查", "有支持", "不确定", "有矛盾", "核验流程", "全面部署", "有限试点", "不部署", "政策选项",
    ),
    "hi": _pack(
        "मूल", "प्रकारांतर", "चौड़ाई-प्रथम", "गहराई-प्रथम", "संदर्भ", "उद्देश्य", "पुष्टिकरण", "असहमति शामिल करें", "केवल समर्थक", "महत्वाकांक्षा", "अपराधबोध", "अव्यवस्था", "मिला", "अनुपलब्ध",
        "अनुमानित पथ", "अवतरण बिंदु", "बाधा", "लक्ष्य क्षेत्र", "श्रृंखला 1", "श्रृंखला 2", "पूरक", "चयनित आधार-युग्म", "वायुमंडल", "पौधे", "मिट्टी", "सतही महासागर", "गहरा महासागर", "जीवाश्म भंडार",
        "चट्टानें व तलछट", "सार्वजनिक दावा", "दोहराई गई पोस्टें", "मूल साक्ष्य", "स्वतंत्र स्रोत", "संदर्भ जाँच", "समर्थित", "अनिश्चित", "खंडित", "सत्यापन प्रवाह", "व्यापक कार्यान्वयन", "सीमित परीक्षण", "लागू न करें", "नीति विकल्प",
    ),
    "es": _pack(
        "Original", "Variante", "Anchura primero", "Profundidad primero", "Contexto", "Propósito", "Corroboración",
        "Incluir desacuerdo", "Solo fuentes favorables", "Ambición", "Culpa", "Desorden", "Localizada", "Ausente",
        "Trayectoria prevista", "Punto de aterrizaje", "Barrera", "Zona objetivo", "Hebra 1", "Hebra 2", "Complementaria",
        "Par de bases seleccionado", "Atmósfera", "Plantas", "Suelos", "Océano superficial", "Océano profundo", "Reservas fósiles",
        "Rocas y sedimentos", "Afirmación pública", "Publicaciones repetidas", "Evidencia original", "Fuentes independientes",
        "Verificación de contexto", "Respaldada", "Incierta", "Refutada", "Flujo de verificación", "Despliegue amplio",
        "Piloto limitado", "No desplegar", "Opciones de política",
    ),
    "ar": _pack(
        "الأصل", "المتغيّر", "البحث بالعرض أولاً", "البحث بالعمق أولاً", "السياق", "الغرض", "التحقق المتقاطع", "تضمين الاختلاف", "المؤيد فقط", "الطموح", "الذنب", "الفوضى", "موجود", "مفقود",
        "المسار المتوقع", "نقطة الهبوط", "حاجز", "منطقة الهدف", "السلسلة 1", "السلسلة 2", "السلسلة المكملة", "زوج القواعد المحدد", "الغلاف الجوي", "النباتات", "التربة", "المحيط السطحي", "المحيط العميق", "مخازن الوقود الأحفوري",
        "الصخور والرواسب", "ادعاء عام", "منشورات مكررة", "الدليل الأصلي", "مصادر مستقلة", "فحص السياق", "مدعوم", "غير مؤكد", "متناقض", "مسار التحقق", "نشر واسع", "تجربة محدودة", "عدم النشر", "خيارات السياسة",
    ),
    "fr": _pack(
        "Original", "Variante", "Parcours en largeur", "Parcours en profondeur", "Contexte", "Intention", "Corroboration",
        "Inclure le désaccord", "Soutiens uniquement", "Ambition", "Culpabilité", "Désordre", "Trouvé", "Manquant",
        "Trajectoire prévue", "Point d’atterrissage", "Barrière", "Zone cible", "Brin 1", "Brin 2", "Complémentaire",
        "Paire de bases sélectionnée", "Atmosphère", "Plantes", "Sols", "Océan de surface", "Océan profond", "Réserves fossiles",
        "Roches et sédiments", "Affirmation publique", "Publications répétées", "Preuve originale", "Sources indépendantes",
        "Vérification du contexte", "Étayée", "Incertaine", "Contredite", "Chaîne de vérification", "Déploiement large",
        "Projet pilote limité", "Ne pas déployer", "Options de politique",
    ),
    "bn": _pack(
        "মূল", "রূপভেদ", "প্রস্থ-প্রথম", "গভীরতা-প্রথম", "প্রেক্ষাপট", "উদ্দেশ্য", "সমর্থন যাচাই", "মতভেদসহ", "শুধু সমর্থনকারী", "উচ্চাকাঙ্ক্ষা", "অপরাধবোধ", "বিশৃঙ্খলা", "পাওয়া গেছে", "অনুপস্থিত",
        "পূর্বানুমিত পথ", "অবতরণ বিন্দু", "বাধা", "লক্ষ্য অঞ্চল", "শৃঙ্খল ১", "শৃঙ্খল ২", "পরিপূরক", "নির্বাচিত বেস জোড়া", "বায়ুমণ্ডল", "উদ্ভিদ", "মাটি", "পৃষ্ঠ মহাসাগর", "গভীর মহাসাগর", "জীবাশ্ম ভান্ডার",
        "শিলা ও পলি", "জনসম্মুখের দাবি", "পুনরাবৃত্ত পোস্ট", "মূল প্রমাণ", "স্বাধীন উৎস", "প্রেক্ষাপট যাচাই", "সমর্থিত", "অনিশ্চিত", "খণ্ডিত", "যাচাই প্রবাহ", "ব্যাপক প্রয়োগ", "সীমিত পরীক্ষামূলক প্রয়োগ", "প্রয়োগ না করা", "নীতি বিকল্প",
    ),
    "pt": _pack(
        "Original", "Variante", "Busca em largura", "Busca em profundidade", "Contexto", "Propósito", "Corroboração",
        "Incluir discordância", "Apenas favoráveis", "Ambição", "Culpa", "Desordem", "Localizado", "Ausente",
        "Trajetória prevista", "Ponto de aterrissagem", "Barreira", "Zona-alvo", "Fita 1", "Fita 2", "Complementar",
        "Par de bases selecionado", "Atmosfera", "Plantas", "Solos", "Oceano superficial", "Oceano profundo", "Reservas fósseis",
        "Rochas e sedimentos", "Alegação pública", "Publicações repetidas", "Evidência original", "Fontes independentes",
        "Verificação de contexto", "Sustentada", "Incerta", "Refutada", "Fluxo de verificação", "Implementação ampla",
        "Projeto-piloto limitado", "Não implementar", "Opções de política",
    ),
    "ru": _pack(
        "Исходный", "Вариант", "Поиск в ширину", "Поиск в глубину", "Контекст", "Цель", "Перекрёстная проверка", "Учитывать несогласие", "Только поддерживающие", "Амбиция", "Вина", "Беспорядок", "Найдено", "Отсутствует",
        "Предсказанная траектория", "Точка приземления", "Препятствие", "Целевая зона", "Цепь 1", "Цепь 2", "Комплементарная цепь", "Выбранная пара оснований", "Атмосфера", "Растения", "Почвы", "Поверхностный океан", "Глубокий океан", "Ископаемые запасы",
        "Породы и осадки", "Публичное утверждение", "Повторные публикации", "Исходное доказательство", "Независимые источники", "Проверка контекста", "Подтверждено", "Неопределённо", "Опровергнуто", "Схема проверки", "Масштабное внедрение", "Ограниченный пилот", "Не внедрять", "Варианты политики",
    ),
    "id": _pack(
        "Asli", "Varian", "Penelusuran melebar", "Penelusuran mendalam", "Konteks", "Tujuan", "Koroborasi",
        "Sertakan perbedaan", "Hanya yang mendukung", "Ambisi", "Rasa bersalah", "Kekacauan", "Ditemukan", "Hilang",
        "Lintasan prediksi", "Titik mendarat", "Penghalang", "Zona target", "Untai 1", "Untai 2", "Pelengkap",
        "Pasangan basa terpilih", "Atmosfer", "Tumbuhan", "Tanah", "Laut permukaan", "Laut dalam", "Cadangan fosil",
        "Batuan dan sedimen", "Klaim publik", "Unggahan berulang", "Bukti asli", "Sumber independen", "Pemeriksaan konteks",
        "Didukung", "Tidak pasti", "Terbantahkan", "Alur verifikasi", "Penerapan luas", "Uji coba terbatas",
        "Jangan diterapkan", "Opsi kebijakan",
    ),
    "ur": _pack(
        "اصل", "متغیر", "چوڑائی-اول تلاش", "گہرائی-اول تلاش", "سیاق", "مقصد", "باہمی تصدیق", "اختلاف شامل کریں", "صرف حمایتی", "عزائم", "احساسِ جرم", "بے ترتیبی", "مل گیا", "غائب",
        "متوقع راستہ", "اترنے کا نقطہ", "رکاوٹ", "ہدفی علاقہ", "زنجیر 1", "زنجیر 2", "تکمیلی", "منتخب اساس جوڑا", "فضا", "پودے", "مٹی", "سطحی سمندر", "گہرا سمندر", "رکازی ذخائر",
        "چٹانیں اور تلچھٹ", "عوامی دعویٰ", "دہرائی گئی پوسٹس", "اصل ثبوت", "آزاد ذرائع", "سیاق کی جانچ", "تائید شدہ", "غیر یقینی", "متضاد", "تصدیقی بہاؤ", "وسیع نفاذ", "محدود آزمائش", "نافذ نہ کریں", "پالیسی اختیارات",
    ),
    "de": _pack(
        "Original", "Variante", "Breitensuche", "Tiefensuche", "Kontext", "Zweck", "Abgleich", "Widerspruch einbeziehen",
        "Nur unterstützend", "Ehrgeiz", "Schuld", "Unordnung", "Gefunden", "Fehlt", "Vorhergesagte Flugbahn",
        "Landepunkt", "Hindernis", "Zielzone", "Strang 1", "Strang 2", "Komplementärstrang", "Ausgewähltes Basenpaar",
        "Atmosphäre", "Pflanzen", "Böden", "Oberflächenozean", "Tiefsee", "Fossile Speicher", "Gesteine und Sedimente",
        "Öffentliche Behauptung", "Wiederholte Beiträge", "Originalbeleg", "Unabhängige Quellen", "Kontextprüfung", "Gestützt",
        "Unsicher", "Widerlegt", "Prüfablauf", "Breite Einführung", "Begrenzter Pilotversuch", "Nicht einführen", "Handlungsoptionen",
    ),
    "ja": _pack(
        "元の配列", "変異", "幅優先探索", "深さ優先探索", "文脈", "目的", "相互検証", "反対意見を含める", "支持資料のみ", "野心", "罪悪感", "秩序の崩壊", "発見済み", "欠落",
        "予測軌道", "着地点", "障害物", "目標区域", "鎖 1", "鎖 2", "相補鎖", "選択した塩基対", "大気", "植物", "土壌", "表層海洋", "深海", "化石貯蔵庫",
        "岩石と堆積物", "公的主張", "繰り返し投稿", "原資料", "独立した情報源", "文脈確認", "支持あり", "不確実", "反証あり", "検証フロー", "全面導入", "限定試行", "導入しない", "政策案",
    ),
    "pcm": _pack(
        "Original", "Variant", "Search level by level", "Search branch reach end", "Context", "Purpose", "Check am with other source",
        "Add disagreement", "Na support only", "Ambition", "Guilt", "Disorder", "We find am", "E no dey",
        "Path we predict", "Where e land", "Barrier", "Target area", "Strand 1", "Strand 2", "Complement",
        "Base pair we select", "Air", "Plants", "Soil", "Sea surface", "Deep sea", "Fossil store", "Rocks and sediment",
        "Public claim", "Posts wey repeat", "Original evidence", "Independent sources", "Check context", "Evidence support am",
        "E never clear", "Evidence oppose am", "Verification flow", "Deploy everywhere", "Small pilot", "No deploy am", "Policy options",
    ),
    "mr": _pack(
        "मूळ", "प्रकारांतर", "रुंदी-प्रथम शोध", "खोली-प्रथम शोध", "संदर्भ", "उद्देश", "पुष्टीकरण", "मतभेद समाविष्ट करा", "फक्त समर्थक", "महत्त्वाकांक्षा", "अपराधभाव", "अव्यवस्था", "सापडले", "अनुपलब्ध",
        "अंदाजित मार्ग", "उतरण्याचा बिंदू", "अडथळा", "लक्ष्य क्षेत्र", "साखळी १", "साखळी २", "पूरक", "निवडलेली आधार-जोडी", "वातावरण", "वनस्पती", "माती", "पृष्ठीय महासागर", "खोल महासागर", "जीवाश्म साठे",
        "खडक व गाळ", "सार्वजनिक दावा", "पुनरावृत्त पोस्ट", "मूळ पुरावा", "स्वतंत्र स्रोत", "संदर्भ तपासणी", "समर्थित", "अनिश्चित", "खंडित", "पडताळणी प्रवाह", "व्यापक अंमलबजावणी", "मर्यादित चाचणी", "अंमलबजावणी करू नका", "धोरण पर्याय",
    ),
    "vi": _pack(
        "Gốc", "Biến thể", "Tìm kiếm theo chiều rộng", "Tìm kiếm theo chiều sâu", "Bối cảnh", "Mục đích", "Đối chứng",
        "Bao gồm bất đồng", "Chỉ nguồn ủng hộ", "Tham vọng", "Tội lỗi", "Rối loạn", "Đã tìm thấy", "Thiếu",
        "Quỹ đạo dự đoán", "Điểm rơi", "Vật cản", "Vùng mục tiêu", "Mạch 1", "Mạch 2", "Bổ sung",
        "Cặp bazơ đã chọn", "Khí quyển", "Thực vật", "Đất", "Đại dương bề mặt", "Đại dương sâu", "Kho nhiên liệu hóa thạch",
        "Đá và trầm tích", "Tuyên bố công khai", "Bài đăng lặp lại", "Bằng chứng gốc", "Nguồn độc lập", "Kiểm tra bối cảnh",
        "Được hỗ trợ", "Chưa chắc chắn", "Bị bác bỏ", "Luồng xác minh", "Triển khai rộng", "Thử nghiệm giới hạn",
        "Không triển khai", "Phương án chính sách",
    ),
    "te": _pack(
        "మూలం", "రూపాంతరం", "వెడల్పు-మొదటి శోధన", "లోతు-మొదటి శోధన", "సందర్భం", "ఉద్దేశ్యం", "పరస్పర ధృవీకరణ", "భిన్నాభిప్రాయాన్ని చేర్చు", "మద్దతు మాత్రమే", "ఆకాంక్ష", "అపరాధభావం", "అస్తవ్యస్తత", "కనుగొనబడింది", "లేదు",
        "అంచనా మార్గం", "దిగిన స్థానం", "అడ్డంకి", "లక్ష్య ప్రాంతం", "శృంఖల 1", "శృంఖల 2", "పూరకం", "ఎంచుకున్న బేస్ జత", "వాతావరణం", "మొక్కలు", "నేలలు", "ఉపరితల సముద్రం", "లోతైన సముద్రం", "శిలాజ నిల్వలు",
        "రాళ్లు మరియు అవక్షేపాలు", "ప్రజా వాదన", "పునరావృత పోస్టులు", "మూల ఆధారం", "స్వతంత్ర మూలాలు", "సందర్భ పరిశీలన", "మద్దతు పొందింది", "అనిశ్చితం", "ఖండించబడింది", "ధృవీకరణ ప్రవాహం", "విస్తృత అమలు", "పరిమిత పైలట్", "అమలు చేయవద్దు", "విధాన ఎంపికలు",
    ),
    "tr": _pack(
        "Özgün", "Varyant", "Genişlik öncelikli", "Derinlik öncelikli", "Bağlam", "Amaç", "Çapraz doğrulama",
        "Görüş ayrılığını dahil et", "Yalnızca destekleyenler", "Hırs", "Suçluluk", "Düzensizlik", "Bulundu", "Eksik",
        "Öngörülen yol", "İniş noktası", "Engel", "Hedef bölge", "Zincir 1", "Zincir 2", "Tamamlayıcı",
        "Seçili baz çifti", "Atmosfer", "Bitkiler", "Topraklar", "Yüzey okyanusu", "Derin okyanus", "Fosil depoları",
        "Kayaçlar ve tortullar", "Kamusal iddia", "Tekrarlanan gönderiler", "Özgün kanıt", "Bağımsız kaynaklar", "Bağlam kontrolü",
        "Destekleniyor", "Belirsiz", "Çürütüldü", "Doğrulama akışı", "Geniş çaplı uygulama", "Sınırlı pilot",
        "Uygulama yapma", "Politika seçenekleri",
    ),
    "ro": _pack(
        "Original", "Variantă", "Căutare în lățime", "Căutare în adâncime", "Context", "Scop", "Coroborare",
        "Include dezacordul", "Doar surse favorabile", "Ambiție", "Vinovăție", "Dezordine", "Găsit", "Lipsește",
        "Traiectorie estimată", "Punct de aterizare", "Barieră", "Zonă-țintă", "Catenă 1", "Catenă 2", "Complementară",
        "Pereche de baze selectată", "Atmosferă", "Plante", "Soluri", "Ocean de suprafață", "Ocean adânc", "Rezerve fosile",
        "Roci și sedimente", "Afirmație publică", "Postări repetate", "Dovadă originală", "Surse independente",
        "Verificarea contextului", "Susținută", "Incertă", "Contrazisă", "Flux de verificare", "Implementare amplă",
        "Proiect-pilot limitat", "Nu implementa", "Opțiuni de politică",
    ),
    "yue": _pack(
        "原始", "變體", "廣度優先搜尋", "深度優先搜尋", "背景", "目的", "互證", "包埋不同意見", "淨係支持觀點", "野心", "罪疚", "失序", "搵到", "缺失",
        "預測路徑", "落點", "障礙", "目標區", "鏈 1", "鏈 2", "互補鏈", "揀選嘅鹼基對", "大氣", "植物", "土壤", "表層海洋", "深海", "化石儲庫",
        "岩石同沉積物", "公開主張", "重複帖文", "原始證據", "獨立來源", "背景核查", "有支持", "唔確定", "有矛盾", "核驗流程", "全面推行", "有限試行", "唔推行", "政策選項",
    ),
}


_OPTION_KEYS: dict[str, str] = {
    "Original": "original",
    "Variant": "variant",
    "Breadth-first": "breadth_first",
    "Depth-first": "depth_first",
    "Context": "context",
    "Purpose": "purpose",
    "Corroboration": "corroboration",
    "Include disagreement": "include_disagreement",
    "Only supportive": "only_supportive",
    "Ambition": "ambition",
    "Guilt": "guilt",
    "Disorder": "disorder",
    "Located": "located",
    "Missing": "missing",
}


def lab_tr(key: str, code: str = "en") -> str:
    """Translate one visual-laboratory term with an explicit English fallback."""

    locale = get_language(code)["code"]
    return _LAB_PACKS.get(locale, _LAB_PACKS["en"]).get(key, _LAB_PACKS["en"].get(key, key))


def lab_option_label(value: object, code: str = "en") -> str:
    """Display a canonical select value without changing its model identifier."""

    canonical = str(value)
    key = _OPTION_KEYS.get(canonical)
    return lab_tr(key, code) if key else canonical


def lab_message_keys() -> tuple[str, ...]:
    """Expose the visual-copy contract for completeness tests."""

    return _LAB_KEYS


__all__ = ["lab_message_keys", "lab_option_label", "lab_tr"]
