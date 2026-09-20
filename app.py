
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Painel de Ações</title>

<style>
body {
    margin: 0;
    padding: 16px;
    background: #101820;
    color: white;
    font-family: Arial, sans-serif;
}
h1 { color: #38bdf8; font-size: 25px; }
.grid {
    display: grid;
    grid-template-columns: repeat(
        auto-fit, minmax(210px, 1fr)
    );
    gap: 12px;
}
.card {
    background: #1e293b;
    padding: 18px;
    border-radius: 12px;
}
.ticker { color: #94a3b8; font-size: 18px; }
.price { font-size: 30px; margin: 12px 0; }
.info { color: #94a3b8; font-size: 14px; }
.status { color: #fbbf24; }
</style>
</head>

<body>
<h1>📈 Painel de Ações</h1>
<p class="info">Monitoramento da Bolsa • Raspberry Pi 3</p>

<div class="grid">
    {% for ticker in tickers %}
    <div class="card">
        <div class="ticker">{{ ticker }}</div>
        <div class="price">Aguardando cotação</div>
        <div class="status">● Conectando dados...</div>
    </div>
    {% endfor %}
</div>

<p class="info" style="margin-top:25px">
    Atualização automática da página a cada 60 segundos.
</p>
</body>
</html>
"""

@app.route("/")
def index():
    tickers = [
        "PETR4.SA",
        "ITUB4.SA",
        "PSSA3.SA",
        "AAPL",
        "MSFT",
        "NVDA"
    ]
    return render_template_string(HTML, tickers=tickers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
