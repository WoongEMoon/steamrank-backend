from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import requests
from datetime import datetime

app = FastAPI()

# ==============================================
# CORS
# ==============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================
# DB 연결
# ==============================================
def get_db():
    return psycopg2.connect(
        host="dpg-d4i86fkhg0os73fi4keg-a",
        dbname="steamrank_db",
        user="steamrank_db_user",
        password="xkUGR7Y35UidHw6HooptU41A0GXXg1Jh",
        port="5432"
    )

# ==============================================
# 기본 체크
# ==============================================
@app.get("/")
def home():
    return {"message": "SteamRank Backend running!"}

# ==============================================
# rankings 테이블 생성
# ==============================================
@app.get("/create_table")
def create_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            date TEXT,
            rank INTEGER,
            appid INTEGER,
            name TEXT,
            concurrent_players INTEGER,
            PRIMARY KEY(date, rank)
        );
    """)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "rankings table created!"}

# ==============================================
# games 테이블 생성
# ==============================================
@app.get("/create_games_table")
def create_games_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            appid INTEGER PRIMARY KEY,
            name TEXT
        );
    """)
    conn.commit()
    conn.close()
    return {"status": "success", "message": "games table created!"}

# ==============================================
# pgAdmin에 저장된 한국 게임 394개 → 자동 삽입
# ==============================================
KOREAN_GAMES = [
    {"steam_appid": 2119580, "name": "골든 레코드 리트리버"},
    {"steam_appid": 2234960, "name": "피그말리온"},
    {"steam_appid": 2020090, "name": "공간을 먹는 악어 | The Space-Eating Croc"},
    {"steam_appid": 1963080, "name": "난중설화 | The Tales of Imjin War"},
    {"steam_appid": 1599340, "name": "LOST ARK"},
    {"steam_appid": 216150, "name": "MapleStory"},
    {"steam_appid": 1431170, "name": "Pepo"},
    {"steam_appid": 4015430, "name": "더 스파이크 | The Spike"},
    {"steam_appid": 2712460, "name": "던전 슬래셔 | DUNGEON SLASHER"},
    {"steam_appid": 2231170, "name": "그래비티 캐슬 | Gravity Castle"},
    {"steam_appid": 1149450, "name": "Tree of Life 2"},
    {"steam_appid": 2219150, "name": "MUA"},
    {"steam_appid": 1663260, "name": "Snow Island"},
    {"steam_appid": 1603720, "name": "다이 크리쳐 | Thy Creature"},
    {"steam_appid": 2396900, "name": "엔스펠 | Enspell"},
    {"steam_appid": 1173010, "name": "여름의 끝에 피는 꽃 | Flowers Blooming at the End of Summer"},
    {"steam_appid": 2166250, "name": "배고픈 원시인 | Hungry Caveman"},
    {"steam_appid": 882900, "name": "여포키우기 | Lu Bu Maker"},
    {"steam_appid": 1490610, "name": "메탈릭 차일드 | METALLIC CHILD"},
    {"steam_appid": 1690040, "name": "메타버스킹 | Metavusking"},
    {"steam_appid": 1386340, "name": "모나드의 겨울 | Monads"},
    {"steam_appid": 2109360, "name": "가짜 하트"},
    {"steam_appid": 2676840, "name": "미제사건은 끝내야 하니까 | No Case Should Remain Unsolved"},
    {"steam_appid": 549850, "name": "Pygmalion"},
    {"steam_appid": 470310, "name": "TROUBLESHOOTER: Abandoned Children | 트러블슈터: 버려진 아이들"},
    {"steam_appid": 2148590, "name": "The Tainted Lands"},
    {"steam_appid": 299660, "name": "6180 the moon"},
    {"steam_appid": 1592520, "name": "WitchSpring3 Re:Fine - The Story of Eirudy - | 마녀의샘3 Re:Fine －인형 마녀 아이루디의 이야기－"},
    {"steam_appid": 1249080, "name": "린, 퍼즐에 그려진 소녀 이야기 | Lynn , The Girl Drawn On Puzzles"},
    {"steam_appid": 2661620, "name": "Love in Login"},
    {"steam_appid": 1334500, "name": "RP7"},
    {"steam_appid": 1137460, "name": "ALTF4"},
    {"steam_appid": 1565580, "name": "Mini Island"},
    {"steam_appid": 1816080, "name": "지구멸망 60초전! -운석배구 편- | Meteor Volleyball!"},
    {"steam_appid": 283660, "name": "Rabbit Hole 3D: Steam Edition"},
    {"steam_appid": 2072980, "name": "파이널나이트 | FINAL KNIGHT"},
    {"steam_appid": 2639460, "name": "첫눈 | First Snow"},
    {"steam_appid": 2419020, "name": "플로리스 다크니스 | Flawless Darkness"},
    {"steam_appid": 995460, "name": "Miracle Snack Shop | 기적의 분식집"},
    {"steam_appid": 1737520, "name": "프로스토리 | Frostory"},
    {"steam_appid": 1121420, "name": "킹덤 언더 파이어 : 더 크루세이더 | Kingdom Under Fire: The Crusaders"},
    {"steam_appid": 2686580, "name": "Trinity Survivors | 트리니티 서바이버즈"},
    {"steam_appid": 449450, "name": "SPLIT BULLET"},
    {"steam_appid": 2402310, "name": "STAND-ALONE"},
    {"steam_appid": 1140570, "name": "A Street Cat's Tale | 길고양이 이야기"},
    {"steam_appid": 2280540, "name": "The Last Saintess | 라스트 세인티스"},
    {"steam_appid": 1587240, "name": "피피숲의 연금술사 | Alchemist of Pipi Forest"},
    {"steam_appid": 1381650, "name": "ACTION SANDBOX"},
    {"steam_appid": 2203600, "name": "Vapor World: Over The Mind"},
    {"steam_appid": 467930, "name": "SMASHING THE BATTLE"},
    {"steam_appid": 2081310, "name": "TOBOR"},
    {"steam_appid": 2660700, "name": "Catch My Color"},
    {"steam_appid": 818500, "name": "Colorzzle"},
    {"steam_appid": 1092260, "name": "Come on Baby!"},
    {"steam_appid": 1675620, "name": "Last Light"},
    {"steam_appid": 1338770, "name": "Contract"},
    {"steam_appid": 517970, "name": "CRANGA!: Harbor Frenzy"},
    {"steam_appid": 876130, "name": "Crazy Farm : VRGROUND"},
    {"steam_appid": 576370, "name": "Cubians VR"},
    {"steam_appid": 1497710, "name": "갤럭시 테일즈: 스토리 오브 라푼젤"},
    {"steam_appid": 2153850, "name": "DEFECTIVE"},
    {"steam_appid": 1337030, "name": "En-Train"},
    {"steam_appid": 2725240, "name": "FADE^2"},
    {"steam_appid": 903850, "name": "Fairy Knights"},
    {"steam_appid": 1904040, "name": "Fantasy Fishing Town"},
    {"steam_appid": 1548010, "name": "Flipol"},
    {"steam_appid": 2393950, "name": "라이트 오디세이 | Light Odyssey"},
    {"steam_appid": 893480, "name": "For the Revenge"},
    {"steam_appid": 2274500, "name": "과몰입금지 | Love Too Easily"},
    {"steam_appid": 23450, "name": "GranAge"},
    {"steam_appid": 2544570, "name": "루미네나이트 | LumineNight"},
    {"steam_appid": 1575450, "name": "다크 세이렌 | Dark Siren"},
    {"steam_appid": 2536600, "name": "Dusty Derby | 더스티 더비"},
    {"steam_appid": 2582960, "name": "낙원: LAST PARADISE | NAKWON: LAST PARADISE"},
    {"steam_appid": 1926120, "name": "Heartless"},
    {"steam_appid": 1918450, "name": "HunterX"},
    {"steam_appid": 1602880, "name": "The Lord of the Parties | 로드 오브 파티"},
    {"steam_appid": 2700550, "name": "Urban Chase"},
    {"steam_appid": 1216060, "name": "DNF Duel"},
    {"steam_appid": 1304130, "name": "ReRoad"},
    {"steam_appid": 1391960, "name": "Star Island"},
    {"steam_appid": 1978520, "name": "Heartless"},
    {"steam_appid": 1714550, "name": "닌자 일섬 | Ninja Issen"},
    {"steam_appid": 2905790, "name": "PROJECT TACHYON"},
    {"steam_appid": 1987750, "name": "Silent World"},
    {"steam_appid": 2004180, "name": "도박묵시록 다구리: Remastered | DAGURI: Gambling Apocalypse"},
    {"steam_appid": 1013750, "name": "Legal Dungeon"},
    {"steam_appid": 1044410, "name": "Little Gods of the Abyss"},
    {"steam_appid": 1190310, "name": "댄싱 에로우 : 비트스매시 | Dancing Arrow : Beat Smash"},
    {"steam_appid": 2093020, "name": "Lonely White"},
    {"steam_appid": 2089460, "name": "데몽헌터 | Demong Hunter"},
    {"steam_appid": 2530490, "name": "Lost Eidolons"},
    {"steam_appid": 1695400, "name": "Lucky Fish Bread"},
    {"steam_appid": 2387310, "name": "Magic Paper"},
    {"steam_appid": 2546170, "name": "Memory Fragment"},
    {"steam_appid": 788770, "name": "Meteor 60 Seconds!"},
    {"steam_appid": 918430, "name": "Second Second"},
    {"steam_appid": 2016580, "name": "데네브: 별을 건너서 | Deneb: Across the Stars"},
    {"steam_appid": 1188930, "name": "크로노 아크 | Chrono Ark"},
    {"steam_appid": 1219300, "name": "Contract"},
    {"steam_appid": 1627720, "name": "P의 거짓 | Lies of P"},
    {"steam_appid": 1958220, "name": "WitchSpring R | 마녀의샘R"},
    {"steam_appid": 2516270, "name": "Pa!nt"},
    {"steam_appid": 1932330, "name": "TOBOR"},
    {"steam_appid": 546090, "name": "VINE"},
    {"steam_appid": 1703210, "name": "Box to the Box"},
    {"steam_appid": 1996090, "name": "Vapor World: Over The Mind"},
    {"steam_appid": 2276110, "name": "쿠시의 엄천난 모험!! | Cush's Amazin' Adventure!!"},
    {"steam_appid": 2725250, "name": "Nientum - Opus Zero"},
    {"steam_appid": 1005470, "name": "Cubians: Combine"},
    {"steam_appid": 496290, "name": "Deep Dark Dungeon"},
    {"steam_appid": 2323810, "name": "DEFENDUN : Hero Defense"},
    {"steam_appid": 1254930, "name": "Rain Island"},
    {"steam_appid": 1039330, "name": "NOTE"},
    {"steam_appid": 2226730, "name": "OVIS LOOP"},
    {"steam_appid": 2232200, "name": "첫눈"},
    {"steam_appid": 2473710, "name": "Abyss School | 어비스 스쿨"},
    {"steam_appid": 1412470, "name": "GranAge"},
    {"steam_appid": 814870, "name": "모나드의 겨울"},
    {"steam_appid": 2482920, "name": "사람 속에 피는 꽃 | Flower in Us"},
    {"steam_appid": 968350, "name": "Hotel Sowls"},
    {"steam_appid": 1580520, "name": "로스트 아이돌론스"},
    {"steam_appid": 1361150, "name": "Day Island"},
    {"steam_appid": 1494140, "name": "7Days Origins | 세븐데이즈 오리진"},
    {"steam_appid": 1000000, "name": "ASCENXION"},
    {"steam_appid": 1367300, "name": "Blade Assault"},
    {"steam_appid": 2376780, "name": "Battery Samurai"},
    {"steam_appid": 1720180, "name": "Mini Island: Autumn"},
    {"steam_appid": 1647430, "name": "Black Mansion"},
    {"steam_appid": 1544020, "name": "The Callisto Protocol™"},
    {"steam_appid": 355980, "name": "Dungeon Warfare"},
    {"steam_appid": 859370, "name": "in My MIND."},
    {"steam_appid": 637120, "name": "Space God"},
    {"steam_appid": 494150, "name": "Box to the Box"},
    {"steam_appid": 2153950, "name": "Broken Blade: Prelude"},
    {"steam_appid": 2016590, "name": "Dark and Darker"},
    {"steam_appid": 851040, "name": "Darkest Mana : Master of the Table"},
    {"steam_appid": 658770, "name": "Dreamals"},
    {"steam_appid": 2552310, "name": "Dungeon Inn"},
    {"steam_appid": 698540, "name": "Dungeon Warfare 2"},
    {"steam_appid": 2520000, "name": "HYNPYTOL"},
    {"steam_appid": 2244130, "name": "Ratopia"},
    {"steam_appid": 2093800, "name": "METAL SUITS"},
    {"steam_appid": 1897970, "name": "Mini Island: Aroma"},
    {"steam_appid": 1454540, "name": "LAPIN | 라핀"},
    {"steam_appid": 1952550, "name": "Mini Island: Cosmos"},
    {"steam_appid": 1200780, "name": "Mini Island: Night"},
    {"steam_appid": 1114740, "name": "Red Island"},
    {"steam_appid": 2081340, "name": "KAMiBAKO - Mythology of Cube -"},
    {"steam_appid": 1357990, "name": "Unfolded : Camellia Tales | 언폴디드 : 동백이야기"},
    {"steam_appid": 2441270, "name": "Kill The Crows"},
    {"steam_appid": 2118250, "name": "Kitchen Crisis"},
    {"steam_appid": 1714510, "name": "Kusan : City of Wolves"},
    {"steam_appid": 2225480, "name": "REMORE: INFESTED KINGDOM | 비포 더 던"},
    {"steam_appid": 2309280, "name": "Mini Star Cafe"},
    {"steam_appid": 2538830, "name": "Mini Star Survivor"},
    {"steam_appid": 2171610, "name": "Mini Star Bakery"},
    {"steam_appid": 692950, "name": "The Dew"},
    {"steam_appid": 1221390, "name": "VOXEL HORIZON"},
    {"steam_appid": 3746740, "name": "MUA"},
    {"steam_appid": 2312340, "name": "Nyan-Nyan Punch! | 냥냥펀치!"},
    {"steam_appid": 994220, "name": "NEOVERSE"},
    {"steam_appid": 1822500, "name": "Mixx Island"},
    {"steam_appid": 1377380, "name": "Night of the Dead"},
    {"steam_appid": 2213190, "name": "NOTE"},
    {"steam_appid": 1822500, "name": "Mixx Island: Remix Vol. 2"},
    {"steam_appid": 1795820, "name": "OctoRaid VR"},
    {"steam_appid": 813920, "name": "oldTail"},
    {"steam_appid": 492610, "name": "One Day : The Sun Disappeared"},
    {"steam_appid": 991560, "name": "OnePunch"},
    {"steam_appid": 1165230, "name": "Elevenses: The Flask | 일레븐지스: 플라스크"},
    {"steam_appid": 1832130, "name": "VINE"},
    {"steam_appid": 1821970, "name": "Diaspora"},
    {"steam_appid": 830560, "name": "OVERTURN"},
    {"steam_appid": 3107230, "name": "Pa!nt"},
    {"steam_appid": 3108340, "name": "Pepo"},
    {"steam_appid": 861150, "name": "PLUTONIUM"},
    {"steam_appid": 2728950, "name": "Potty Knight Saga"},
    {"steam_appid": 735570, "name": "Project Rhombus"},
    {"steam_appid": 578080, "name": "PUBG: BATTLEGROUNDS"},
    {"steam_appid": 297760, "name": "QV"},
    {"steam_appid": 1203140, "name": "RaidTitans"},
    {"steam_appid": 1660270, "name": "Rain Island: Orange"},
    {"steam_appid": 1108370, "name": "Ratropolis"},
    {"steam_appid": 995240, "name": "RemiLore: Lost Girl in the Lands of Lore"},
    {"steam_appid": 2397140, "name": "TOKYO PSYCHODEMIC | 사이코데믹 특수 수사 사건부 X-FILE"},
    {"steam_appid": 1464500, "name": "Ruvato: Original Complex | 루바토: 오리지널 콤플렉스"},
    {"steam_appid": 300380, "name": "ReRoad"},
    {"steam_appid": 382920, "name": "RETSNOM"},
    {"steam_appid": 1479400, "name": "Riffle Effect"},
    {"steam_appid": 1394480, "name": "Rocco's Island: Ring to End the Pain"},
    {"steam_appid": 1147560, "name": "Skul: The Hero Slayer"},
    {"steam_appid": 2436940, "name": "Sephiria"},
    {"steam_appid": 1045720, "name": "The Coma 2: Vicious Sisters"},
    {"steam_appid": 600090, "name": "The Coma: Recut"},
    {"steam_appid": 1573100, "name": "Subterrain"},
    {"steam_appid": 1573100, "name": "Subterrain: Mines of Titan"},
    {"steam_appid": 938220, "name": "TAPSONIC BOLD"},
    {"steam_appid": 2347910, "name": "Seal: WHAT the FUN"},
    {"steam_appid": 2889460, "name": "Route8"},
    {"steam_appid": 2289630, "name": "Shambles"},
    {"steam_appid": 212110, "name": "Sugar Cube: Bittersweet Factory"},
    {"steam_appid": 331460, "name": "ROOMS: The Toymaker's Mansion"},
    {"steam_appid": 512230, "name": "Sally's Law"},
    {"steam_appid": 304500, "name": "Rooms: The Main Building"},
    {"steam_appid": 826040, "name": "Sacred Stones"},
    {"steam_appid": 1933700, "name": "Smilemo"},
    {"steam_appid": 699710, "name": "Rose and Lotus: Petals of Memories | 장화홍련: 기억의 조각"},
    {"steam_appid": 2126010, "name": "Soul Guardians"},
    {"steam_appid": 1025960, "name": "베리드 스타즈 | BURIED STARS"},
    {"steam_appid": 2447120, "name": "Veiled Edge | 베일드 엣지"},
    {"steam_appid": 2484250, "name": "ASTRA: Knights of Veda | 별이되어라2: 베다의 기사들"},
    {"steam_appid": 2280520, "name": "Vampire Mansion | 뱀파이어 맨션"},
    {"steam_appid": 2897270, "name": "Black hole Escape | 블랙홀 이스케이프"},
    {"steam_appid": 340490, "name": "Subterrain"},
    {"steam_appid": 1153840, "name": "Snow Island"},
    {"steam_appid": 2167600, "name": "Star Rabbits"},
    {"steam_appid": 2104560, "name": "SOWON"},
    {"steam_appid": 2104520, "name": "Roll me Home"},
    {"steam_appid": 2516280, "name": "SEOIRYE"},
    {"steam_appid": 3683960, "name": "RUNES Magica"},
    {"steam_appid": 1012880, "name": "Second Second"},
    {"steam_appid": 2712480, "name": "Shikhondo"},
    {"steam_appid": 625770, "name": "SMASHING THE BATTLE"},
    {"steam_appid": 1561510, "name": "Space God"},
    {"steam_appid": 2054660, "name": "Star Island"},
    {"steam_appid": 1829420, "name": "Before The Night | 비포 더 나이트"},
    {"steam_appid": 2814860, "name": "Vindictus: Defying Fate | 빈딕투스: 디파잉 페이트"},
    {"steam_appid": 2120310, "name": "Sagres | 사그레스"},
    {"steam_appid": 1865080, "name": "Idol Queens Production | 퀸즈 아이돌"},
    {"steam_appid": 1925860, "name": "Seonbi : Scholar of Joseon | 문경새재"},
    {"steam_appid": 944710, "name": "TurnTack"},
    {"steam_appid": 1210670, "name": "Silent World"},
    {"steam_appid": 466130, "name": "White Day: A Labyrinth Named School"},
    {"steam_appid": 1193340, "name": "Zelter"},
    {"steam_appid": 904380, "name": "Vambrace: Cold Soul"},
    {"steam_appid": 1042920, "name": "Unsouled"},
    {"steam_appid": 2078040, "name": "White Day2: The Flower That Tells Lies"},
    {"steam_appid": 2492290, "name": "Uncover the Smoking Gun"},
    {"steam_appid": 465130, "name": "Wicce"},
    {"steam_appid": 1847120, "name": "11F | 11층"},
    {"steam_appid": 1475460, "name": "3 Minute Heroes | 3분 영웅"},
    {"steam_appid": 2108060, "name": "The Ramsey | 더 램지"},
    {"steam_appid": 1311540, "name": "The Wake: Mourning Father, Mourning Mother"},
    {"steam_appid": 1362120, "name": "PIGROMANCE | 피그로맨스"},
    {"steam_appid": 2164200, "name": "Acretia - Guardians of Lian | 아크레티아 전기"},
    {"steam_appid": 746660, "name": "Throw Anything"},
    {"steam_appid": 1494110, "name": "QV"},
    {"steam_appid": 1908500, "name": "RUNES Magica"},
    {"steam_appid": 720150, "name": "Shikhondo(食魂徒) - Soul Eater"},
    {"steam_appid": 1945560, "name": "World of Mines Creator's Edition"},
    {"steam_appid": 2073850, "name": "THE FINALS"},
    {"steam_appid": 1198810, "name": "Wolf and Pigs"},
    {"steam_appid": 2266740, "name": "Twinkle Hunter"},
    {"steam_appid": 1551770, "name": "Too Many Zombies!"},
    {"steam_appid": 2889980, "name": "The Reeve"},
    {"steam_appid": 2125870, "name": "30 Days Another | 30일 어나더"},
    {"steam_appid": 2795540, "name": "The Midnight Walkers"},
    {"steam_appid": 2928190, "name": "There is NO PLAN B"},
    {"steam_appid": 712870, "name": "Vectorium"},
    {"steam_appid": 1897060, "name": "VELASTER"},
    {"steam_appid": 2686570, "name": "Waltz and Jam"},
    {"steam_appid": 2310920, "name": "THE EDITOR | 편집장"},
    {"steam_appid": 2144310, "name": "Wetory"},
    {"steam_appid": 1227320, "name": "Shutter Nyan! Enhanced Edition | 셔터냥! Enhanced Edition"},
    {"steam_appid": 1934020, "name": "Polar Penguin Post | 폴라 펭귄 포스트"},
    {"steam_appid": 2356450, "name": "길고양이 이야기 2: 집밖은 위험해 | A Street Cat's Tale 2: Out side is dangerous"},
    {"steam_appid": 2090760, "name": "X Invader | 엑스 인베이더"},
    {"steam_appid": 1683100, "name": "Ultra Age | 울트라 에이지"},
    {"steam_appid": 2207300, "name": "블루 웬즈데이 | Blue Wednesday"},
    {"steam_appid": 1552250, "name": "세 장의 카드 | Three of Cards"},
    {"steam_appid": 2216600, "name": "조선메타실록 | Korea Dynasty"},
    {"steam_appid": 2329060, "name": "청구야담: 팔도견문록 | Dynasty Detective"},
    {"steam_appid": 2177170, "name": "지금 우리 학교는 | All of Us Are Dead…"},
    {"steam_appid": 2187230, "name": "ALTF42"},
    {"steam_appid": 1326920, "name": "AstroWings: Space War"},
    {"steam_appid": 1602390, "name": "Black Academy"},
    {"steam_appid": 1557410, "name": "BLACK WITCHCRAFT"},
    {"steam_appid": 943510, "name": "Blindia"},
    {"steam_appid": 1476350, "name": "Brain Meltdown - Into Despair"},
    {"steam_appid": 385440, "name": "Buff Knight Advanced"},
    {"steam_appid": 1758060, "name": "Ceilless"},
    {"steam_appid": 928680, "name": "Chicken in the Darkness"},
    {"steam_appid": 1594940, "name": "Little Witch in the Woods | 숲속의 작은 마녀"},
    {"steam_appid": 2697930, "name": "Commander Quest"},
    {"steam_appid": 2007770, "name": "Corrupted: Dawn of Havoc"},
    {"steam_appid": 2637070, "name": "크롤링 랩 | Crawling Lab"},
    {"steam_appid": 2925010, "name": "Cryptic Route"},
    {"steam_appid": 712910, "name": "Cubians : Rescue Princess"},
    {"steam_appid": 1709780, "name": "Cute Invaders"},
    {"steam_appid": 321290, "name": "Dandelion - Wishes brought to you -"},
    {"steam_appid": 1235830, "name": "다크워터 : 슬라임 인베이더 | Dark Water : Slime Invader"},
    {"steam_appid": 1868140, "name": "데이브 더 다이버 | DAVE THE DIVER"},
    {"steam_appid": 2147680, "name": "Day Island"},
    {"steam_appid": 1281890, "name": "DEFECTIVE"},
    {"steam_appid": 1454010, "name": "루시의 일기 | Diary of Lucie"},
    {"steam_appid": 1395420, "name": "Diaspora"},
    {"steam_appid": 960170, "name": "DJMAX RESPECT V"},
    {"steam_appid": 2153920, "name": "DOWNFALLEN"},
    {"steam_appid": 2803280, "name": "Dragon Is Dead"},
    {"steam_appid": 1042290, "name": "Duckumentary"},
    {"steam_appid": 271760, "name": "던전 로드 | Dungeon Lord"},
    {"steam_appid": 3419220, "name": "Dungeon Warfare"},
    {"steam_appid": 753420, "name": "Dungreed"},
    {"steam_appid": 1049590, "name": "이터널 리턴 | Eternal Return"},
    {"steam_appid": 1152820, "name": "Everslash"},
    {"steam_appid": 1477590, "name": "EZ2ON REBOOT : R"},
    {"steam_appid": 2161430, "name": "FAKE SIGNALS"},
    {"steam_appid": 2302820, "name": "FAS: Fight Action Sandbox"},
    {"steam_appid": 2235500, "name": "유물의 숲 | Forest Of Relics"},
    {"steam_appid": 1452540, "name": "Frincess&Cnight"},
    {"steam_appid": 2319940, "name": "GREAT TOY SHOWDOWN"},
    {"steam_appid": 2667410, "name": "영웅모집 | Heroes Wanted"},
    {"steam_appid": 2680330, "name": "HunterX: code name T"},
    {"steam_appid": 2399080, "name": "Idle Catfarmia"},
    {"steam_appid": 2021280, "name": "in My MIND."},
    {"steam_appid": 673810, "name": "Infinite Sunshine Dust"},
    {"steam_appid": 2717010, "name": "KALPA: Cosmic Symphony"},
    {"steam_appid": 1255740, "name": "Karma Knight"},
    {"steam_appid": 917200, "name": "Kill the Dictator"},
    {"steam_appid": 2183600, "name": "Kingdom Under Fire: A War of Heroes"},
    {"steam_appid": 1125880, "name": "레이저존 | LaserZone"},
    {"steam_appid": 287390, "name": "Last Light"},
    {"steam_appid": 1256670, "name": "Library Of Ruina"},
    {"steam_appid": 568220, "name": "Lobotomy Corporation | Monster Management Simulation"},
    {"steam_appid": 1306630, "name": "Lost Ruins"},
    {"steam_appid": 1817940, "name": "러브 딜리버리 | Love Delivery"},
    {"steam_appid": 1274710, "name": "라라바이 데이즈 | Lullaby Days"},
    {"steam_appid": 1218360, "name": "루나 : 차원의 감시자 | Luna : The Dimension Watcher"},
    {"steam_appid": 2098560, "name": "Youtuber Survivors | 유튜버 서바이버즈"},
    {"steam_appid": 1178150, "name": "MazM: Jekyll and Hyde"},
    {"steam_appid": 1483300, "name": "MazM: 오페라의 유령 | MazM: The Phantom of the Opera"},
    {"steam_appid": 1446930, "name": "Merge & Blade"},
    {"steam_appid": 1173200, "name": "Metal Unit"},
    {"steam_appid": 2522550, "name": "Mini Garden Cafe"},
    {"steam_appid": 1427680, "name": "Magia X"},
    {"steam_appid": 1601790, "name": "Mini Island: Summer"},
    {"steam_appid": 1781980, "name": "Mini Island: Winter"},
    {"steam_appid": 2012790, "name": "Mini Star Fishing"},
    {"steam_appid": 2782420, "name": "Minimal Escape"},
    {"steam_appid": 1822500, "name": "Mixx Island: Remix"},
    {"steam_appid": 1386340, "name": "모나드의 겨울 II | Monads II"},
    {"steam_appid": 1006830, "name": "Moonlight thief"},
    {"steam_appid": 1414180, "name": "모태솔로 | Motesolo : No Girlfriend Since Birth"},
    {"steam_appid": 337930, "name": "Nameless The one thing you must recall"},
    {"steam_appid": 1222090, "name": "네바에 | Nevaeh"},
    {"steam_appid": 756490, "name": "Next Hero"},
    {"steam_appid": 1301390, "name": "No Umbrellas Allowed"},
    {"steam_appid": 1352080, "name": "SMASH LEGENDS | 스매시 레전드"},
    {"steam_appid": 1113560, "name": "Replica"},
    {"steam_appid": 1536210, "name": "Ira | 이라"},
    {"steam_appid": 837090, "name": "Tree of Life: Oddria!"},
    {"steam_appid": 334310, "name": "Plebby Quest: The Crusades | 플레비 퀘스트: 더 크루세이즈"},
    {"steam_appid": 1098080, "name": "3000th Duel"},
    {"steam_appid": 1141120, "name": "Scarlet Hood and the Wicked Wood"},
    {"steam_appid": 607660, "name": "21 Days"},
    {"steam_appid": 1442650, "name": "White Day VR: The Courage Test"},
    {"steam_appid": 1042130, "name": "Under Water : Abyss Survival VR"},
    {"steam_appid": 1312070, "name": "Pink Island"},
    {"steam_appid": 2277370, "name": "Marco Entertainment | 마르코 엔터테인먼트"},
    {"steam_appid": 2104750, "name": "아케이드 파티 | Arcade Party"},
    {"steam_appid": 2696400, "name": "마법소녀 카와이 러블리 즈큥도큥 바큥부큥 루루핑 | Magical Mic Duel"},
    {"steam_appid": 2131920, "name": "Super Hamster Ball"},
    {"steam_appid": 2491130, "name": "Split square | 스플릿 스퀘어"},
    {"steam_appid": 1802720, "name": "Sixtar Gate: STARTRAIL | 식스타 게이트: 스타트레일"},
    {"steam_appid": 371120, "name": "실망실업자"},
    {"steam_appid": 1217390, "name": "Some Some Convenience Store | 썸썸 편의점"},
    {"steam_appid": 1190130, "name": "Araha : Curse of Yieun Island | 아라하 : 이은도의 저주"},
    {"steam_appid": 1229900, "name": "ARIA CHRONICLE | 아리아 크로니클"},
    {"steam_appid": 2551550, "name": "GoodbyeSeoul : Itaewon | 안녕서울 : 이태원편"},
    {"steam_appid": 2891020, "name": "Undusted: Letters from the Past | 언더스티드"},
    {"steam_appid": 2050530, "name": "Age of Solitaire : Build Civilization"},
    {"steam_appid": 2659150, "name": "_message: | _전언:"},
    {"steam_appid": 668550, "name": "8Doors: Arum's Afterlife Adventure | 사망여각"},
    {"steam_appid": 1562700, "name": "SANABI: The Revenant | 산나비"},
    {"steam_appid": 628730, "name": "Adolescent Santa Claus"},
    {"steam_appid": 2388920, "name": "SOULERS | 소울러즈"},
    {"steam_appid": 1474200, "name": "Sudoku RPG | 스도쿠 알피지"},
    {"steam_appid": 2658920, "name": "Staffer Reborn | 스테퍼 리본"},
    {"steam_appid": 2128480, "name": "Staffer Case: A Supernatural Mystery Adventure"},
    {"steam_appid": 1802880, "name": "The Devil Within: Satgat | 데블위딘 삿갓"},
    {"steam_appid": 771580, "name": "Mad World - Age of Darkness – MMORPG"},
    {"steam_appid": 2153900, "name": "Ember's Love | 엠버스 러브"},
    {"steam_appid": 1985960, "name": "Ogu and the Secret Forest | 오구와 비밀의 숲"},
    {"steam_appid": 2308820, "name": "Qualification as Rogue | 용사의 자격"},
    {"steam_appid": 1158720, "name": "Causality | 인과율"},
    {"steam_appid": 2265760, "name": "Chosun Zombie Defense | 조선 좀비 디펜스"},
    {"steam_appid": 1534980, "name": "Terminus: Zombie Survivors | 터미너스"},
    {"steam_appid": 1372810, "name": "Teamfight Manager | 팀파이트 매니저"},
    {"steam_appid": 2074920, "name": "The First Descendant | 퍼스트 디센던트"},
    {"steam_appid": 2680010, "name": "The First Berserker: Khazan | 퍼스트 버서커: 카잔"},
    {"steam_appid": 2210700, "name": "Pechka: Historical Story Adventure | 페치카"}
]

@app.get("/update_games")
def update_games():
    conn = get_db()
    cur = conn.cursor()

    inserted = 0

    for game in KOREAN_GAMES:
        appid = game["steam_appid"]
        name = game["name"]

        cur.execute("""
            INSERT INTO games (appid, name)
            VALUES (%s, %s)
            ON CONFLICT (appid)
            DO UPDATE SET name = EXCLUDED.name;
        """, (appid, name))

        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success", "total_processed": inserted}


# ==============================================
# SteamCharts TOP100 → rankings 저장
# ==============================================
from datetime import datetime
import requests

@app.get("/update")
def update():
    conn = get_db()
    cur = conn.cursor()

    # 오늘 날짜 (랭킹에 저장할 날짜)
    today = datetime.utcnow().date()

    # 1) games 테이블에서 "한국 게임 394개" 목록 가져오기
    #    - steam_appid: 동접자 API에 쓸 ID
    #    - name: 랭킹 테이블에 같이 넣을 이름
    cur.execute("""
        SELECT appid, name
        FROM games;
    """)
    games = cur.fetchall()  # [(appid, name), ...]

    results = []

    # 2) 각 게임별로 동접자 수 조회
    for appid, name in games:
        try:
            players_api = (
                "https://api.steampowered.com/"
                "ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
                f"?appid={appid}"
            )
            res = requests.get(players_api, timeout=5).json()
            players = res.get("response", {}).get("player_count", 0)
        except Exception:
            players = 0

        results.append((appid, name, players))

    # 3) 동접자 수 기준으로 내림차순 정렬 → 랭킹 번호 부여
    results.sort(key=lambda x: x[2], reverse=True)

    # 같은 날짜의 기존 랭킹은 지워버리고 새로 채운다
    cur.execute("DELETE FROM rankings WHERE date = %s;", (today,))

    # 4) rankings 테이블에 저장
    # rankings 테이블 구조 가정:
    #   date DATE
    #   rank INTEGER
    #   appid INTEGER
    #   name TEXT
    #   concurrent_players INTEGER
    inserted = 0
    for rank, (steam_appid, name, players) in enumerate(results, start=1):
        cur.execute(
            """
            INSERT INTO rankings (date, rank, appid, name, concurrent_players)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (today, rank, steam_appid, name, players),
        )
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success", "count": inserted}


# ==============================================
# 오늘의 랭킹 조회 (한국 게임 + 공식 스팀 링크용 appid 포함)
# ==============================================
@app.get("/rank")
def get_rank(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.rank, r.appid, g.name, r.concurrent_players
        FROM rankings r
        JOIN games g ON r.appid = g.appid
        WHERE r.date = %s
        ORDER BY r.rank ASC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "rank": r[0],
            "appid": r[1],
            "name": r[2],
            "players": r[3],
            "steam_url": f"https://store.steampowered.com/app/{r[1]}"
        }
        for r in rows
    ]

# ==============================================
# 자동완성 검색
# ==============================================
@app.get("/api/search")
def search_game(q: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT appid, name FROM games
        WHERE name ILIKE %s
        ORDER BY name ASC
        LIMIT 20;
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()

    return [
        {"appid": r[0], "name": r[1]} for r in rows
    ]

# ==============================================
# React용 rankings API
# ==============================================
@app.get("/api/rankings")
def api_rankings(date: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.rank, r.appid, g.name, r.concurrent_players
        FROM rankings r
        JOIN games g ON r.appid = g.appid
        WHERE r.date = %s
        ORDER BY r.rank ASC;
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return {
        "rankings": [
            {
                "rank": r[0],
                "appid": r[1],
                "name": r[2],
                "players": r[3],
                "steam_url": f"https://store.steampowered.com/app/{r[1]}"
            }
            for r in rows
        ]
    }
