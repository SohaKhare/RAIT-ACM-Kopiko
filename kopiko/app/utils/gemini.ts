export const TRANSLATIONS: Record<string, Record<string, string>> = {
  'q1': {
    'en-IN': 'What is the closest mandi to you?',
    'hi-IN': 'आपके सबसे करीब कौन सी मंडी है?',
    'mr-IN': 'तुमच्या सर्वात जवळची बाजार समिती कोणती आहे?',
    'ur-IN': 'آپ کے قریب ترین منڈی کون سی ہے؟',
    'ta-IN': 'உங்களுக்கு மிக அருகில் உள்ள மண்டி எது?'
  },
  'q2': {
    'en-IN': 'Which crop are you growing right now?',
    'hi-IN': 'आप अभी कौन सी फसल उगा रहे हैं?',
    'mr-IN': 'तुम्ही सध्या कोणते पीक घेत आहात?',
    'ur-IN': 'آپ اس وقت کون سی فصل اگا رہے ہیں؟',
    'ta-IN': 'நீங்கள் தற்போது என்ன பயிர் வளர்க்கிறீர்கள்?'
  }
}

export const LANGUAGES = [
  { code: 'en-IN', name: 'English' },
  { code: 'hi-IN', name: 'हिंदी' },
  { code: 'mr-IN', name: 'मराठी' },
  { code: 'ur-IN', name: 'اردو' },
  { code: 'ta-IN', name: 'தமிழ்' }
];

export async function simulateGeminiTranslation(textKey: string, langCode: string): Promise<string> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 600));
  return TRANSLATIONS[textKey]?.[langCode] || TRANSLATIONS[textKey]?.['en-IN'] || 'Translation failed';
}

