import os
import csv
import io
import json
from datetime import datetime

from flask import Flask, request, render_template_string, redirect, url_for, session, make_response
from sqlalchemy import create_engine, text


# =========================
# UYGULAMA
# =========================
app = Flask(__name__)

# =========================
# KİMLİK / METİN
# =========================
TRAINING_NAME = "KESKİN NİŞANCILIK EĞİTİMİ DEĞERLENDİRME TESTİ"
INSTITUTION_NAME = "HAKKARİ ÖZEL HAREKAT ŞUBE MÜDÜRLÜĞÜ"

POINTS_PER_Q = 10
PASS_PERCENT = 70  # yüzde
TOTAL_QUIZ_SECONDS = 10 * 60  # 10 dakika

# =========================
# ENV (Render)
# =========================
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me_now")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin_change_me")

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine("sqlite:///results.db", pool_pre_ping=True)


# =========================
# SORULAR (10)
# =========================
QUIZ = [
    {
        "q": "Keskin nişancılıkta ilk atış isabeti neden kritik kabul edilir?",
        "choices": [
            "Çünkü ikinci atış daha pahalıdır",
            "Çünkü hedef genellikle ilk atıştan sonra saklanır veya yer değiştirir",
            "Çünkü silahlar tek atış yapar",
            "Çünkü optik sadece bir kez ayarlanır",
        ],
        "correct": 1,
    },
    {
        "q": "Balistik katsayı (BC) neyi ifade eder?",
        "choices": [
            "Merminin namlu çıkış hızını",
            "Merminin hava direncine karşı dayanımını",
            "Geri tepmenin şiddetini",
            "Optiğin büyütmesini",
        ],
        "correct": 1,
    },
    {
        "q": "Uzun mesafede en çok hata hangi faktörden çıkar?",
        "choices": ["Tetik kontrolü", "Rüzgâr okuma", "Optik markası", "Dipçik tipi"],
        "correct": 1,
    },
    {
        "q": "DOPE terimi ne anlama gelir?",
        "choices": [
            "Silah temizleme yağı",
            "Saha verisine dayalı atış ayarları",
            "Atış sonrası hedef incelemesi",
            "Optik montaj standardı",
        ],
        "correct": 1,
    },
    {
        "q": "Mirage (ısı dalgalanması) en çok neyi okumada işe yarar?",
        "choices": ["Mesafe", "Rüzgâr", "Geri tepme", "Paralaks"],
        "correct": 1,
    },
    {
        "q": "Coriolis etkisi hangi durumda daha anlamlı olur?",
        "choices": ["Kısa mesafe", "Hızlı seri atış", "Uzun mesafe hassas atış", "Kapalı alan"],
        "correct": 2,
    },
    {
        "q": "Tetik neden hafif ve nettir?",
        "choices": ["Daha hızlı atış", "Nişanı bozmadan tetik düşürmek", "Silahı sessiz yapmak", "Daha az bakım"],
        "correct": 1,
    },
    {
        "q": "Spin drift nedir?",
        "choices": ["Rüzgâr savurması", "Yer çekimi düşüşü", "Merminin dönüşünden kaynaklı yan sapma", "Optik kayması"],
        "correct": 2,
    },
    {
        "q": ".308 Win çoğu eğitim düzeninde neden sevilir?",
        "choices": ["En uzun menzil", "Eğitim/orta mesafe dengesi", "Zırh delme", "Sessiz atış"],
        "correct": 1,
    },
    {
        "q": "Profesyoneli amatörden ayıran temel şey nedir?",
        "choices": ["Pahalı ekipman", "Fiziksel güç", "Veri disiplini ve ölçüm alışkanlığı", "Büyük kalibre"],
        "correct": 2,
    },
]

TOTAL_POINTS = len(QUIZ) * POINTS_PER_Q


# =========================
# TEMA
# =========================
CSS = """
:root{
  --bg1:#0b0f14;
  --bg2:#0a1b2a;
  --card:#0f1620;
  --line:#23314a;
  --text:#eaf1ff;
  --muted:#a9b7cc;
  --accent:#2dd4bf;
  --accent2:#60a5fa;
  --danger:#fb7185;
  --ok:#34d399;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
  color:var(--text);
  background:
    radial-gradient(900px 450px at 15% -10%, rgba(96,165,250,.18), transparent),
    radial-gradient(900px 450px at 110% 10%, rgba(45,212,191,.14), transparent),
    linear-gradient(180deg, var(--bg2), var(--bg1));
}
header{
  position:sticky; top:0; z-index:10;
  background: rgba(11,15,20,.85);
  backdrop-filter: blur(8px);
  border-bottom:1px solid rgba(35,49,74,.9);
  padding:16px;
}
.container{max-width:1020px;margin:0 auto;padding:16px}
h1{margin:0;font-size:18px;letter-spacing:.4px}
h2{margin:0;font-size:15px;color:var(--muted);font-weight:700;letter-spacing:.3px}
.small{margin-top:6px;color:var(--muted);font-size:13px}
.card{
  background: rgba(15,22,32,.85);
  border:1px solid rgba(35,49,74,.9);
  border-radius:16px;
  padding:14px;
  margin:12px 0;
}
.grid{display:grid;gap:12px}
@media (min-width:720px){ .grid.two{grid-template-columns:1fr 1fr} }
.label{color:var(--muted);font-size:13px;margin-bottom:6px;font-weight:800;letter-spacing:.2px}
input[type="text"], input[type="password"], input[type="date"], select{
  width:100%;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid rgba(35,49,74,.9);
  background: rgba(10,27,42,.55);
  color: var(--text);
  outline: none;
}
.option{
  display:block;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid rgba(35,49,74,.9);
  margin:8px 0;
  background: rgba(10,27,42,.45);
}
.option:hover{border-color: rgba(45,212,191,.5)}
button{
  border:1px solid rgba(45,212,191,.55);
  background: linear-gradient(180deg, rgba(45,212,191,.18), rgba(96,165,250,.12));
  color:var(--text);
  padding:10px 14px;
  border-radius:12px;
  font-weight:900;
  cursor:pointer;
}
button.secondary{
  border-color: rgba(169,183,204,.25);
  background: rgba(10,27,42,.45);
}
.notice{
  border:1px dashed rgba(96,165,250,.5);
  background: rgba(10,27,42,.45);
  color:var(--muted);
  padding:12px;
  border-radius:14px;
}
.badge{
  display:inline-block;
  padding:4px 10px;
  border-radius:999px;
  border:1px solid rgba(35,49,74,.9);
  background: rgba(10,27,42,.45);
  font-size:12px;
  color: var(--muted);
  font-weight:800;
}
.badge.ok{border-color: rgba(52,211,153,.45); color: rgba(52,211,153,.95)}
.badge.bad{border-color: rgba(251,113,133,.45); color: rgba(251,113,133,.95)}
table{width:100%;border-collapse:collapse;border:1px solid rgba(35,49,74,.9);border-radius:14px;overflow:hidden}
th,td{padding:10px;border-bottom:1px solid rgba(35,49,74,.9);text-align:left;font-size:13px;vertical-align:top}
th{background: rgba(10,27,42,.6); color: var(--muted); font-weight:900}
.mono{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace}
a{color:var(--accent2);text-decoration:none;font-weight:800}
.timer{
  display:flex; align-items:center; justify-content:space-between; gap:10px;
}
.timerBox{
  padding:8px 12px;
  border-radius:999px;
  border:1px solid rgba(35,49,74,.9);
  background: rgba(10,27,42,.45);
}
.timerDanger{
  border-color: rgba(251,113,133,.55) !important;
  color: rgba(251,113,133,.95) !important;
}
"""

def no_store(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


# =========================
# DB ŞEMA / MIGRATION
# =========================
def init_db():
    is_postgres = bool(DATABASE_URL) and ("postgres" in DATABASE_URL)

    if is_postgres:
        ddl = """
        CREATE TABLE IF NOT EXISTS results (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            ts_utc TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            sicil TEXT NOT NULL UNIQUE,
            correct_count INTEGER NOT NULL,
            total_count INTEGER NOT NULL,
            score_points INTEGER NOT NULL,
            pass INTEGER NOT NULL,
            wrong_questions_json TEXT NOT NULL,
            answers_json TEXT NOT NULL
        )
        """
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            sicil TEXT NOT NULL UNIQUE,
            correct_count INTEGER NOT NULL,
            total_count INTEGER NOT NULL,
            score_points INTEGER NOT NULL,
            pass INTEGER NOT NULL,
            wrong_questions_json TEXT NOT NULL,
            answers_json TEXT NOT NULL
        )
        """

    with engine.begin() as conn:
        conn.execute(text(ddl))

        # Migration: eski tabloda kolon yoksa ekle
        # Postgres IF NOT EXISTS destekler; SQLite farklı olabilir => try/except
        try:
            conn.execute(text("ALTER TABLE results ADD COLUMN IF NOT EXISTS branch TEXT NOT NULL DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE results ADD COLUMN IF NOT EXISTS answers_json TEXT NOT NULL DEFAULT '[]'"))
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE results ADD COLUMN branch TEXT NOT NULL DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE results ADD COLUMN answers_json TEXT NOT NULL DEFAULT '[]'"))
        except Exception:
            pass


init_db()


# =========================
# DB yardımcıları
# =========================
def db_has_sicil(sicil: str) -> bool:
    with engine.begin() as conn:
        row = conn.execute(text("SELECT 1 FROM results WHERE sicil = :s LIMIT 1"), {"s": sicil}).fetchone()
        return row is not None


def db_insert_result(payload: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO results (
                ts_utc, first_name, last_name, branch, sicil,
                correct_count, total_count, score_points, pass,
                wrong_questions_json, answers_json
            )
            VALUES (
                :ts_utc, :first_name, :last_name, :branch, :sicil,
                :correct_count, :total_count, :score_points, :pass,
                :wrong_questions_json, :answers_json
            )
        """), payload)


def db_query_results(date_from: str | None, date_to: str | None, sicil: str | None, status: str | None):
    clauses = []
    params = {}

    if date_from:
        clauses.append("ts_utc >= :df")
        params["df"] = f"{date_from}T00:00:00Z"
    if date_to:
        clauses.append("ts_utc <= :dt")
        params["dt"] = f"{date_to}T23:59:59Z"
    if sicil:
        clauses.append("sicil LIKE :sic")
        params["sic"] = f"%{sicil}%"
    if status in ("pass", "fail"):
        clauses.append("pass = :p")
        params["p"] = 1 if status == "pass" else 0

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    q = f"""
        SELECT
          ts_utc, first_name, last_name, branch, sicil,
          correct_count, total_count, score_points, pass,
          wrong_questions_json, answers_json
        FROM results
        {where}
        ORDER BY ts_utc DESC
        LIMIT 2000
    """
    with engine.begin() as conn:
        rows = conn.execute(text(q), params).mappings().all()
        return rows


# =========================
# Admin: yanlışları okunur yap (numara listesi)
# =========================
def wrong_pretty(wrong_json: str) -> str:
    try:
        arr = json.loads(wrong_json)
        if not arr:
            return "-"
        return ", ".join(str(x) for x in arr)
    except Exception:
        return "-"


app.jinja_env.globals["wrong_pretty"] = wrong_pretty


# =========================
# SAYFALAR
# =========================
HOME_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{training}} - Katılım</title>
<style>{{css}}</style>
</head><body>
<header>
  <div class="container">
    <h1>{{training}}</h1>
    <h2>{{institution}}</h2>
    <div class="small">Ad / Soyad / Sicil / Şube ile giriş yap. Her sicil yalnızca 1 kez katılabilir.</div>
  </div>
</header>

<div class="container">
  {% if msg %}<div class="card notice">{{msg}}</div>{% endif %}
  <div class="card">
    <form method="post" action="/start">
      <div class="grid two">
        <div>
          <div class="label">AD</div>
          <input type="text" name="first_name" required>
        </div>
        <div>
          <div class="label">SOYAD</div>
          <input type="text" name="last_name" required>
        </div>
      </div>

      <div style="height:10px"></div>
      <div class="grid two">
        <div>
          <div class="label">SİCİL</div>
          <input type="text" name="sicil" required>
        </div>
        <div>
          <div class="label">ŞUBE</div>
          <input type="text" name="branch" required placeholder="Örn: 1. Tim / A Takımı">
        </div>
      </div>

      <div style="height:14px"></div>
      <button type="submit">TESTE BAŞLA</button>
    </form>
  </div>

  <div class="small">
    Not: Sonuç katılımcıya gösterilmez. Değerlendirme admin panelde tutulur. Test süresi toplam <span class="mono">{{total_minutes}}</span> dakikadır.
  </div>
</div>
</body></html>
"""

QUIZ_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{training}} - Test</title>
<style>{{css}}</style>
</head><body>
<header>
  <div class="container">
    <h1>{{training}}</h1>
    <h2>{{institution}}</h2>
    <div class="small">
      KATILIMCI: <span class="mono">{{user.first_name}} {{user.last_name}}</span> •
      SİCİL: <span class="mono">{{user.sicil}}</span> •
      ŞUBE: <span class="mono">{{user.branch}}</span> •
      TOPLAM PUAN: <span class="mono">{{total_points}}</span>
    </div>
  </div>
</header>

<div class="container">

{% if done %}
  <div class="card notice">
    <div style="font-weight:900;color:var(--text)">CEVAPLARINIZ ALINDI, TEŞEKKÜRLER.</div>
    <div class="small">Bu sicil ile tekrar katılım yapılamaz.</div>
  </div>
{% elif blocked %}
  <div class="card notice">
    <div style="font-weight:900;color:var(--text)">DAHA ÖNCE KATILIM SAĞLADINIZ.</div>
    <div class="small">Bu sicil ile tekrar test açılamaz.</div>
  </div>
{% else %}
  <div class="card">
    <div class="timer">
      <div class="small">
        SÜRE: <span class="mono timerBox" id="timerBox"><span id="timer">10:00</span></span>
        <span class="small">• Süre bitince otomatik gönderilir.</span>
      </div>
      <div>
        <button type="submit" form="quizForm">GÖNDER</button>
      </div>
    </div>
  </div>

  <form method="post" id="quizForm">
    {% for i, item in enumerate(quiz) %}
      <div class="card">
        <div style="font-weight:900; margin-bottom:10px">{{i+1}}) {{item.q}}</div>
        {% for c_i, c in enumerate(item.choices) %}
          <label class="option">
            <input type="radio" name="q{{i}}" value="{{c_i}}">
            {{ "ABCD"[c_i] }}) {{c}}
          </label>
        {% endfor %}
        <div class="small">Bu soru: {{ppq}} puan</div>
      </div>
    {% endfor %}
  </form>

  <script>
  (() => {
    const total = {{total_seconds}};
    let left = total;
    const timerEl = document.getElementById('timer');
    const box = document.getElementById('timerBox');
    const form = document.getElementById('quizForm');

    function fmt(s){
      const m = Math.floor(s/60);
      const r = s % 60;
      const mm = String(m).padStart(2,'0');
      const rr = String(r).padStart(2,'0');
      return `${mm}:${rr}`;
    }

    function tick(){
      timerEl.textContent = fmt(left);

      if (left <= 60){
        box.classList.add('timerDanger');
      }

      if (left <= 0){
        // Süre bitti: otomatik gönder
        form.submit();
        return;
      }
      left -= 1;
      setTimeout(tick, 1000);
    }

    // Sayfa refresh olursa reset olur. İstersen daha sonra localStorage ile devam ettiririz.
    timerEl.textContent = fmt(left);
    setTimeout(tick, 1000);
  })();
  </script>
{% endif %}

<div style="height:8px"></div>
<a class="small" href="/">ANA SAYFA</a>

</div>
</body></html>
"""

ADMIN_LOGIN_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Giriş</title>
<style>{{css}}</style>
</head><body>
<header><div class="container">
  <h1>ADMIN PANEL</h1>
  <h2>{{institution}}</h2>
  <div class="small">Şifre ile giriş</div>
</div></header>

<div class="container">
  {% if msg %}<div class="card notice">{{msg}}</div>{% endif %}
  <div class="card">
    <form method="post">
      <div class="label">ADMIN ŞİFRESİ</div>
      <input type="password" name="password" required>
      <div style="height:14px"></div>
      <button type="submit">GİRİŞ</button>
    </form>
  </div>
</div>
</body></html>
"""

ADMIN_DASHBOARD_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin – Sonuçlar</title>
<style>{{css}}</style>
</head><body>
<header><div class="container">
  <h1>SONUÇLAR</h1>
  <h2>{{institution}}</h2>

  <div class="small">
    Toplam (filtre sonrası): <span class="mono">{{count}}</span> •
    <span class="badge ok">BAŞARILI: {{pass_count}}</span>
    <span class="badge bad">BAŞARISIZ: {{fail_count}}</span>
    • <a href="/admin/export.csv?{{qs}}">CSV İNDİR</a>
    • <a href="/admin/logout">ÇIKIŞ</a>
  </div>
</div></header>

<div class="container">

  <div class="card">
    <form method="get" action="/admin/dashboard" class="grid two">
      <div>
        <div class="label">TARİH BAŞLANGIÇ (UTC)</div>
        <input type="date" name="from" value="{{f_from}}">
      </div>
      <div>
        <div class="label">TARİH BİTİŞ (UTC)</div>
        <input type="date" name="to" value="{{f_to}}">
      </div>
      <div>
        <div class="label">SİCİL ARA</div>
        <input type="text" name="sicil" value="{{f_sicil}}" placeholder="Örn: 12345">
      </div>
      <div>
        <div class="label">DURUM</div>
        <select name="status">
          <option value="" {% if f_status=="" %}selected{% endif %}>HEPSİ</option>
          <option value="pass" {% if f_status=="pass" %}selected{% endif %}>BAŞARILI</option>
          <option value="fail" {% if f_status=="fail" %}selected{% endif %}>BAŞARISIZ</option>
        </select>
      </div>
      <div style="grid-column:1/-1">
        <button type="submit">FİLTRELE</button>
        <a href="/admin/dashboard"><button class="secondary" type="button">SIFIRLA</button></a>
      </div>
    </form>
  </div>

  <div class="card">
    <table>
      <thead>
        <tr>
          <th>SİCİL</th>
          <th>AD</th>
          <th>SOYAD</th>
          <th>ŞUBE</th>
          <th>PUAN</th>
          <th>DURUM</th>
          <th>TARİH (UTC)</th>
          <th>YANLIŞ SORULAR</th>
        </tr>
      </thead>
      <tbody>
      {% if rows %}
        {% for r in rows %}
          <tr>
            <td class="mono">{{r.sicil}}</td>
            <td><a href="/admin/result/{{r.sicil}}">{{r.first_name}}</a></td>
            <td><a href="/admin/result/{{r.sicil}}">{{r.last_name}}</a></td>
            <td>{{r.branch}}</td>
            <td class="mono">{{r.score_points}} / {{r.total_count * ppq}}</td>
            <td>
              {% if r.pass == 1 %}
                <span class="badge ok">BAŞARILI</span>
              {% else %}
                <span class="badge bad">BAŞARISIZ</span>
              {% endif %}
            </td>
            <td class="mono">{{r.ts_utc}}</td>
            <td class="mono">{{wrong_pretty(r.wrong_questions_json)}}</td>
          </tr>
        {% endfor %}
      {% else %}
        <tr><td colspan="8">Sonuç yok.</td></tr>
      {% endif %}
      </tbody>
    </table>
  </div>

  <div class="small">
    İsim/soyisim tıklayınca cevap anahtarı detayına gider (doğru yeşil, yanlış kırmızı).
  </div>

</div>
</body></html>
"""

ADMIN_RESULT_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin – Detay</title>
<style>{{css}}</style>
</head><body>
<header><div class="container">
  <h1>SONUÇ DETAYI</h1>
  <h2>{{institution}}</h2>
  <div class="small">
    SİCİL: <span class="mono">{{r.sicil}}</span> •
    AD: <span class="mono">{{r.first_name}}</span> •
    SOYAD: <span class="mono">{{r.last_name}}</span> •
    ŞUBE: <span class="mono">{{r.branch}}</span><br>
    PUAN: <span class="mono">{{r.score_points}}/{{total_points}}</span> •
    {% if r.pass==1 %}<span class="badge ok">BAŞARILI</span>{% else %}<span class="badge bad">BAŞARISIZ</span>{% endif %}
    • <a href="/admin/dashboard">GERİ</a>
  </div>
</div></header>

