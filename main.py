DB_USER=budget_user
DB_PASSWORD=budget123
DB_HOST=budget-oracle
DB_PORT=1521
DB_SERVICE=FREEPDB1

DATABASE_URL=oracle+oracledb://budget_user:budget123@budget-oracle:1521/FREEPDB1

JWT_SECRET_KEY=my_super_secret_key_2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

EMAIL_ADDRESS=your_email_here
EMAIL_PASSWORD=your_email_password_here

GEMINI_API_KEY=your_gemini_key_here

RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxx
----------------------------------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
--------------------------
venv
__pycache__
*.pyc
.env
backend.env.docker
.git
.gitignore
alembic/versions/__pycache__
----------------------------------
docker run -d \
  --name budgetpro-backend \
  --env-file ./budget-management-backend/backend.env.docker \
  --network budget-net \
  -p 8000:8000 \
  budgetpro-backend:dev
  -------------------------
  