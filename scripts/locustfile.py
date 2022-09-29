import json

from locust import HttpUser, task


class MuseUser(HttpUser):
    @task
    def predict(self):
        data = {"dream": "A purple cloud with Lightning", "high_quality": False}
        URL = f"{self.host}/api/predict"
        print(self.host, URL)
        data = json.dumps(data)
        response = self.client.post(URL, data=data, timeout=120)
        response.raise_for_status()