export const CARD_TRANSLATIONS: Record<string, Record<string, string>> = {
  'select_mandi': {
    'en-IN': 'Select a mandi manually (Optional)',
    'hi-IN': 'मैन्युअल रूप से एक मंडी चुनें (वैकल्पिक)',
    'mr-IN': 'स्वतः एक मंडी निवडा (पर्यायी)',
    'ur-IN': 'دستی طور پر ایک منڈی منتخب کریں (اختیاری)',
    'ta-IN': 'மண்டியை கைமுறையாக தேர்ந்தெடுக்கவும் (விருப்பத்தேர்வு)'
  },
  'mandi_alpha': {
    'en-IN': 'Mandi Alpha',
    'hi-IN': 'मंडी अल्फा',
    'mr-IN': 'मंडी अल्फा',
    'ur-IN': 'منڈی الفا',
    'ta-IN': 'மண்டி ஆல்பா'
  },
  'mandi_beta': {
    'en-IN': 'Mandi Beta',
    'hi-IN': 'मंडी बीटा',
    'mr-IN': 'मंडी बीटा',
    'ur-IN': 'منڈی بیٹا',
    'ta-IN': 'மண்டி பீட்டா'
  },
  'mandi_gamma': {
    'en-IN': 'Mandi Gamma',
    'hi-IN': 'मंडी गामा',
    'mr-IN': 'मंडी गामा',
    'ur-IN': 'منڈی گاما',
    'ta-IN': 'மண்டி காமா'
  },
  'district_average': {
    'en-IN': 'District Average',
    'hi-IN': 'जिला औसत',
    'mr-IN': 'जिल्ह्याची सरासरी',
    'ur-IN': 'ضلعی اوسط',
    'ta-IN': 'மாவட்ட சராசரி'
  },
  'hello': {
    'en-IN': 'Hello',
    'hi-IN': 'नमस्ते',
    'mr-IN': 'नमस्कार',
    'ur-IN': 'ہیلو',
    'ta-IN': 'வணக்கம்'
  },
  'swipe_up': {
    'en-IN': '↑ Swipe up for more stats ↑',
    'hi-IN': '↑ अधिक आँकड़ों के लिए ऊपर स्वाइप करें ↑',
    'mr-IN': '↑ अधिक आकडेवारीसाठी वर स्वाइप करा ↑',
    'ur-IN': '↑ مزید اعدادوشمار کے لیے اوپر سوائپ کریں ↑',
    'ta-IN': '↑ மேலும் புள்ளிவிவரங்களுக்கு மேலே ஸ்வைப் செய்யவும் ↑'
  },
  'swipe_down': {
    'en-IN': '↓ Swipe down to talk again ↓',
    'hi-IN': '↓ फिर से बात करने के लिए नीचे स्वाइप करें ↓',
    'mr-IN': '↓ पुन्हा बोलण्यासाठी खाली स्वाइप करा ↓',
    'ur-IN': '↓ دوبارہ بات کرنے کے لیے نیچے سوائپ کریں ↓',
    'ta-IN': '↓ மீண்டும் பேச கீழே ஸ்வைப் செய்யவும் ↓'
  },
  'advisory_dashboard': {
    'en-IN': 'Advisory Dashboard',
    'hi-IN': 'सलाहकार डैशबोर्ड',
    'mr-IN': 'सल्लागार डॅशबोर्ड',
    'ur-IN': 'مشاورتی ڈیش بورڈ',
    'ta-IN': 'ஆலோசனை டாஷ்போர்டு'
  },
  'groundwater_level': {
    'en-IN': '💧 Groundwater Level',
    'hi-IN': '💧 भूजल स्तर',
    'mr-IN': '💧 भूजल पातळी',
    'ur-IN': '💧 زمینی پانی کی سطح',
    'ta-IN': '💧 நிலத்தடி நீர் மட்டம்'
  },
  'expected_rainfall': {
    'en-IN': '🌧️ Expected Rainfall',
    'hi-IN': '🌧️ अपेक्षित वर्षा',
    'mr-IN': '🌧️ अपेक्षित पाऊस',
    'ur-IN': '🌧️ متوقع بارش',
    'ta-IN': '🌧️ எதிர்பார்க்கப்படும் மழை'
  },
  'price': {
    'en-IN': 'Price',
    'hi-IN': 'कीमत',
    'mr-IN': 'किंमत',
    'ur-IN': 'قیمت',
    'ta-IN': 'விலை'
  },
  'depth': {
    'en-IN': 'depth',
    'hi-IN': 'गहराई',
    'mr-IN': 'खोली',
    'ur-IN': 'گہرائی',
    'ta-IN': 'ஆழம்'
  },
  'stats_speech': {
    'en-IN': 'Your groundwater is at 12 meters, and expected rainfall is 120 millimeters.',
    'hi-IN': 'आपका भूजल 12 मीटर पर है, और अपेक्षित वर्षा 120 मिलीमीटर है।',
    'mr-IN': 'तुमचे भूजल १२ मीटरवर आहे आणि अपेक्षित पाऊस १२० मिलीमीटर आहे.',
    'ur-IN': 'آپ کا زیر زمین پانی 12 میٹر پر ہے، اور متوقع بارش 120 ملی میٹر ہے۔',
    'ta-IN': 'உங்கள் நிலத்தடி நீர் 12 மீட்டரில் உள்ளது, மற்றும் எதிர்பார்க்கப்படும் மழை 120 மில்லிமீட்டர்.'
  },
  'bhoomi_title': {
    'en-IN': 'Bhoomi',
    'hi-IN': 'भूमि',
    'mr-IN': 'भूमी',
    'ur-IN': 'بھومی',
    'ta-IN': 'பூமி'
  },
  'welcome_to_bhoomi': {
    'en-IN': 'Welcome to Bhoomi',
    'hi-IN': 'भूमि में आपका स्वागत है',
    'mr-IN': 'भूमी मध्ये आपले स्वागत आहे',
    'ur-IN': 'بھومی میں خوش آمدید',
    'ta-IN': 'பூமிக்கு உங்களை வரவேற்கிறோம்'
  },
  'tap_mic_to_start': {
    'en-IN': 'Tap the microphone to start',
    'hi-IN': 'शुरू करने के लिए माइक्रोफोन टैप करें',
    'mr-IN': 'सुरू करण्यासाठी मायक्रोफोन टॅप करा',
    'ur-IN': 'شروع کرنے کے لیے مائیکروفون پر ٹیپ کریں',
    'ta-IN': 'தொடங்க மைக்ரோஃபோனைத் தட்டவும்'
  },
  'select_language': {
    'en-IN': 'Select Language',
    'hi-IN': 'भाषा चुनें',
    'mr-IN': 'भाषा निवडा',
    'ur-IN': 'زبان منتخب کریں',
    'ta-IN': 'மொழியைத் தேர்ந்தெடுக்கவும்'
  },
  'tap_to_speak': {
    'en-IN': 'Tap to Speak',
    'hi-IN': 'बोलने के लिए टैप करें',
    'mr-IN': 'बोलण्यासाठी टॅप करा',
    'ur-IN': 'بولنے کے لیے ٹیپ کریں',
    'ta-IN': 'பேச தட்டவும்'
  },
  'tap_to_stop': {
    'en-IN': 'Tap to Stop',
    'hi-IN': 'रोकने के लिए टैप करें',
    'mr-IN': 'थांबवण्यासाठी टॅप करा',
    'ur-IN': 'روکنے کے لیے ٹیپ کریں',
    'ta-IN': 'நிறுத்த தட்டவும்'
  },
  'processing': {
    'en-IN': 'Processing...',
    'hi-IN': 'प्रोसेसिंग...',
    'mr-IN': 'प्रक्रिया करत आहे...',
    'ur-IN': 'پروسیسنگ...',
    'ta-IN': 'செயலாக்குகிறது...'
  },
  'price_forecast': {
    'en-IN': 'Price Trend Forecast',
    'hi-IN': 'मूल्य प्रवृत्ति का अनुमान',
    'mr-IN': 'किंमत अंदाज',
    'ur-IN': 'قیمت کا رجحان',
    'ta-IN': 'விலை போக்கு முன்னறிவிப்பு'
  },
  'next_month': {
    'en-IN': 'Next Month',
    'hi-IN': 'अगला महीना',
    'mr-IN': 'पुढील महिना',
    'ur-IN': 'اگلا مہینہ',
    'ta-IN': 'அடுத்த மாதம்'
  },
  'two_months': {
    'en-IN': 'In 2 Months',
    'hi-IN': '2 महीने में',
    'mr-IN': '२ महिन्यांत',
    'ur-IN': '2 مہینوں میں',
    'ta-IN': '2 மாதங்களில்'
  },
  'three_months': {
    'en-IN': 'In 3 Months',
    'hi-IN': '3 महीने में',
    'mr-IN': '३ महिन्यांत',
    'ur-IN': '3 مہینوں میں',
    'ta-IN': '3 மாதங்களில்'
  },
  'government_msp': {
    'en-IN': 'Government MSP',
    'hi-IN': 'सरकारी एमएसपी (MSP)',
    'mr-IN': 'शासकीय हमीभाव (MSP)',
    'ur-IN': 'سرکاری ایم ایس پی',
    'ta-IN': 'அரசு எம்.எஸ்.பி'
  },
  'above_msp': {
    'en-IN': 'above MSP',
    'hi-IN': 'एमएसपी से ऊपर',
    'mr-IN': 'हमीभावापेक्षा जास्त',
    'ur-IN': 'ایم ایس پی سے زیادہ',
    'ta-IN': 'எம்.எஸ்.பி-க்கு மேல்'
  },
  'below_msp': {
    'en-IN': 'below MSP',
    'hi-IN': 'एमएसपी से कम',
    'mr-IN': 'हमीभावापेक्षा कमी',
    'ur-IN': 'ایم ایس پی سے کم',
    'ta-IN': 'எம்.எஸ்.பி-க்கு கீழ்'
  }
}

export function translateCardText(key: string, langCode: string): string {
  return CARD_TRANSLATIONS[key]?.[langCode] || CARD_TRANSLATIONS[key]?.['en-IN'] || key;
}
