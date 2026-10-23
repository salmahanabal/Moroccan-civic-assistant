// Tous les textes de l'interface, en français et en arabe (exigence FR-11).
// Pour traduire un nouveau texte, on l'ajoute dans les DEUX langues ci-dessous.

export const translations = {
  fr: {
    dir: 'ltr',
    title: 'Assistant civique marocain',
    subtitle: 'La Constitution, les élections et les institutions, expliquées avec des sources officielles',
    placeholder: 'Posez votre question…',
    send: 'Envoyer',
    welcomeTitle: 'Bonjour, que voulez-vous savoir ?',
    welcomeText:
      'Je réponds uniquement à partir de textes officiels et je cite toujours mes sources. Posez votre question en français ou en arabe.',
    examplesTitle: 'Essayez par exemple :',
    examples: [
      'Qui choisit le chef du gouvernement ?',
      'Combien de juges siègent à la Cour constitutionnelle ?',
      'Faut-il demander la permission pour organiser une réunion publique ?',
      'À quoi servent les partis politiques ?',
    ],
    thinking: "L'assistant réfléchit…",
    sourcesTitle: 'Sources',
    page: 'page',
    openSource: 'Ouvrir le document',
    notFoundLabel: 'Pas dans mes documents',
    languageLabel: 'Langue de l’interface',
    disclaimer:
      'Information indicative issue de textes officiels, à vérifier auprès des institutions compétentes. Cet assistant ne donne aucune opinion politique.',
    errors: {
      network: "Impossible de joindre l'assistant. Vérifiez votre connexion ou réessayez dans un instant.",
      rateLimit: 'Trop de questions en peu de temps. Patientez une minute avant de réessayer.',
      unavailable: "Le service de réponse est momentanément indisponible. Réessayez dans quelques instants.",
      invalid: 'Votre question est vide ou trop longue (500 caractères au maximum).',
      generic: 'Une erreur est survenue. Réessayez dans un instant.',
    },
  },
  ar: {
    dir: 'rtl',
    title: 'المساعد المدني المغربي',
    subtitle: 'الدستور والانتخابات والمؤسسات، مشروحة بمصادر رسمية',
    placeholder: 'اطرح سؤالك…',
    send: 'إرسال',
    welcomeTitle: 'مرحبا، ماذا تريد أن تعرف؟',
    welcomeText: 'أجيب فقط انطلاقا من نصوص رسمية وأذكر دائما مصادري. اطرح سؤالك بالعربية أو بالفرنسية.',
    examplesTitle: 'جرّب مثلا:',
    examples: [
      'ما هي اللغات الرسمية في المغرب؟',
      'كم سنة يُنتخب أعضاء مجلس النواب؟',
      'ما هو دور رئيس الحكومة؟',
      'هل يضمن الدستور حق الإضراب؟',
    ],
    thinking: 'المساعد يفكر…',
    sourcesTitle: 'المصادر',
    page: 'الصفحة',
    openSource: 'فتح الوثيقة',
    notFoundLabel: 'غير موجود في وثائقي',
    languageLabel: 'لغة الواجهة',
    disclaimer:
      'معلومات إرشادية مستمدة من نصوص رسمية، يُرجى التحقق منها لدى المؤسسات المختصة. هذا المساعد لا يبدي أي رأي سياسي.',
    errors: {
      network: 'تعذر الاتصال بالمساعد. تحقق من اتصالك أو أعد المحاولة بعد قليل.',
      rateLimit: 'عدد كبير من الأسئلة في وقت قصير. انتظر دقيقة ثم أعد المحاولة.',
      unavailable: 'خدمة الإجابة غير متاحة مؤقتا. أعد المحاولة بعد قليل.',
      invalid: 'سؤالك فارغ أو طويل جدا (500 حرف كحد أقصى).',
      generic: 'حدث خطأ. أعد المحاولة بعد قليل.',
    },
  },
}
