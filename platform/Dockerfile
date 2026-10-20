FROM python:3.11-slim
WORKDIR /app
COPY platform/requirements.txt .
COPY platform/vendor ./vendor
RUN pip install --no-cache-dir -r requirements.txt
COPY platform/app.py platform/risk.py ./
COPY platform/accounts.py platform/account_routes.py ./
COPY platform/templates ./templates
COPY platform/static ./static
COPY platform/artifacts ./artifacts
COPY platform/docs ./docs
COPY data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf /data/fira/context/
ENV PORT=5000
EXPOSE 5000
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
