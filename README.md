## SmartExpense — API для классификации и аналитики трат

**Идея**: отправляете банковскую транзакцию в виде текста, сервер сам определяет категорию (модель TF‑IDF + Logistic Regression), сохраняет в PostgreSQL и отдаёт аналитику.

---

### Стек

- **Backend**: `FastAPI`
- **БД**: `PostgreSQL` (через `SQLAlchemy`)
- **ML**: `scikit-learn`, `joblib`
- **Прочее**: `uvicorn`, `docker`

---

### Установка локально

1. Создайте и активируйте виртуальное окружение:

```bash
cd SmartExpense
python -m venv .venv
.venv\Scripts\activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Поднимите PostgreSQL.

По умолчанию используется:

```text
postgresql+psycopg2://postgres:123456@localhost:5432/smart_expense
```

Можно переопределить через переменную окружения `DATABASE_URL`.

4. Обучите ML-модель (один раз):

```bash
python train.py
```

Это создаст файл `models/expense_classifier.joblib`.

5. Запустите API-сервер:

```bash
uvicorn app.main:app --reload
```

Документация будет по адресу `http://127.0.0.1:8000/docs`.

---

### Запуск через Docker

1. Соберите образ:

```bash
docker build -t smartexpense .
```

Во время сборки вызовется `python train.py` и модель обучится внутри образа.

2. Запустите контейнер, прокинув `DATABASE_URL`:

```bash
docker run -p 8000:8000 ^
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/smart_expense ^
  smartexpense
```

---

### Основные эндпоинты

- **1. Добавить транзакцию**

  `POST /api/v1/transactions`

  Тело:

  ```json
  {
    "description": "Магнит продукты",
    "amount": 1500.50,
    "date": "2025-06-01T12:00:00"
  }
  ```

  Ответ: транзакция с определённой категорией и уверенностью модели.
- **2. Загрузить CSV**

  `POST /api/v1/transactions/upload`

  Ожидается `multipart/form-data` с полем `file` (CSV) формата:

  ```text
  description,amount,date
  Магнит продукты,1500.50,2025-06-01T12:00:00
  Яндекс Go такси,350.00,2025-06-01T13:00:00
  ```
- **3. Получить список транзакций**

  `GET /api/v1/transactions?category=Продукты&limit=50`

  Параметры:

  - `category` — необязательный фильтр по категории
  - `limit` — максимум записей (по умолчанию 50)
- **4. Удалить транзакцию**

  `DELETE /api/v1/transactions/{id}`
- **5. Аналитика**

  `GET /api/v1/analytics`

  Возвращает:

  - общую сумму трат
  - общее количество транзакций
  - агрегаты по категориям
  - агрегаты по месяцам (`YYYY-MM`)

---

### ML-часть

- Модель: `TF-IDF -> LogisticRegression`
- Данные: синтетические, зашиты в `train.py` (`build_synthetic_dataset`)
- Сохранение: `models/expense_classifier.joblib`
- В рантайме:
  - сначала пытаемся загрузить модель (`app.ml.load_model`)
  - если не получилось — используется простой rule-based классификатор по подстрокам (`такси` → `Транспорт`, `Магнит`/`Пятёрочка` → `Продукты` и т.д.)

Это гарантирует, что API работает даже без предварительного обучения.