<div class="container">
  {% for i, q in enumerate(quiz) %}
    <div class="card">
      <div style="font-weight:900;margin-bottom:10px">{{i+1}}) {{q.q}}</div>
      {% for c_i, c in enumerate(q.choices) %}
        {% set is_correct = (c_i == q.correct) %}
        {% set user_sel = answers[i] %}
        {% set is_user = (user_sel is not none and c_i == user_sel) %}

        <div class="option"
             style="
               {% if is_user and not is_correct %}border-color: rgba(251,113,133,.75); background: rgba(251,113,133,.12);{% endif %}
               {% if is_correct %}border-color: rgba(52,211,153,.75); background: rgba(52,211,153,.10);{% endif %}
             ">
          <span class="mono">{{ "ABCD"[c_i] }})</span> {{c}}
          {% if is_user and is_correct %} <span class="badge ok">SEÇTİĞİ (DOĞRU)</span>{% endif %}
          {% if is_user and not is_correct %} <span class="badge bad">SEÇTİĞİ (YANLIŞ)</span>{% endif %}
          {% if (not is_user) and is_correct %} <span class="badge ok">DOĞRU</span>{% endif %}
        </div>
      {% endfor %}
    </div>
  {% endfor %}
</div>
</body></html>
"""


# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    msg = request.args.get("msg", "")
    resp = make_response(render_template_string(
        HOME_PAGE,
        css=CSS,
        training=TRAINING_NAME,
        institution=INSTITUTION_NAME,
        msg=msg,
        total_minutes=TOTAL_QUIZ_SECONDS // 60
    ))
    return no_store(resp)


@app.post("/start")
def start():
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    sicil = (request.form.get("sicil") or "").strip()
    branch = (request.form.get("branch") or "").strip()

    if not first_name or not last_name or not sicil or not branch:
        return redirect(url_for("home", msg="Lütfen tüm alanları doldurun."))

    if db_has_sicil(sicil):
        return redirect(url_for("home", msg="Daha önce katılım sağladınız."))

    session["user"] = {"first_name": first_name, "last_name": last_name, "sicil": sicil, "branch": branch}
    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    user = session.get("user")
    if not user:
        return redirect(url_for("home", msg="Teste başlamadan önce bilgilerinizi girin."))

    sicil = (user.get("sicil") or "").strip()
    if not sicil:
        return redirect(url_for("home", msg="Sicil bilgisi eksik."))

    # DB'de varsa soruları gösterme
    if db_has_sicil(sicil):
        resp = make_response(render_template_string(
            QUIZ_PAGE, css=CSS, training=TRAINING_NAME, institution=INSTITUTION_NAME,
            user=user, quiz=QUIZ, enumerate=enumerate, done=False, blocked=True,
            total_points=TOTAL_POINTS, ppq=POINTS_PER_Q, total_seconds=TOTAL_QUIZ_SECONDS
        ))
        return no_store(resp)

    if request.method == "POST":
        correct = 0
        wrong_qnums = []
        answers = []  # her soru için seçilen şık index'i (0-3) veya None

        for i, q in enumerate(QUIZ):
            v = request.form.get(f"q{i}")
            if v is None or v == "":
                answers.append(None)
                wrong_qnums.append(i + 1)
                continue

            sel = int(v)
            answers.append(sel)

            if sel == q["correct"]:
                correct += 1
            else:
                wrong_qnums.append(i + 1)

        score_points = correct * POINTS_PER_Q
        percent = (score_points / TOTAL_POINTS) * 100 if TOTAL_POINTS else 0
        passed = 1 if percent >= PASS_PERCENT else 0

        payload = {
            "ts_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "branch": user.get("branch", ""),
            "sicil": sicil,
            "correct_count": correct,
            "total_count": len(QUIZ),
            "score_points": score_points,
            "pass": passed,
            "wrong_questions_json": json.dumps(wrong_qnums, ensure_ascii=False),
            "answers_json": json.dumps(answers, ensure_ascii=False),
        }

        try:
            db_insert_result(payload)
        except Exception:
            return redirect(url_for("home", msg="Daha önce katılım sağladınız."))

        # Bitti: soruları tekrar göstermiyoruz
        resp = make_response(render_template_string(
            QUIZ_PAGE, css=CSS, training=TRAINING_NAME, institution=INSTITUTION_NAME,
            user=user, quiz=QUIZ, enumerate=enumerate, done=True, blocked=False,
            total_points=TOTAL_POINTS, ppq=POINTS_PER_Q, total_seconds=TOTAL_QUIZ_SECONDS
        ))
        return no_store(resp)

    # GET
    resp = make_response(render_template_string(
        QUIZ_PAGE, css=CSS, training=TRAINING_NAME, institution=INSTITUTION_NAME,
        user=user, quiz=QUIZ, enumerate=enumerate, done=False, blocked=False,
        total_points=TOTAL_POINTS, ppq=POINTS_PER_Q, total_seconds=TOTAL_QUIZ_SECONDS
    ))
    return no_store(resp)


# -------- Admin login ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin") is True:
        return redirect(url_for("admin_dashboard"))

    msg = ""
    if request.method == "POST":
        pw = (request.form.get("password") or "").strip()
        if pw == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        msg = "Şifre hatalı."

    resp = make_response(render_template_string(
        ADMIN_LOGIN_PAGE, css=CSS, msg=msg, institution=INSTITUTION_NAME
    ))
    return no_store(resp)


@app.get("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# -------- Admin dashboard ----------
@app.get("/admin/dashboard")
def admin_dashboard():
    if session.get("admin") is not True:
        return redirect(url_for("admin_login"))

    f_from = request.args.get("from", "") or ""
    f_to = request.args.get("to", "") or ""
    f_sicil = (request.args.get("sicil", "") or "").strip()
    f_status = request.args.get("status", "") or ""

    rows = db_query_results(f_from or None, f_to or None, f_sicil or None, f_status or None)

    pass_count = sum(1 for r in rows if r["pass"] == 1)
    fail_count = sum(1 for r in rows if r["pass"] == 0)

    qs = request.query_string.decode("utf-8")

    resp = make_response(render_template_string(
        ADMIN_DASHBOARD_PAGE,
        css=CSS,
        institution=INSTITUTION_NAME,
        rows=rows,
        count=len(rows),
        pass_count=pass_count,
        fail_count=fail_count,
        f_from=f_from,
        f_to=f_to,
        f_sicil=f_sicil,
        f_status=f_status,
        qs=qs,
        ppq=POINTS_PER_Q
    ))
    return no_store(resp)


# -------- Admin: detay ----------
@app.get("/admin/result/<sicil>")
def admin_result_detail(sicil):
    if session.get("admin") is not True:
        return redirect(url_for("admin_login"))

    with engine.begin() as conn:
        r = conn.execute(text("""
            SELECT ts_utc, first_name, last_name, branch, sicil, correct_count, total_count,
                   score_points, pass, wrong_questions_json, answers_json
            FROM results
            WHERE sicil = :s
            LIMIT 1
        """), {"s": sicil}).mappings().fetchone()

    if not r:
        return "Kayıt bulunamadı", 404

    try:
        answers = json.loads(r["answers_json"]) if r["answers_json"] else [None] * len(QUIZ)
    except Exception:
        answers = [None] * len(QUIZ)

    # answers uzunluğu tutmazsa normalize et
    if len(answers) < len(QUIZ):
        answers = answers + [None] * (len(QUIZ) - len(answers))
    if len(answers) > len(QUIZ):
        answers = answers[:len(QUIZ)]

    resp = make_response(render_template_string(
        ADMIN_RESULT_PAGE,
        css=CSS,
        institution=INSTITUTION_NAME,
        r=r,
        quiz=QUIZ,
        enumerate=enumerate,
        answers=answers,
        total_points=TOTAL_POINTS
    ))
    return no_store(resp)


# -------- CSV export ----------
@app.get("/admin/export.csv")
def admin_export_csv():
    if session.get("admin") is not True:
        return redirect(url_for("admin_login"))

    f_from = request.args.get("from", "") or ""
    f_to = request.args.get("to", "") or ""
    f_sicil = (request.args.get("sicil", "") or "").strip()
    f_status = request.args.get("status", "") or ""

    rows = db_query_results(f_from or None, f_to or None, f_sicil or None, f_status or None)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ts_utc", "sicil", "first_name", "last_name", "branch",
        "score_points", "total_points", "pass", "wrong_questions", "answers_json"
    ])

    for r in rows:
        total_points = r["total_count"] * POINTS_PER_Q
        writer.writerow([
            r["ts_utc"], r["sicil"], r["first_name"], r["last_name"], r["branch"],
            r["score_points"], total_points, r["pass"],
            wrong_pretty(r["wrong_questions_json"]),
            r["answers_json"]
        ])

    data = output.getvalue().encode("utf-8")
    resp = make_response(data)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = 'attachment; filename="sonuclar.csv"'
    return no_store(resp)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
