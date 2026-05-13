import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    print("✅ Simulateur connecté au broker")
    client.subscribe("traffic/cmd")
    print("👂 Abonné à traffic/cmd")

def on_message(client, userdata, msg):
    print(f"🚨 Commande reçue : {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.emqx.io", 1883, 60)
client.loop_start()  # thread automatique

voies = ["nord", "sud", "est", "ouest"]
etats = ["VERT", "JAUNE", "ROUGE"]
densites = ["FAIBLE", "MOYENNE", "ELEVEE"]
durees = [5, 8, 10, 13]

for i in range(60):  # tourne plus longtemps pour laisser le temps de cliquer
    voie = voies[i % 4]
    msg = {
        "voie": voie,
        "etat_feu": etats[i % 3],
        "densite": densites[i % 3],
        "duree_vert": durees[i % 4]
    }
    client.publish("traffic/data", json.dumps(msg))
    print("Publié :", msg)
    time.sleep(3)