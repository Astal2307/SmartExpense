from __future__ import annotations

import os
from typing import Tuple

import joblib


MODEL_PATH = os.getenv("MODEL_PATH", os.path.join("models", "expense_classifier.joblib"))


class RuleBasedClassifier:

    def __init__(self) -> None:
        self.default_category = "Другое"

    def _classify_text(self, text: str) -> Tuple[str, float]:
        t = text.lower()

        rules = [
            (["такси", "yandex go", "яндекс go"], "Транспорт"),
            (["метро", "mcdonalds", "макдональдс", "kfc"], "Рестораны"),
            (["магазин", "магнит", "пятерочка", "пятёрочка", "перекресток", "перекрёсток"], "Продукты"),
            (["steam", "игра", "cinema", "кино", "ivi", "okko"], "Развлечения"),
            (["подписка", "subscription", "spotify", "netflix", "yandex plus", "яндекс плюс"], "Подписки"),
            (["жкх", "коммунал", "электричеств", "газ", "вода"], "Коммунальные услуги"),
            (["аптека", "лекарств", "здоров"], "Здоровье"),
            (["телефон", "связь", "мегафон", "билайн", "tele2", "ростелеком"], "Связь"),
            (["перевод", "p2p", "transfer"], "Переводы"),
        ]

        for keywords, category in rules:
            if any(k in t for k in keywords):
                return category, 0.7

        return self.default_category, 0.5

    def predict(self, texts):
        return [self._classify_text(text)[0] for text in texts]

    def predict_proba(self, texts):
        return [[self._classify_text(text)[1]] for text in texts]


def load_model():
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            return model
        except Exception:
            pass
    return RuleBasedClassifier()


def classify_text(model, text: str) -> Tuple[str, float]:
    if hasattr(model, "predict_proba"):
        label = model.predict([text])[0]
        proba = model.predict_proba([text])[0]
        confidence = float(proba.max())
        return label, confidence

    label = model.predict([text])[0]
    return label, 0.5

