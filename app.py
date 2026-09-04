from flask import Flask, jsonify
import redis
import os

# Crea la aplicación web Flask.
app = Flask(__name__)

# Conexión a Redis local en el puerto 6379.
# Ambos backends compartirán este mismo contador.
r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# Obtiene el puerto desde una variable de entorno.
# Así usamos el mismo archivo para los puertos 5001 y 5002.
PORT = int(os.environ.get("PORT", 5001))


@app.route("/")
def index():

    # Incrementa de forma atómica el contador compartido en Redis.
    total = r.incr("peticiones_totales")

    # Devuelve qué nodo respondió y el total acumulado.
    return jsonify({
        "nodo": PORT,
        "total_redis": total
    })


if __name__ == "__main__":

    # Inicia Flask escuchando en todas las interfaces.
    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )