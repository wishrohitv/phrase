from enum import Enum as PyEnum


class AccountStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"


class UserRole(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class ProviderType(str, PyEnum):
    LOCAL = "local"
    GOOGLE = "google"
    APPLE = "apple"


class FeatureType(str, PyEnum):
    MOVIE = "movie"
    TVSHOW = "tvshow"  # tvshow for refering groups of episode


class Language(str, PyEnum):
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    PERSIAN = "fa"
    SWEDISH = "sv"
    DUTCH = "nl"
    POLISH = "pl"
    CZECH = "cs"
    HUNGARIAN = "hu"
    ROMANIAN = "ro"
    BULGARIAN = "bg"
    CROATIAN = "hr"
    SLOVAK = "sk"
    SLOVENIAN = "sl"
    ESTONIAN = "et"
    LATVIAN = "lv"
    LITHUANIAN = "lt"
    FINNISH = "fi"
    DANISH = "da"
    NORWEGIAN = "no"
    ICELANDIC = "is"
    WELSH = "cy"
    SCOTTISH = "gd"
    GALICIAN = "gl"
    BASQUE = "eu"
    CATALAN = "ca"
    VALENCIA = "va"
    FRISIAN = "fy"
    BRETON = "br"
    CORNISH = "kw"
    SCOTS = "sco"
    MANX = "gv"
    GREEK = "el"
    HEBREW = "he"
    YIDDISH = "yi"
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    TAGALOG = "tl"
    MALAY = "ms"
    FILIPINO = "fil"
    HAITIAN = "ht"
    SERBIAN = "sr"
    BOSNIAN = "bs"
    MACEDONIAN = "mk"
    ALBANIAN = "sq"
    ARMENIAN = "hy"
    GEORGIAN = "ka"
    AZERBAIJANI = "az"
    UZBEK = "uz"
    KAZAKH = "kk"
    KYRGYZ = "ky"
    TURKMEN = "tk"
    UKRAINIAN = "uk"
    CHINESE_TW = "zh-TW"
    CHINESE_CN = "zh-CN"
    PORTUGUESE_PT = "pt-BR"
    PORTUGUESE_BR = "pt-PT"
    TAMIL = "ta"
    TELUGU = "te"
    MALAYALAM = "ml"
    KANNADA = "kn"
    MARATHI = "mr"
    GUJARATI = "gu"
    PUNJABI = "pa"
    BENGALI = "bn"
    ORIYA = "or"
    ASSAMESE = "as"
    MIZO = "mizo"
    KASHMIRI = "ks"
    NEPALI = "ne"
    SINDHI = "sd"
    URDU = "ur"
    BODO = "brx"
    MANIPURI = "mni"
    SANSCIRT = "sa"

    OTHER = "other"


class FeatureUnit(str, PyEnum):
    REQUEST = "request"
    TOKENS = "tokens"
    CHARACATER = "characters"


class SubscriptionStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class PlansStatus(str, PyEnum):
    ACTIVE = "active"
    DISCOUNTINUED = "discountinued"


class PlansBillingType(str, PyEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class DiscoverType(str, PyEnum):
    POPULAR = "popular"
    LATEST = "latest"


class ChatRoleType(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageStatus(str, PyEnum):
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
