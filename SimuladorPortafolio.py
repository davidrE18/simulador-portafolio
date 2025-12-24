import streamlit as st
import pandas as pd

# =========================
# CONFIGURACIÓN
# =========================
st.set_page_config(layout="wide")

# =========================
# USUARIOS (LOGIN MVP)
# =========================
USUARIOS = {
    "admin": "admin123",
    "comercial": "ventas2025",
    "gerencia": "luker2025"
}

# =========================
# FUNCIÓN LOGIN
# =========================
def login():
    st.title("🔐 Acceso al Simulador de Portafolio")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario in USUARIOS and USUARIOS[usuario] == password:
            st.session_state["login_ok"] = True
            st.session_state["usuario"] = usuario
            st.success("Acceso correcto")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# =========================
# CONTROL DE SESIÓN
# =========================
if "login_ok" not in st.session_state:
    st.session_state["login_ok"] = False

if not st.session_state["login_ok"]:
    login()
    st.stop()

# =========================
# APP PRINCIPAL
# =========================
st.title("📊 Simulador de Portafolio")
st.caption(f"Usuario conectado: **{st.session_state['usuario']}**")

# =========================
# BOTÓN LOGOUT
# =========================
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

# =========================
# DATOS BASE
# =========================
archivo = "PortafolioFoco.xlsx"
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
df.columns = (
    df.columns
      .str.strip()
      .str.lower()
      .str.replace(" ", "_")
)

# =========================
# LIMPIEZA DE DATOS
# =========================
for c in ["kilos", "venta", "dn", "caf"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

canales = st.sidebar.multiselect(
    "Canal",
    options=sorted(df["nombre_canal"].unique()),
    default=df["nombre_canal"].unique()
)

clientes = st.sidebar.multiselect(
    "Grupo Cliente",
    options=sorted(df["nombre_g_cliente"].unique()),
    default=df["nombre_g_cliente"].unique()
)

categorias = st.sidebar.multiselect(
    "Categoría",
    options=sorted(df["categoria"].unique()),
    default=df["categoria"].unique()
)

oficinas = st.sidebar.multiselect(
    "Oficinas",
    options=sorted(df["nombre_oficina_ventas"].dropna().unique()),
    default=df["nombre_oficina_ventas"].dropna().unique()
)

# Aplicar filtros
df_f = df[
    (df["nombre_canal"].isin(canales)) &
    (df["nombre_g_cliente"].isin(clientes)) &
    (df["categoria"].isin(categorias)) &
    (df["nombre_oficina_ventas"].isin(oficinas))
].copy()

# =========================
# NORMALIZACIÓN
# =========================
for c in ["kilos", "venta", "dn", "caf"]:
    if df_f[c].nunique() > 1:
        df_f[c + "_norm"] = df_f[c].rank(pct=True)
    else:
        df_f[c + "_norm"] = 0

# =========================
# PESOS
# =========================
st.sidebar.header("🎛️ Pesos del modelo (%)")

w_kilos = st.sidebar.slider("Kilos", 0, 100, 25)
w_venta = st.sidebar.slider("Ventas $", 0, 100, 25)
w_dn    = st.sidebar.slider("Distribución Numérica", 0, 100, 25)
w_caf   = st.sidebar.slider("CAF", 0, 100, 25)

total = w_kilos + w_venta + w_dn + w_caf
st.sidebar.metric("Suma pesos", f"{total}%")

if total != 100:
    st.sidebar.warning("⚠️ Ajusta los pesos a 100%")

# =========================
# SCORE Y RANKING
# =========================
df_f["score"] = (
    df_f["kilos_norm"] * w_kilos +
    df_f["venta_norm"] * w_venta +
    df_f["dn_norm"]    * w_dn +
    df_f["caf_norm"]   * w_caf
) / 100

df_f["ranking"] = df_f["score"].rank(ascending=False, method="first")

# =========================
# DATAFRAME FINAL (LIMPIO)
# =========================
df_show = df_f.drop(
    columns=["kilos_norm", "venta_norm", "dn_norm", "caf_norm"],
    errors="ignore"
)

from io import BytesIO

st.markdown("### 📥 Exportar resultados")

buffer = BytesIO()

with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df_show.sort_values("ranking").to_excel(
        writer,
        index=False,
        sheet_name="Ranking"
    )

st.download_button(
    label="⬇️ Descargar Excel (.xlsx)",
    data=buffer.getvalue(),
    file_name="ranking_portafolio.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# OUTPUT
# =========================
st.subheader("📌 Ranking dinámico del portafolio")

st.dataframe(
    df_show.sort_values("ranking"),
    use_container_width=True
)