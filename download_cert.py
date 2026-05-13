import requests

url = "https://test.mosquitto.org/ssl/mosquitto.org.crt"
response = requests.get(url)

with open("mosquitto_ca.crt", "wb") as f:
    f.write(response.content)

print("✅ Certificat téléchargé : mosquitto_ca.crt")