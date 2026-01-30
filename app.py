import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

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
        "explain": "İlk atış sonrası hedef çoğu zaman saklanır/yer değiştirir ya da karşılık verir."
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
        "explain": "BC, merminin havada sürüklemeye karşı aerodinamik verimliliğini temsil eder."
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
        "explain": "Uzun mesafede yatay sapmaların ana kaynağı rüzgâr tahmin/okumadır."
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
        "explain": "DOPE: Sahada ölçülmüş gerçek verilerle oluşturulan klik/hold ayarlarının kaydıdır."
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
        "explain": "Mirage desenleri rüzgârın yön/şiddeti için güçlü ipucudur."
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
        "explain": "Dünya’nın dönüşü etkisi; uçuş süresi uzadıkça ve hassasiyet arttıkça anlamlı olur."
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
        "explain": "Tetiğe kuvvet uygularken nişanı bozmamak için hafif ve kırılması net tetik tercih edilir."
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
        "explain": "Merminin dönüşünden kaynaklı yan sapma; rüzgâr değil fiziksel etkidir."
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
        "explain": ".308; yönetilebilir geri tepme ve yaygın lojistik nedeniyle eğitim/orta mesafede sık kullanılır."
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
        "explain": "Tutarlılık; ölçüm, kayıt ve sistematik değerlendirmeden gelir."
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
    .ok{border-color:#1f6f43;background:rgba(31,111,67,.12)}
    .bad{border-color:#8a2a2a;background:rgba(138,42,42,.12)}
    .explain{margin-top:8px;color:#b6c2d0;font-size:13px}
  </style>
</head>
<body>
<header>
  <h1>Keskin Nişancılık – 10 Soruluk Test</h1>
  <div class="muted">Tek doğru seçenek. Bitince sonucu gör.</div>
</header>
<main>
  <form method="post">
    {% for i, item in enumerate(quiz) %}
      <div class="card">
        <div class="q">{{i+1}}) {{item.q}}</div>
        {% for c_i, c in enumerate(item.choices) %}
          <label class="{% if show %}{% if answers[i] is not none and c_i==item.correct %}ok{% elif answers[i]==c_i and c_i!=item.correct %}bad{% endif %}{% endif %}">
            <input type="radio" name="q{{i}}" value="{{c_i}}" {% if answers[i]==c_i %}checked{% endif %} {% if show %}disabled{% endif %}>
            {{ "ABCD"[c_i] }}) {{c}}
          </label>
        {% endfor %}
        {% if show %}
          <div class="explain"><b>Doğru:</b> {{ "ABCD"[item.correct] }} — {{ item.explain }}</div>
        {% endif %}
      </div>
    {% endfor %}

    {% if not show %}
      <button type="submit">Sonucu Gör</button>
    {% else %}
      <div class="card">
        <div class="q">Skor: {{score}} / {{quiz|length}}</div>
        <div class="muted">Yanlışlar: {{wrong}}</div>
      </div>
      <a href="/"><button type="button">Tekrar Başlat</button></a>
    {% endif %}
  </form>
</main>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    answers = [None] * len(QUIZ)
    show = False
    score = 0
    wrong = 0

    if request.method == "POST":
        show = True
        for i in range(len(QUIZ)):
            v = request.form.get(f"q{i}")
            answers[i] = int(v) if v is not None else None

        for i, item in enumerate(QUIZ):
            if answers[i] == item["correct"]:
                score += 1
            else:
                wrong += 1

    return render_template_string(
        PAGE,
        quiz=QUIZ,
        answers=answers,
        show=show,
        score=score,
        wrong=wrong,
        enumerate=enumerate,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

