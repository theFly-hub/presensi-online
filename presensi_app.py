import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import random
import string
from datetime import datetime, date, timedelta
import plotly.express as px

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Presensi Online | FIPP UNNES",
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
        background: linear-gradient(135deg,#1e3a5f,#2e86de);
        padding:1.5rem 2rem; border-radius:12px;
        margin-bottom:1.5rem; color:white;
    }
    .main-header h1 { color:white; margin:0; font-size:1.8rem; }
    .main-header p  { color:#cce0ff; margin:.2rem 0 0; font-size:.9rem; }
    .kode-box {
        background:#1e3a5f; color:#FFD700;
        font-size:3.5rem; font-weight:900; letter-spacing:.4rem;
        text-align:center; padding:1.2rem 2rem;
        border-radius:16px; margin:1rem 0;
        font-family:monospace;
    }
    .timer-box {
        background:#f8f9fa; border:2px solid #2e86de;
        border-radius:10px; padding:.8rem 1.5rem;
        text-align:center; font-size:1.2rem; font-weight:700; color:#1e3a5f;
    }
    .badge-hadir { background:#d4edda;color:#155724;padding:3px 10px;border-radius:20px;font-size:.8rem; }
    .badge-alpha { background:#f8d7da;color:#721c24;padding:3px 10px;border-radius:20px;font-size:.8rem; }
    .badge-izin  { background:#fff3cd;color:#856404;padding:3px 10px;border-radius:20px;font-size:.8rem; }
    .badge-sakit { background:#d1ecf1;color:#0c5460;padding:3px 10px;border-radius:20px;font-size:.8rem; }
    .card-mhs {
        background:white; border-radius:12px; padding:2rem;
        box-shadow:0 4px 20px rgba(0,0,0,.12); max-width:480px; margin:auto;
    }
    .sukses-box {
        background:#d4edda; border:2px solid #28a745;
        border-radius:12px; padding:1.5rem; text-align:center;
        font-size:1.1rem; color:#155724; margin:1rem 0;
    }
    .gagal-box {
        background:#f8d7da; border:2px solid #dc3545;
        border-radius:12px; padding:1.5rem; text-align:center;
        font-size:1.1rem; color:#721c24; margin:1rem 0;
    }
    div[data-testid="stSidebarContent"] { background:#f0f4f8; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def gen_kode(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

def df_to_excel_bytes(sheets_dict):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for nm, df in sheets_dict.items():
            df.to_excel(w, sheet_name=nm[:31], index=False)
    return buf.getvalue()

def download_btn(data, filename, label="📥 Unduh Excel"):
    b64 = base64.b64encode(data).decode()
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return (f'<a href="data:{mime};base64,{b64}" download="{filename}" '
            f'style="text-decoration:none;background:#2e86de;color:white;'
            f'padding:9px 20px;border-radius:8px;font-weight:600;">{label}</a>')

def get_presensi_cols(df):
    base = {"No","NIM","Nama","Program Studi","Angkatan"}
    return [c for c in df.columns if c not in base]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "matakuliah": {},       # {nama_mk: DataFrame}
    "sesi_aktif": None,     # {mk, kolom, kode, expire, log:[{nim,nama,waktu}]}
    "notif": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>📋 Sistem Presensi Online</h1>
  <p>Kode Sesi + NIM · Kelola Mata Kuliah · Rekap & Unduh · FIPP UNNES</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGASI
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/id/7/73/Unnes_logo.png", width=80)
    st.markdown("### Navigasi")
    mode = st.radio("Pilih tampilan:", ["👨‍🏫 Dosen", "🎓 Mahasiswa"], horizontal=True)

    if mode == "👨‍🏫 Dosen":
        menu = st.radio("Menu Dosen:", [
            "🏠 Dashboard",
            "📚 Kelola Mata Kuliah",
            "👥 Daftar Mahasiswa",
            "🔑 Buka Sesi Presensi",
            "📊 Rekap & Statistik",
        ])
    else:
        menu = "MAHASISWA"

    st.markdown("---")
    if st.session_state.sesi_aktif:
        sa = st.session_state.sesi_aktif
        sisa = (sa["expire"] - datetime.now()).seconds // 60
        exp_str = sa["expire"].strftime("%H:%M:%S")
        st.markdown(f"🟢 **Sesi Aktif**")
        st.markdown(f"MK: `{sa['mk']}`")
        st.markdown(f'<div class="kode-box" style="font-size:2rem;letter-spacing:.3rem;">{sa["kode"]}</div>', unsafe_allow_html=True)
        st.caption(f"Berlaku s/d {exp_str}")
    else:
        st.markdown("🔴 Tidak ada sesi aktif")

# shortcut
mk_dict = st.session_state.matakuliah
mk_list  = list(mk_dict.keys())

# ─────────────────────────────────────────────────────────────────────────────
# ██ HALAMAN MAHASISWA (self-check-in)
# ─────────────────────────────────────────────────────────────────────────────
if menu == "MAHASISWA":
    st.markdown("""
    <div style="max-width:480px;margin:auto;">
    """, unsafe_allow_html=True)
    st.markdown("## 🎓 Presensi Mandiri Mahasiswa")

    with st.container():
        st.markdown('<div class="card-mhs">', unsafe_allow_html=True)

        nim_input  = st.text_input("🪪 Masukkan NIM Anda", placeholder="contoh: 2301001", key="nim_mhs")
        kode_input = st.text_input("🔑 Masukkan Kode Sesi", placeholder="contoh: ABK291", key="kode_mhs",
                                   max_chars=6).strip().upper()

        if st.button("✅ Konfirmasi Hadir", type="primary", use_container_width=True):
            sa = st.session_state.sesi_aktif
            now = datetime.now()

            if sa is None:
                st.markdown('<div class="gagal-box">❌ Tidak ada sesi presensi yang sedang buka.</div>', unsafe_allow_html=True)
            elif now > sa["expire"]:
                st.markdown('<div class="gagal-box">⏰ Sesi sudah berakhir. Hubungi dosen.</div>', unsafe_allow_html=True)
            elif kode_input != sa["kode"]:
                st.markdown('<div class="gagal-box">🔑 Kode sesi salah. Periksa kembali.</div>', unsafe_allow_html=True)
            elif not nim_input.strip():
                st.warning("NIM tidak boleh kosong.")
            else:
                nim = nim_input.strip()
                mk  = sa["mk"]
                col = sa["kolom"]
                df  = mk_dict[mk]

                # Cari mahasiswa
                idx = df.index[df["NIM"].astype(str) == nim].tolist()
                if not idx:
                    st.markdown(f'<div class="gagal-box">❌ NIM <b>{nim}</b> tidak ditemukan di daftar {mk}.</div>', unsafe_allow_html=True)
                else:
                    idx = idx[0]
                    # Cek sudah absen belum
                    if df.at[idx, col] == "Hadir":
                        nama = df.at[idx,"Nama"]
                        st.markdown(f'<div class="sukses-box">ℹ️ <b>{nama}</b>, Anda sudah tercatat Hadir sebelumnya.</div>', unsafe_allow_html=True)
                    else:
                        df.at[idx, col] = "Hadir"
                        mk_dict[mk] = df
                        st.session_state.matakuliah = mk_dict
                        nama = df.at[idx,"Nama"]
                        # Simpan log
                        sa["log"].append({"NIM": nim, "Nama": nama, "Waktu": now.strftime("%H:%M:%S")})
                        st.session_state.sesi_aktif = sa
                        st.markdown(f'<div class="sukses-box">✅ <b>{nama}</b> ({nim})<br>Berhasil tercatat <b>HADIR</b><br>📚 {mk} · {col}<br>🕐 {now.strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
                        st.balloons()

        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ██ DASHBOARD DOSEN
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🏠 Dashboard":
    st.subheader("🏠 Dashboard")
    c1,c2,c3 = st.columns(3)
    c1.metric("Mata Kuliah", len(mk_dict))
    c2.metric("Total Mahasiswa", sum(len(d) for d in mk_dict.values()))
    c3.metric("Total Pertemuan", sum(len(get_presensi_cols(d)) for d in mk_dict.values()))

    if mk_dict:
        rows = []
        for nm, df in mk_dict.items():
            pc = get_presensi_cols(df)
            n  = len(df)
            if n > 0 and pc:
                avg = round(df[pc].apply(lambda c: (c=="Hadir").sum()).sum() / (n*len(pc)) * 100, 1)
            else:
                avg = 0
            rows.append({"Mata Kuliah": nm, "Mahasiswa": n, "Pertemuan": len(pc), "Avg Hadir (%)": avg})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada mata kuliah. Tambahkan di menu Kelola Mata Kuliah.")

# ─────────────────────────────────────────────────────────────────────────────
# ██ KELOLA MATA KULIAH
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📚 Kelola Mata Kuliah":
    st.subheader("📚 Kelola Mata Kuliah")
    tab1, tab2, tab3 = st.tabs(["➕ Tambah MK", "🗑️ Hapus MK", "📋 Salin Daftar"])

    with tab1:
        new_mk = st.text_input("Nama Mata Kuliah", placeholder="cth: Pendidikan_Luar_Sekolah_A")
        if st.button("Tambah MK", type="primary"):
            if new_mk.strip() and new_mk not in mk_dict:
                mk_dict[new_mk] = pd.DataFrame(columns=["No","NIM","Nama","Program Studi","Angkatan"])
                st.session_state.matakuliah = mk_dict
                st.success(f"MK '{new_mk}' ditambahkan.")
                st.rerun()
            else:
                st.error("Nama kosong atau sudah ada.")

    with tab2:
        if mk_list:
            del_mk = st.selectbox("Pilih MK yang dihapus:", mk_list)
            if st.checkbox(f"Konfirmasi hapus '{del_mk}'"):
                if st.button("Hapus", type="secondary"):
                    del mk_dict[del_mk]
                    st.session_state.matakuliah = mk_dict
                    st.success(f"MK '{del_mk}' dihapus.")
                    st.rerun()

    with tab3:
        if len(mk_list) >= 1:
            src_mk  = st.selectbox("Salin dari MK:", mk_list)
            dst_name = st.text_input("Nama MK tujuan (baru):")
            if st.button("Salin Daftar Mahasiswa"):
                if dst_name.strip() and dst_name not in mk_dict:
                    src_df = mk_dict[src_mk]
                    base   = [c for c in src_df.columns if c not in get_presensi_cols(src_df)]
                    mk_dict[dst_name] = src_df[base].copy()
                    st.session_state.matakuliah = mk_dict
                    st.success(f"Daftar mahasiswa dari '{src_mk}' disalin ke '{dst_name}'.")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ██ DAFTAR MAHASISWA
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "👥 Daftar Mahasiswa":
    st.subheader("👥 Daftar Mahasiswa")
    if not mk_list:
        st.info("Belum ada MK. Tambahkan dulu di menu Kelola Mata Kuliah.")
        st.stop()

    sel_mk = st.selectbox("Pilih Mata Kuliah:", mk_list)
    df = mk_dict[sel_mk].copy()
    for col in ["No","NIM","Nama","Program Studi","Angkatan"]:
        if col not in df.columns: df[col] = ""

    st.caption("✏️ Isi/edit tabel di bawah langsung — klik sel untuk mengedit, + di bawah untuk tambah baris")

    pc = get_presensi_cols(df)
    base_cols = ["No","NIM","Nama","Program Studi","Angkatan"]
    edited = st.data_editor(
        df[base_cols + pc] if pc else df[base_cols],
        num_rows="dynamic",
        use_container_width=True,
        key=f"tbl_{sel_mk}",
        column_config={
            "No":            st.column_config.NumberColumn("No.", min_value=1, step=1),
            "NIM":           st.column_config.TextColumn("NIM"),
            "Nama":          st.column_config.TextColumn("Nama Lengkap"),
            "Program Studi": st.column_config.TextColumn("Prodi"),
            "Angkatan":      st.column_config.NumberColumn("Angkatan", min_value=2000, max_value=2099, step=1),
        }
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Simpan Perubahan", type="primary"):
            mk_dict[sel_mk] = edited
            st.session_state.matakuliah = mk_dict
            st.success("Daftar mahasiswa disimpan.")

    with col_b:
        st.markdown("**Upload Excel:**")
        up = st.file_uploader("Upload .xlsx", type=["xlsx"], key=f"up_{sel_mk}", label_visibility="collapsed")
        if up:
            try:
                uploaded_df = pd.read_excel(up)
                mk_dict[sel_mk] = uploaded_df
                st.session_state.matakuliah = mk_dict
                st.success(f"{len(uploaded_df)} mahasiswa berhasil diimport.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Unduh template
    templ = pd.DataFrame({
        "No":[1,2],"NIM":["2301001","2301002"],
        "Nama":["Nama Mahasiswa 1","Nama Mahasiswa 2"],
        "Program Studi":["PLS","PLS"],"Angkatan":[2023,2023]
    })
    templ_bytes = BytesIO()
    templ.to_excel(templ_bytes, index=False)
    st.markdown(download_btn(templ_bytes.getvalue(), "template_daftar.xlsx", "📄 Unduh Template Excel"),
                unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ██ BUKA SESI PRESENSI
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔑 Buka Sesi Presensi":
    st.subheader("🔑 Buka & Kelola Sesi Presensi")
    if not mk_list:
        st.warning("Belum ada MK. Tambahkan dulu.")
        st.stop()

    sa = st.session_state.sesi_aktif

    # ── Tampilan sesi aktif ──
    if sa and datetime.now() <= sa["expire"]:
        st.success(f"✅ Sesi aktif untuk **{sa['mk']}** — Kolom: `{sa['kolom']}`")
        sisa_det = int((sa["expire"] - datetime.now()).total_seconds())
        mnt, det = divmod(sisa_det, 60)
        st.markdown(f'<div class="timer-box">⏱️ Sisa waktu: {mnt:02d} menit {det:02d} detik</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kode-box">{sa["kode"]}</div>', unsafe_allow_html=True)
        st.caption("Tampilkan kode ini kepada mahasiswa di kelas (proyektor / WA grup).")

        # Log check-in realtime
        if sa["log"]:
            st.markdown(f"### ✅ Log Check-in ({len(sa['log'])} mahasiswa)")
            st.dataframe(pd.DataFrame(sa["log"]), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada mahasiswa yang melakukan check-in.")

        if st.button("⛔ Tutup Sesi Sekarang", type="secondary"):
            st.session_state.sesi_aktif = None
            st.success("Sesi ditutup.")
            st.rerun()

    else:
        if sa:  # expired
            st.warning("Sesi sebelumnya telah berakhir.")
            st.session_state.sesi_aktif = None

        st.markdown("### Buka Sesi Baru")
        sel_mk   = st.selectbox("Mata Kuliah:", mk_list)
        df_mk    = mk_dict[sel_mk]
        pc       = get_presensi_cols(df_mk)
        tgl      = st.date_input("Tanggal pertemuan:", value=date.today())
        ptm_ke   = st.number_input("Pertemuan ke-", min_value=1, max_value=99, value=len(pc)+1)
        col_name = f"P{ptm_ke}_{tgl.strftime('%Y-%m-%d')}"
        durasi   = st.slider("Durasi sesi (menit):", min_value=5, max_value=60, value=15, step=5)
        kode_manual = st.checkbox("Atur kode manual")
        if kode_manual:
            kode = st.text_input("Kode (6 karakter):", max_chars=6).upper()
        else:
            kode = gen_kode()
            st.info(f"Kode yang akan digunakan: **{kode}**")

        if st.button("🔓 Buka Sesi Presensi", type="primary"):
            if not kode.strip():
                st.error("Kode tidak boleh kosong.")
            else:
                # Tambah kolom ke dataframe jika belum ada, isi default "Alpha"
                if col_name not in df_mk.columns:
                    df_mk[col_name] = "Alpha"
                    mk_dict[sel_mk] = df_mk
                    st.session_state.matakuliah = mk_dict

                expire_time = datetime.now() + timedelta(minutes=durasi)
                st.session_state.sesi_aktif = {
                    "mk":     sel_mk,
                    "kolom":  col_name,
                    "kode":   kode,
                    "expire": expire_time,
                    "log":    [],
                }
                st.success(f"Sesi dibuka! Kode: **{kode}** · Berlaku hingga {expire_time.strftime('%H:%M:%S')}")
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ██ REKAP & STATISTIK
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📊 Rekap & Statistik":
    st.subheader("📊 Rekap & Statistik Kehadiran")
    if not mk_list:
        st.info("Belum ada data.")
        st.stop()

    sel_mk = st.selectbox("Pilih Mata Kuliah:", mk_list)
    df = mk_dict[sel_mk].copy()
    pc = get_presensi_cols(df)

    if df.empty or not pc:
        st.warning("Belum ada data presensi untuk MK ini.")
        st.stop()

    # Hitung rekap
    df["Hadir"]  = df[pc].apply(lambda r: (r=="Hadir").sum(), axis=1)
    df["Alpha"]  = df[pc].apply(lambda r: (r=="Alpha").sum(), axis=1)
    df["Izin"]   = df[pc].apply(lambda r: (r=="Izin").sum(), axis=1)
    df["Sakit"]  = df[pc].apply(lambda r: (r=="Sakit").sum(), axis=1)
    df["% Hadir"]= (df["Hadir"]/len(pc)*100).round(1)

    def warna(v):
        if   v>=75: return "background:#d4edda;color:#155724"
        elif v>=50: return "background:#fff3cd;color:#856404"
        else:       return "background:#f8d7da;color:#721c24"

    show = ["No","NIM","Nama","Hadir","Alpha","Izin","Sakit","% Hadir"]
    show = [c for c in show if c in df.columns]
    st.dataframe(df[show].style.applymap(warna, subset=["% Hadir"]),
                 use_container_width=True, hide_index=True)

    # Manual override status
    with st.expander("✏️ Ubah Status Manual (koreksi dosen)"):
        idx_mhs = st.selectbox("Pilih mahasiswa:", df["Nama"].tolist() if "Nama" in df.columns else [])
        col_prs = st.selectbox("Pilih pertemuan:", pc)
        new_stat = st.selectbox("Status baru:", ["Hadir","Alpha","Izin","Sakit"])
        if st.button("Update Status"):
            row_i = df.index[df["Nama"]==idx_mhs].tolist()
            if row_i:
                mk_dict[sel_mk].at[row_i[0], col_prs] = new_stat
                st.session_state.matakuliah = mk_dict
                st.success(f"Status {idx_mhs} pada {col_prs} diubah ke {new_stat}.")
                st.rerun()

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📈 Tren per Pertemuan","🥧 Distribusi Status","⚠️ Kehadiran Rendah"])

    with tab1:
        rows_tren = []
        for c in pc:
            total = len(df)
            rows_tren.append({
                "Pertemuan": c,
                "% Hadir":  round((df[c]=="Hadir").sum()/total*100,1),
                "% Alpha":  round((df[c]=="Alpha").sum()/total*100,1),
                "% Izin":   round((df[c]=="Izin").sum()/total*100,1),
                "% Sakit":  round((df[c]=="Sakit").sum()/total*100,1),
            })
        tren_df = pd.DataFrame(rows_tren)
        fig = px.line(tren_df, x="Pertemuan", y=["% Hadir","% Alpha","% Izin","% Sakit"],
                      markers=True, title=f"Tren Kehadiran – {sel_mk}",
                      color_discrete_map={"% Hadir":"#28a745","% Alpha":"#dc3545","% Izin":"#ffc107","% Sakit":"#17a2b8"})
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        pie_data = {"Hadir":int(df["Hadir"].sum()),"Alpha":int(df["Alpha"].sum()),
                    "Izin":int(df["Izin"].sum()),"Sakit":int(df["Sakit"].sum())}
        fig2 = px.pie(pd.DataFrame(list(pie_data.items()),columns=["Status","Jumlah"]),
                      names="Status",values="Jumlah",
                      color="Status",
                      color_discrete_map={"Hadir":"#28a745","Alpha":"#dc3545","Izin":"#ffc107","Sakit":"#17a2b8"},
                      title=f"Distribusi Status – {sel_mk}")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        batas = st.slider("Tampilkan % hadir ≤", 0, 100, 75)
        low = df[df["% Hadir"]<=batas][["No","NIM","Nama","% Hadir","Alpha"]].sort_values("% Hadir")
        if low.empty:
            st.success(f"Tidak ada mahasiswa dengan kehadiran ≤ {batas}%.")
        else:
            st.warning(f"{len(low)} mahasiswa perlu perhatian:")
            st.dataframe(low, use_container_width=True, hide_index=True)

    st.markdown("---")
    excel_dl = df_to_excel_bytes(mk_dict)
    st.markdown(download_btn(excel_dl, f"presensi_{sel_mk}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                             "📥 Unduh Excel Lengkap"), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
fc1, fc2 = st.columns([3,1])
fc1.caption("📋 Sistem Presensi Online – Kode Sesi + NIM · FIPP UNNES · Streamlit")
with fc2:
    if mk_dict:
        all_excel = df_to_excel_bytes(mk_dict)
        st.markdown(download_btn(all_excel, f"semua_presensi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                 "📥 Unduh Semua Data"), unsafe_allow_html=True)
