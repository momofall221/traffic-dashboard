from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
socketio = SocketIO(app)

USERNAME = "admin"
PASSWORD = "traffic2026"

voies = {
    "nord":  {"feu": "ROUGE", "densite": "FAIBLE", "duree": 0},
    "sud":   {"feu": "ROUGE", "densite": "FAIBLE", "duree": 0},
    "est":   {"feu": "ROUGE", "densite": "FAIBLE", "duree": 0},
    "ouest": {"feu": "ROUGE", "densite": "FAIBLE", "duree": 0}
}

historique = []

# Client MQTT global (pour pouvoir publier depuis les routes)
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("✅ Connecté au broker MQTT")
    client.subscribe("traffic/data")

def on_message(client, userdata, msg):
    global voies, historique
    data = json.loads(msg.payload.decode())
    print("📩 Reçu :", data)
    voie = data.get("voie", "nord")
    if voie in voies:
        voies[voie]["feu"] = data.get("etat_feu", "ROUGE")
        voies[voie]["densite"] = data.get("densite", "FAIBLE")
        voies[voie]["duree"] = data.get("duree_vert", 0)

    evenement = {
        "heure": datetime.now().strftime("%H:%M:%S"),
        "voie": voie,
        "feu": data.get("etat_feu", "?"),
        "densite": data.get("densite", "?"),
        "duree": data.get("duree_vert", 0)
    }
    historique.append(evenement)
    if len(historique) > 20:
        historique.pop(0)

    socketio.emit('update', {
        "voies": voies,
        "historique": historique
    })

def demarrer_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect("broker.emqx.io", 1883, 60)
    mqtt_client.loop_forever()

thread = threading.Thread(target=demarrer_mqtt, daemon=True)
thread.start()

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Identifiant ou mot de passe incorrect.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- Nouvelle route pour forcer le feu vert ---
@app.route('/forcer_vert', methods=['POST'])
def forcer_vert():
    if not session.get('logged_in'):
        return jsonify({"status": "non autorisé"}), 403
    voie = request.form.get('voie')
    if voie in voies:
        commande = {"voie": voie, "action": "forcer_vert"}
        mqtt_client.publish("traffic/cmd", json.dumps(commande))
        print(f"🚨 Commande envoyée : {commande}")
        return jsonify({"status": "ok", "voie": voie})
    return jsonify({"status": "erreur", "message": "voie inconnue"}), 400

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)