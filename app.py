import os
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Render > Environment'da ADMIN_KEY tanımla (kodda görünmesin)
ADMIN_KEY = os.environ.get("ADMIN_KEY", "degistir_bunu")

# Basit bellek içi kayıt (Render free restart ederse sıfırlanabilir)
RESULTS = []

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

PAGE = """
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Keskin Nişancılık – 10 Soruluk Test</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:0;background:#0b0f14;color:#e6edf3}
  header{position:sticky;top:0;background:#0b0f14;border-bottom:1px solid #1f2a37;padding:16px}
  h1{margin:0;font-size:18px}
  main{max-width:900px;margin:0 auto;padding:16px}
  .card{background:#0f1620;border:1px solid #1f2a37;border-radius:14px;padding:14px;margin:12px 0}
  .q{font-weight:700;margin-bottom:10px}
  label{display:block;padding:10px 12px;border:1px solid #223246;border-radius:12px;margin:8px 0;background:#0b111a}
  input{transform:scale(1.1);margin-right:10px}
  button{border:1px solid #2a3a52;background:#111b28;color:#e6edf3;padding:10px 14px;border-radius:12px;font-weight:700;cursor:pointer}
  .muted{color:#9aa4b2;font-size:13px}
</style>
</head>
<body>
<header>
  <h1>Keskin Nişancılık – 10 Soruluk Test</h1>
  <div class="muted">Tek doğru seçenek. Sonuçlar katılımcıya gösterilmez.</div>
</header>

<main>
  <form method="post">
    {% for i, item in enumerate(quiz) %}
      <div class="card">
        <div class="q">{{i+1}}) {{item.q}}</div>
        {% for c_i, c in enumerate(item.choices) %}
          <label>
            <input type="radio" name="q{{i}}" value="{{c_i}}" required>
            {{ "ABCD"[c_i] }}) {{c}}
          </label>
        {% endfor %}
      </div>
    {% endfor %}

    {% if not show %}
      <button type="submit">Gönder</button>
    {% else %}
      <div class="card">
        <div class="q">Cevaplarınız kaydedildi.</div>
        <div class="muted">Teşekkürler.</div>
      </div>
      <a href="/"><button type="button">Yeni Test</button></a>
    {% endif %}
  </form>
</main>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    show = False
    score = 0

    if request.method == "POST":
        show = True

        for i, q in enumerate(QUIZ):
            v = request.form.get(f"q{i}")
            if v is not None and int(v) == q["correct"]:
                score += 1

        RESULTS.append({
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "score": score,
            "total": len(QUIZ),
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        })

    return render_template_string(PAGE, quiz=QUIZ, show=show, enumerate=enumerate)

@app.route("/admin")
def admin():
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        return "Yetkisiz erişim", 403

    rows = []
    for i, r in enumerate(reversed(RESULTS), start=1):
        rows.append(f"<tr><td>{i}</td><td>{r['ts']}</td><td>{r['ip']}</td><td>{r['score']}/{r['total']}</td></tr>")

    html = f"""
    <!doctype html><html lang="tr"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Admin – Sonuçlar</title>
    <style>
      body{{font-family:system-ui;margin:0;padding:16px;background:#0b0f14;color:#e6edf3}}
      table{{width:100%;border-collapse:collapse;background:#0f1620;border:1px solid #1f2a37;border-radius:12px;overflow:hidden}}
      th,td{{padding:10px;border-bottom:1px solid #1f2a37;text-align:left}}
      th{{background:#111b28}}
      .muted{{color:#9aa4b2;font-size:13px;margin:10px 0}}
    </style>
    </head><body>
      <h2>Sonuçlar</h2>
      <div class="muted">Toplam kayıt: {len(RESULTS)}</div>
      <table>
        <thead><tr><th>#</th><th>Zaman (UTC)</th><th>IP</th><th>Skor</th></tr></thead>
        <tbody>{"".join(rows) if rows else "<tr><td colspan='4'>Henüz sonuç yok.</td></tr>"}</tbody>
      </table>
    </body></html>
    """
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
    