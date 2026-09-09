from flask import Flask, jsonify
import redis
import os
import time

app = Flask(__name__)

# Conexión a Redis.
r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# Puerto del nodo: 5001 o 5002.
PORT = int(os.environ.get("PORT", 5001))

# Rate Limiting.
RATE_LIMIT = 30
RATE_WINDOW = 10

# Caché.
CACHE_KEY = "cache:reporte_pesado"
CACHE_TTL = 10


@app.route("/")
def index():
    # Funcionalidad original del Taller 1.
    total = r.incr("peticiones_totales")

    return jsonify({
        "nodo": PORT,
        "total_redis": total
    })


@app.route("/api")
def api():

    # -----------------------------
    # RATE LIMITING
    # -----------------------------

    peticiones = r.incr("ratelimit:global")

    # La primera petición inicia la ventana de 10 segundos.
    if peticiones == 1:
        r.expire("ratelimit:global", RATE_WINDOW)

    # Después de 30 peticiones responde HTTP 429.
    if peticiones > RATE_LIMIT:
        return jsonify({
            "error": "Too Many Requests",
            "limite": RATE_LIMIT,
            "ventana_segundos": RATE_WINDOW
        }), 429


    # -----------------------------
    # MÉTRICAS POR NODO
    # -----------------------------

    nodo = f"nodo_{PORT}"

    # Incrementa el contador específico del nodo
    # dentro del Hash metricas:nodos.
    contador_nodo = r.hincrby(
        "metricas:nodos",
        nodo,
        1
    )


    # -----------------------------
    # CACHÉ DISTRIBUIDO
    # -----------------------------

    dato_cache = r.get(CACHE_KEY)

    if dato_cache is not None:

        # El dato ya estaba calculado.
        estado_cache = "HIT"
        resultado = dato_cache

    else:

        # Simula un cálculo pesado de 100 ms.
        estado_cache = "MISS"

        time.sleep(0.1)

        resultado = "reporte_generado"

        # Guarda el resultado durante 10 segundos.
        r.setex(
            CACHE_KEY,
            CACHE_TTL,
            resultado
        )


    return jsonify({
        "nodo": PORT,
        "metricas_nodo": contador_nodo,
        "cache": estado_cache,
        "resultado": resultado,
        "rate_limit": peticiones
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )
