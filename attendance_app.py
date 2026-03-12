import streamlit as st
import pandas as pd
from io import BytesIO
import base64
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PRESENSI ONLINE | FIPP UNNES",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2e86de 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: #cce0ff; margin: 0.2rem 0 0 0; font-size: 0.9rem; }
    .metric-card {
        background: white;
        border-left: 4px solid #2e86de;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,.08);
        margin-bottom: 1rem;
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #1e3a5f; }
    .metric-card .label { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: .05em; }
    .badge-hadir   { background:#d4edda; color:#155724; padding:3px 10px; border-radius:20px; font-size:.8rem; }
    .badge-alpha   { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:.8rem; }
    .badge-izin    { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:20px; font-size:.8rem; }
    .badge-sakit   { background:#d1ecf1; color:#0c5460; padding:3px 10px; border-radius:20px; font-size:.8rem; }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    div[data-testid="stSidebarContent"] { background: #f0f4f8; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>📋 Sistem Presensi Online Canggih</h1>
  <p>Upload daftar mahasiswa · Catat kehadiran · Rekap & Unduh — FIPP UNNES</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
STATUS_OPTIONS  = ["Hadir", "Alpha", "Izin", "Sakit"]
STATUS_COLORS   = {"Hadir":"#28a745","Alpha":"#dc3545","Izin":"#ffc107","Sakit":"#17a2b8"}

def load_excel(file):
    try:
        xls = pd.ExcelFile(file)
        sheets = {s: xls.parse(s) for s in xls.sheet_names}
        return sheets, None
    except Exception as e:
        return None, str(e)

def df_to_excel_bytes(sheets_dict):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, df in sheets_dict.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
    return buf.getvalue()

def download_link(data, filename, label="📥 Unduh Excel"):
    b64 = base64.b64encode(data).decode()
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return f'<a href="data:{mime};base64,{b64}" download="{filename}" style="text-decoration:none;background:#2e86de;color:white;padding:8px 18px;border-radius:8px;font-weight:600;">{label}</a>'

def get_date_cols(df):
    return [c for c in df.columns if c not in ("Nama","NIM","Program Studi","Angkatan","No")]

def pct_hadir(row, date_cols):
    if not date_cols: return 0
    return round(sum(row[c]=="Hadir" for c in date_cols)/len(date_cols)*100, 1)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "sheets" not in st.session_state:
    st.session_state.sheets = {}
if "file_name" not in st.session_state:
    st.session_state.file_name = "presensi_baru.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📁 Sumber Data")
    mode = st.radio("Pilih mode:", ["Upload Excel", "Buat Baru (kosong)"], horizontal=True)

    if mode == "Upload Excel":
        up = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
        if up:
            sheets, err = load_excel(up)
            if err:
                st.error(err)
            else:
                st.session_state.sheets   = sheets
                st.session_state.file_name = up.name
                st.success(f"✅ {len(sheets)} sheet dimuat.")
    else:
        mk_name = st.text_input("Nama Mata Kuliah / Sheet Baru", value="MataKuliah_Baru")
        if st.button("➕ Buat Sheet Kosong"):
            new_df = pd.DataFrame(columns=["No","NIM","Nama","Program Studi","Angkatan"])
            st.session_state.sheets[mk_name] = new_df
            st.success(f"Sheet '{mk_name}' ditambahkan.")

    st.markdown("---")
    st.markdown("## 📌 Menu")
    menu = st.radio("Navigasi:", [
        "🏠 Dashboard",
        "👥 Kelola Daftar Nama",
        "✅ Input Presensi",
        "📊 Rekap & Statistik",
        "🔁 Tambah / Hapus Sheet",
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PILIH SHEET
# ─────────────────────────────────────────────────────────────────────────────
sheets = st.session_state.sheets
if not sheets:
    st.info("ℹ️ Belum ada data. Silakan upload Excel atau buat sheet baru via sidebar.")
    st.stop()

sheet_names = list(sheets.keys())

# ─────────────────────────────────────────────────────────────────────────────
# ██  HALAMAN: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🏠 Dashboard":
    st.subheader("🏠 Dashboard Ringkasan")

    total_sheets = len(sheets)
    total_mahasiswa = sum(len(df) for df in sheets.values())
    total_pertemuan = sum(len(get_date_cols(df)) for df in sheets.values())

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="value">{total_sheets}</div><div class="label">Mata Kuliah</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="value">{total_mahasiswa}</div><div class="label">Total Mahasiswa (semua MK)</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="value">{total_pertemuan}</div><div class="label">Total Pertemuan (semua MK)</div></div>', unsafe_allow_html=True)

    st.markdown("### Daftar Mata Kuliah")
    rows = []
    for sn, df in sheets.items():
        dcols = get_date_cols(df)
        n_mhs  = len(df)
        n_tm   = len(dcols)
        if n_mhs > 0 and n_tm > 0:
            avg_h = round(df.apply(lambda r: sum(r[c]=="Hadir" for c in dcols), axis=1).mean() / n_tm * 100, 1) if n_tm else 0
        else:
            avg_h = 0
        rows.append({"Mata Kuliah": sn, "Jumlah Mahasiswa": n_mhs, "Pertemuan": n_tm, "Rata-rata Kehadiran (%)": avg_h})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# ██  HALAMAN: KELOLA DAFTAR NAMA
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "👥 Kelola Daftar Nama":
    st.subheader("👥 Kelola Daftar Nama Mahasiswa")
    sel = st.selectbox("Pilih Mata Kuliah:", sheet_names)
    df  = sheets[sel].copy()

    # Pastikan kolom dasar ada
    for col in ["No","NIM","Nama","Program Studi","Angkatan"]:
        if col not in df.columns:
            df[col] = ""

    st.markdown("**Edit tabel di bawah** — tambah baris baru, ubah data, atau hapus baris:")
    base_cols = ["No","NIM","Nama","Program Studi","Angkatan"]
    date_cols = get_date_cols(df)
    edited = st.data_editor(
        df[base_cols + date_cols] if date_cols else df[base_cols],
        num_rows="dynamic",
        use_container_width=True,
        key=f"edit_{sel}",
        column_config={
            "No":              st.column_config.NumberColumn("No.", min_value=1, step=1),
            "NIM":             st.column_config.TextColumn("NIM"),
            "Nama":            st.column_config.TextColumn("Nama Lengkap"),
            "Program Studi":   st.column_config.TextColumn("Prodi"),
            "Angkatan":        st.column_config.NumberColumn("Angkatan", min_value=2000, max_value=2099, step=1),
        }
    )
    if st.button("💾 Simpan Perubahan Daftar Nama", type="primary"):
        sheets[sel] = edited
        st.session_state.sheets = sheets
        st.success("Daftar nama berhasil disimpan.")

# ─────────────────────────────────────────────────────────────────────────────
# ██  HALAMAN: INPUT PRESENSI
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "✅ Input Presensi":
    st.subheader("✅ Input Presensi")
    sel = st.selectbox("Pilih Mata Kuliah:", sheet_names)
    df  = sheets[sel].copy()

    if "Nama" not in df.columns or df.empty:
        st.warning("Sheet ini belum memiliki data mahasiswa. Silakan isi terlebih dahulu di menu Kelola Daftar Nama.")
        st.stop()

    col1, col2 = st.columns([2,2])
    with col1:
        tgl = st.date_input("📅 Tanggal Pertemuan:", value=date.today())
        tgl_str = tgl.strftime("%Y-%m-%d")
    with col2:
        pertemuan_ke = st.number_input("Pertemuan ke-", min_value=1, max_value=99, value=len(get_date_cols(df))+1)
        col_label = f"P{pertemuan_ke}_{tgl_str}"

    add_col = st.button("➕ Tambah Kolom Pertemuan Ini", type="primary")
    if add_col:
        if col_label not in df.columns:
            df[col_label] = "Alpha"
            sheets[sel] = df
            st.session_state.sheets = sheets
            st.success(f"Kolom '{col_label}' ditambahkan. Silakan isi status kehadiran di bawah.")
            st.rerun()
        else:
            st.info(f"Kolom '{col_label}' sudah ada.")

    date_cols = get_date_cols(df)
    if not date_cols:
        st.info("Belum ada kolom pertemuan. Tambahkan dulu dengan tombol di atas.")
        st.stop()

    selected_col = st.selectbox("Pilih pertemuan yang ingin diisi:", date_cols, index=len(date_cols)-1)

    st.markdown(f"**Status kehadiran untuk: `{selected_col}`**")
    st.caption("Klik pada kolom Status untuk mengubah: Hadir / Alpha / Izin / Sakit")

    if selected_col not in df.columns:
        df[selected_col] = "Alpha"

    edit_df = df[["No","NIM","Nama",selected_col]].copy()
    edited_pres = st.data_editor(
        edit_df,
        column_config={
            "No":          st.column_config.NumberColumn("No.", disabled=True),
            "NIM":         st.column_config.TextColumn("NIM", disabled=True),
            "Nama":        st.column_config.TextColumn("Nama", disabled=True),
            selected_col:  st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, required=True),
        },
        use_container_width=True,
        hide_index=True,
        key=f"pres_{sel}_{selected_col}",
    )

    # Summary badge
    if not edited_pres.empty:
        counts = edited_pres[selected_col].value_counts()
        s1,s2,s3,s4 = st.columns(4)
        s1.markdown(f'<div style="text-align:center"><span class="badge-hadir">✅ Hadir: {counts.get("Hadir",0)}</span></div>', unsafe_allow_html=True)
        s2.markdown(f'<div style="text-align:center"><span class="badge-alpha">❌ Alpha: {counts.get("Alpha",0)}</span></div>', unsafe_allow_html=True)
        s3.markdown(f'<div style="text-align:center"><span class="badge-izin">⚠️ Izin: {counts.get("Izin",0)}</span></div>', unsafe_allow_html=True)
        s4.markdown(f'<div style="text-align:center"><span class="badge-sakit">🤒 Sakit: {counts.get("Sakit",0)}</span></div>', unsafe_allow_html=True)

    if st.button("💾 Simpan Presensi", type="primary"):
        df[selected_col] = edited_pres[selected_col].values
        sheets[sel] = df
        st.session_state.sheets = sheets
        st.success(f"Presensi untuk '{selected_col}' berhasil disimpan!")

# ─────────────────────────────────────────────────────────────────────────────
# ██  HALAMAN: REKAP & STATISTIK
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📊 Rekap & Statistik":
    st.subheader("📊 Rekap & Statistik Kehadiran")
    sel = st.selectbox("Pilih Mata Kuliah:", sheet_names)
    df  = sheets[sel].copy()
    date_cols = get_date_cols(df)

    if "Nama" not in df.columns or df.empty:
        st.warning("Belum ada data mahasiswa di sheet ini.")
        st.stop()
    if not date_cols:
        st.warning("Belum ada data presensi (kolom pertemuan) di sheet ini.")
        st.stop()

    # Hitung rekap
    df["Total Hadir"]  = df[date_cols].apply(lambda r: (r=="Hadir").sum(), axis=1)
    df["Total Alpha"]  = df[date_cols].apply(lambda r: (r=="Alpha").sum(), axis=1)
    df["Total Izin"]   = df[date_cols].apply(lambda r: (r=="Izin").sum(), axis=1)
    df["Total Sakit"]  = df[date_cols].apply(lambda r: (r=="Sakit").sum(), axis=1)
    df["% Hadir"]      = (df["Total Hadir"] / len(date_cols) * 100).round(1)

    # Warna % Hadir
    def color_pct(val):
        if   val >= 75: return "background-color:#d4edda;color:#155724"
        elif val >= 50: return "background-color:#fff3cd;color:#856404"
        else:           return "background-color:#f8d7da;color:#721c24"

    show_cols = ["No","NIM","Nama","Total Hadir","Total Alpha","Total Izin","Total Sakit","% Hadir"]
    show_cols = [c for c in show_cols if c in df.columns]
    styled = df[show_cols].style.applymap(color_pct, subset=["% Hadir"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📈 Grafik Kehadiran per Pertemuan","🥧 Distribusi Status","🎯 Mahasiswa Kehadiran Rendah"])

    with tab1:
        pct_per_tgl = []
        for c in date_cols:
            vals = df[c]
            total = len(vals)
            pct_per_tgl.append({
                "Pertemuan": c,
                "% Hadir":   round((vals=="Hadir").sum()/total*100,1) if total else 0,
                "% Alpha":   round((vals=="Alpha").sum()/total*100,1) if total else 0,
                "% Izin":    round((vals=="Izin").sum()/total*100,1)  if total else 0,
                "% Sakit":   round((vals=="Sakit").sum()/total*100,1) if total else 0,
            })
        tgl_df = pd.DataFrame(pct_per_tgl)
        fig = px.line(
            tgl_df, x="Pertemuan",
            y=["% Hadir","% Alpha","% Izin","% Sakit"],
            markers=True,
            title=f"Tren Kehadiran – {sel}",
            color_discrete_map={"% Hadir":"#28a745","% Alpha":"#dc3545","% Izin":"#ffc107","% Sakit":"#17a2b8"},
        )
        fig.update_layout(xaxis_tickangle=-45, legend_title="Status")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        total_status = {
            "Hadir": int(df["Total Hadir"].sum()),
            "Alpha": int(df["Total Alpha"].sum()),
            "Izin":  int(df["Total Izin"].sum()),
            "Sakit": int(df["Total Sakit"].sum()),
        }
        pie_df = pd.DataFrame(list(total_status.items()), columns=["Status","Jumlah"])
        fig2 = px.pie(pie_df, names="Status", values="Jumlah",
                      color="Status",
                      color_discrete_map=STATUS_COLORS,
                      title=f"Distribusi Status Kehadiran – {sel}")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        threshold = st.slider("Tampilkan mahasiswa dengan % hadir ≤", 0, 100, 75)
        low = df[df["% Hadir"] <= threshold][["No","NIM","Nama","% Hadir","Total Alpha"]].sort_values("% Hadir")
        if low.empty:
            st.success(f"Tidak ada mahasiswa dengan kehadiran ≤ {threshold}%.")
        else:
            st.warning(f"{len(low)} mahasiswa dengan kehadiran ≤ {threshold}%:")
            st.dataframe(low, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📥 Unduh Rekap")
    excel_data = df_to_excel_bytes(sheets)
    st.markdown(download_link(excel_data, f"presensi_{sel}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", "📥 Unduh Excel Lengkap"), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ██  HALAMAN: TAMBAH / HAPUS SHEET
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔁 Tambah / Hapus Sheet":
    st.subheader("🔁 Kelola Sheet Mata Kuliah")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### ➕ Tambah Sheet Baru")
        new_name = st.text_input("Nama sheet baru", placeholder="cth: Pendidikan_Luar_Sekolah")
        if st.button("Tambah", type="primary"):
            if new_name.strip():
                if new_name in sheets:
                    st.error("Nama sheet sudah ada!")
                else:
                    sheets[new_name] = pd.DataFrame(columns=["No","NIM","Nama","Program Studi","Angkatan"])
                    st.session_state.sheets = sheets
                    st.success(f"Sheet '{new_name}' berhasil ditambahkan.")
                    st.rerun()
            else:
                st.error("Nama tidak boleh kosong.")

    with col_b:
        st.markdown("#### 🗑️ Hapus Sheet")
        to_del = st.selectbox("Pilih sheet yang akan dihapus:", sheet_names)
        confirm = st.checkbox(f"Saya yakin ingin menghapus sheet '{to_del}'")
        if st.button("Hapus", type="secondary") and confirm:
            del sheets[to_del]
            st.session_state.sheets = sheets
            st.success(f"Sheet '{to_del}' berhasil dihapus.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Salin Sheet ke Mata Kuliah Lain")
    src = st.selectbox("Sumber sheet:", sheet_names, key="copy_src")
    dst_name = st.text_input("Nama sheet tujuan (baru):", placeholder="cth: Salinan_PLS")
    copy_data = st.checkbox("Salin data mahasiswa (tanpa kolom presensi)")
    if st.button("Salin Sheet"):
        if dst_name.strip() and dst_name not in sheets:
            df_src = sheets[src].copy()
            base_cols = [c for c in df_src.columns if c not in get_date_cols(df_src)]
            sheets[dst_name] = df_src[base_cols].copy() if copy_data else pd.DataFrame(columns=base_cols)
            st.session_state.sheets = sheets
            st.success(f"Sheet disalin ke '{dst_name}'.")
            st.rerun()
        else:
            st.error("Nama tujuan kosong atau sudah ada.")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
fc1, fc2 = st.columns([3,1])
with fc1:
    st.caption("📋 Sistem Presensi Online Canggih · FIPP UNNES · Dibuat dengan Streamlit & Plotly")
with fc2:
    if sheets:
        excel_all = df_to_excel_bytes(sheets)
        st.markdown(download_link(excel_all, f"all_presensi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", "📥 Unduh Semua Data"), unsafe_allow_html=True)
