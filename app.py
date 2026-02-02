import os
import csv
import io
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, session, make_response

app = Flask(__name__)

# =========================
# AYARLAR (Render Environment)
# =========================
# Render > Environment'a ekle:
# SECRET_KEY: uzun rastgele bir string (en az 32 karakter)
# ADMIN_PASSWORD: admin panel şifresi
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me_now")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin_change_me")

# Bellek içi veri (Render free restart olursa sıfırlanabilir)
RESULTS = []          # kayıt listesi
SUBMITTED = set()     # sicil bazlı tek katılım


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
            "Tüfeğin geri tepkisini",
            "Optiğin büyütme oranını",
        ],
        "correct": 1,
    },
    {
        "q": "Uzun mesafe atışlarında en çok hata hangi faktörden kaynaklanır?",
        "choices": [
            "Tetik kontrolü",
            "Rüzgâr okuma",
            "Optik kalitesi",
            "Kalibre seçimi",
        ],
        "correct": 1,
    },
    {
        "q": "DOPE terimi ne anlama gelir?",
        "choices": [
            "Silah temizleme yağı",
            "Gerçek saha verilerine dayalı atış ayarları",
            "Atış sonrası analiz",
            "Optik montaj sistemi",
        ],
        "correct": 1,
    },
    {
        "q": "Mirage (ısı dalgalanması) keskin nişancıya ne hakkında bilgi verir?",
        "choices": [
            "Hedefin mesafesi",
            "Rüzgârın yönü ve şiddeti",
            "Merminin düşüşü",
            "Işık kırılması",
        ],
        "correct": 1,
    },
    {
        "q": "Coriolis etkisi hangi durumlarda önem kazanır?",
        "choices": [
            "Kısa mesafe atışlarda",
            "Düşük hızlı mermilerde",
            "Uzun mesafe ve yüksek hassasiyetli atışlarda",
            "Kapalı alan atışlarında",
        ],
        "correct": 2,
    },
    {
        "q": "Keskin nişancı tüfeğinde tetik neden hafif ve nettir?",
        "choices": [
            "Daha hızlı ateş etmek için",
            "Atış sırasında nişan bozulmasın diye",
            "Geri tepmeyi azaltmak için",
            "Silahı daha sessiz yapmak için",
        ],
        "correct": 1,
    },
    {
        "q": "Spin drift nedir?",
        "choices": [
            "Rüzgârın mermiyi savurması",
            "Merminin yer çekimiyle düşmesi",
            "Merminin kendi dönüşü nedeniyle yan sapma yapması",
            "Optiğin paralaks hatası",
        ],
        "correct": 2,
    },
    {
        "q": ".308 Winchester kalibresi genellikle hangi amaçla tercih edilir?",
        "choices": [
            "Aşırı uzun mesafe rekorları",
            "Eğitim ve orta mesafe görevler",
            "Sadece avcılık",
            "Zırhlı hedefler",
        ],
        "correct": 1,
    },
    {
        "q": "Profesyonel keskin nişancılığı amatörden ayıran en temel unsur hangisidir?",
        "choices": [
            "Daha pahalı ekipman",
            "Fiziksel güç",
            "Veri disiplini ve ölçüm alışkanlığı",
            "Daha büyük kalibre",
        ],
        "correct": 2,
    },
]


# =========================
# PROFESYONEL TEMA (CSS)
# =========================
BASE_CSS = """
:root{
  --bg:#0b1220;
  --card:#0f1a2e;
  --muted:#9fb0c3;
  --text:#e7eef7;
  --line:#23314a;
  --accent:#6ea8fe;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
  background: radial-gradient(1200px 600px at 20% -10%, rgba(110,168,254,.18), transparent),
              radial-gradient(900px 500px at 110% 10%, rgba(120,255,214,.10), transparent),
              var(--bg);
  color:var(--text);
}
header{
  position:sticky; top:0; z-index:10;
  background: rgba(11,18,32,.82);
  backdrop-filter: blur(8px);
  border-bottom:1px solid var(--line);
  padding:16px;
}
.container{max-width:980px; margin:0 auto; padding:16px}
h1{margin:0; font-size:18px; letter-spacing:.2px}
.small{color:var(--muted); font-size:13px; margin-top:6px}
.card{
  background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  margin:12px 0;
}
.grid{display:grid; gap:12px}
@media (min-width:720px){ .grid.two{grid-template-columns:1fr 1fr} }
.label{font-weight:650; margin-bottom:6px; font-size:13px; color:var(--muted)}
input[type="text"], input[type="password"]{
  width:100%;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid var(--line);
  background: rgba(15,26,46,.65);
  color:var(--text);
  outline:none;
}
.option{
  display:block;
  padding:10px 12px;
  border:1px solid var(--line);
  border-radius:12px;
  margin:8px 0;
  background: rgba(15,26,46,.55);
}
.option:hover{border-color: rgba(110,168,254,.45)}
button{
  border:1px solid rgba(110,168,254,.35);
  background: linear-gradient(180deg, rgba(19,33,58,.9), rgba(15,26,46,.9));
  color:var(--text);
  padding:10px 14px;
  border-radius:12px;
  font-weight:750;
  cursor:pointer;
}
button.secondary{
  border-color: rgba(159,176,195,.25);
  background: rgba(15,26,46,.7);
}
.notice{
  padding:12px;
  border-radius:14px;
  border:1px dashed rgba(110,168,254,.35);
  color:var(--muted);
  background: rgba(15,26,46,.40);
}
table{width:100%; border-collapse:collapse; overflow:hidden; border-radius:14px; border:1px solid var(--line)}
th,td{padding:10px; border-bottom:1px solid var(--line); text-align:left; font-size:13px}
th{color:var(--muted); font-weight:750; background: rgba(15,26,46,.85)}
.mono{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace}
a{color:var(--accent); text-decoration:none}
"""

def no_store(resp):
    # Quiz bittiğinde kullanıcı geri tuşuyla cache’den soruları görmesin
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


# =========================
# 1) KULLANICI GİRİŞ (Ad/Soyad/Sicil)
# =========================
REGISTER_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Katılım</title>
<style>{{css}}</style>
</head><body>
<header>
  <div class="container">
    <h1>Keskin Nişancılık – 10 Soruluk Test</h1>
    <div class="small">Ad / Soyad / Sicil ile giriş yap. Her sicil 1 kez katılabilir.</div>
  </div>
</header>

<div class="container">
  {% if msg %}
    <div class="card notice">{{msg}}</div>
  {% endif %}

  <div class="card">
    <form method="post" action="/start">
      <div class="grid two">
        <div>
          <div class="label">Ad</div>
          <input type="text" name="first_name" required>
        </div>
        <div>
          <div class="label">Soyad</div>
          <input type="text" name="last_name" required>
        </div>
      </div>
      <div style="height:10px"></div>
      <div>
        <div class="label">Sicil</div>
        <input type="text" name="sicil" required>
      </div>
      <div style="height:14px"></div>
      <button type="submit">Teste Başla</button>
    </form>
  </div>

  <div class="small">Not: Sonuç katılımcıya gösterilmez; sadece admin panelde görünür.</div>
</div>
</body></html>
"""

@app.route("/", methods=["GET"])
def home():
    msg = request.args.get("msg", "")
    resp = make_response(render_template_string(REGISTER_PAGE, css=BASE_CSS, msg=msg))
    return no_store(resp)

@app.route("/start", methods=["POST"])
def start():
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    sicil = (request.form.get("sicil") or "").strip()

    if not first_name or not last_name or not sicil:
        return redirect(url_for("home", msg="Lütfen tüm alanları doldurun."))

    # Tek katılım kontrolü
    if sicil in SUBMITTED:
        return redirect(url_for("home", msg="Daha önce katılım sağladınız."))

    # Oturumda sakla
    session["user"] = {"first_name": first_name, "last_name": last_name, "sicil": sicil}
    return redirect(url_for("quiz"))


# =========================
# 2) QUIZ
# =========================
QUIZ_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test</title>
<style>{{css}}</style>
</head><body>
<header>
  <div class="container">
    <h1>Keskin Nişancılık – 10 Soruluk Test</h1>
    <div class="small">Katılımcı: <span class="mono">{{user.first_name}} {{user.last_name}}</span> • Sicil: <span class="mono">{{user.sicil}}</span></div>
  </div>
</header>

<div class="container">
  {% if done %}
    <div class="card notice">
      <div style="font-weight:800; color:var(--text)">Cevaplarınız alındı, teşekkürler.</div>
      <div class="small">Bu sicil ile tekrar katılım yapılamaz.</div>
    </div>
  {% elif blocked %}
    <div class="card notice">
      <div style="font-weight:800; color:var(--text)">Daha önce katılım sağladınız.</div>
      <div class="small">Bu sicil ile tekrar test açılamaz.</div>
    </div>
  {% else %}
    <form method="post">
      {% for i, item in enumerate(quiz) %}
        <div class="card">
          <div style="font-weight:800; margin-bottom:10px">{{i+1}}) {{item.q}}</div>
          {% for c_i, c in enumerate(item.choices) %}
            <label class="option">
              <input type="radio" name="q{{i}}" value="{{c_i}}" required>
              {{ "ABCD"[c_i] }}) {{c}}
            </label>
          {% endfor %}
        </div>
      {% endfor %}
      <button type="submit">Gönder</button>
    </form>
  {% endif %}

  <div style="height:8px"></div>
  <a class="small" href="/">Ana sayfa</a>
</div>
</body></html>
"""

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    user = session.get("user")
    if not user:
        return redirect(url_for("home", msg="Teste başlamadan önce bilgilerinizi girin."))

    sicil = (user.get("sicil") or "").strip()
    if not sicil:
        return redirect(url_for("home", msg="Sicil bilgisi eksik."))

    # Daha önce katıldıysa soru gösterme
    if sicil in SUBMITTED:
        resp = make_response(render_template_string(
            QUIZ_PAGE, css=BASE_CSS, user=user, quiz=QUIZ, enumerate=enumerate,
            done=False, blocked=True
        ))
        return no_store(resp)

    if request.method == "POST":
        score = 0
        for i, q in enumerate(QUIZ):
            v = request.form.get(f"q{i}")
            if v is not None and int(v) == q["correct"]:
                score += 1

        # IP KAYDI YOK — sadece kimlik + skor
        RESULTS.append({
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "sicil": sicil,
            "score": score,
            "total": len(QUIZ),
        })
        SUBMITTED.add(sicil)

        # Bitti: soruları tekrar göstermiyoruz
        resp = make_response(render_template_string(
            QUIZ_PAGE, css=BASE_CSS, user=user, quiz=QUIZ, enumerate=enumerate,
            done=True, blocked=False
        ))
        return no_store(resp)

    resp = make_response(render_template_string(
        QUIZ_PAGE, css=BASE_CSS, user=user, quiz=QUIZ, enumerate=enumerate,
        done=False, blocked=False
    ))
    return no_store(resp)


# =========================
# 3) ADMIN LOGIN (sayfada şifre gir)
# =========================
ADMIN_LOGIN_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Giriş</title>
<style>{{css}}</style>
</head><body>
<header><div class="container">
  <h1>Admin Panel</h1>
  <div class="small">Şifre ile giriş</div>
</div></header>

<div class="container">
  {% if msg %}<div class="card notice">{{msg}}</div>{% endif %}
  <div class="card">
    <form method="post">
      <div class="label">Admin Şifresi</div>
      <input type="password" name="password" required>
      <div style="height:14px"></div>
      <button type="submit">Giriş</button>
    </form>
  </div>
</div>
</body></html>
"""

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

    resp = make_response(render_template_string(ADMIN_LOGIN_PAGE, css=BASE_CSS, msg=msg))
    return no_store(resp)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# =========================
# 4) ADMIN DASHBOARD + CSV
# =========================
ADMIN_DASHBOARD_PAGE = """
<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin – Sonuçlar</title>
<style>{{css}}</style>
</head><body>
<header><div class="container">
  <h1>Admin – Sonuçlar</h1>
  <div class="small">
    Toplam kayıt: <span class="mono">{{count}}</span> •
    <a href="/admin/export.csv">CSV indir</a> •
    <a href="/admin/logout">Çıkış</a>
  </div>
</div></header>

<div class="container">
  <div class="card">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Zaman (UTC)</th>
          <th>Ad</th>
          <th>Soyad</th>
          <th>Sicil</th>
          <th>Skor</th>
        </tr>
      </thead>
      <tbody>
        {% if rows %}
          {% for r in rows %}
            <tr>
              <td>{{loop.index}}</td>
              <td class="mono">{{r.ts}}</td>
              <td>{{r.first_name}}</td>
              <td>{{r.last_name}}</td>
              <td class="mono">{{r.sicil}}</td>
              <td class="mono">{{r.score}}/{{r.total}}</td>
            </tr>
          {% endfor %}
        {% else %}
          <tr><td colspan="6">Henüz sonuç yok.</td></tr>
        {% endif %}
      </tbody>
    </table>
  </div>
</div>
</body></html>
"""

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("admin") is not True:
        return redirect(url_for("admin_login"))

    rows = list(reversed(RESULTS))  # en yeni en üstte
    resp = make_response(render_template_string(
        ADMIN_DASHBOARD_PAGE, css=BASE_CSS, rows=rows, count=len(RESULTS)
    ))
    return no_store(resp)

@app.route("/admin/export.csv")
def admin_export_csv():
    if session.get("admin") is not True:
        return redirect(url_for("admin_login"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ts_utc", "first_name", "last_name", "sicil", "score", "total"])

    for r in RESULTS:
        writer.writerow([r["ts"], r["first_name"], r["last_name"], r["sicil"], r["score"], r["total"]])

    data = output.getvalue().encode("utf-8")
    resp = make_response(data)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = 'attachment; filename="sonuclar.csv"'
    return no_store(resp)


# =========================
# ÇALIŞTIRMA
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
