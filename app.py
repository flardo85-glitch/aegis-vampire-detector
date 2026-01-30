# --- DASHBOARD DI LIVELLO ---
st.divider()
st.subheader("🛡️ Executive Summary: Audit Quantitativo")

# Layout a 3 colonne per le metriche chiave
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="DISPERSIONE PATRIMONIALE STIMATA", 
        value=format_euro_ui(loss), 
        delta="- Perdita di Potere d'Acquisto", 
        delta_color="inverse"
    )

with col2:
    # Colore dinamico per lo score
    status_color = "normal" if score < 4 else "off"
    st.metric(
        label="INDICE DI INEFFICIENZA (AI)", 
        value=f"{score} / 10", 
        delta="Livello Critico" if score > 6 else "Livello Ottimizzabile"
    )

with col3:
    efficienza_percent = round((f_b / f_a) * 100, 1)
    st.metric(
        label="EFFICIENZA DEL CAPITALE", 
        value=f"{efficienza_percent}%", 
        delta="Rispetto al Benchmark Ottimale"
    )

st.divider()

# Layout Grafico + Analisi Testuale
c1, c2 = st.columns([2, 1])

with c1:
    st.write("**Proiezione della Dispersione nel Tempo**")
    # Creazione di un dataframe per il grafico temporale
    years_range = np.arange(0, yrs + 1)
    data_plot = pd.DataFrame({
        'Anni': years_range,
        'Capitale Efficiente': [cap * ((1.05 - 0.002)**y) for y in years_range],
        'Capitale Attuale': [cap * ((1.05 - (ter/100))**y) for y in years_range]
    })
    fig = px.area(data_plot, x='Anni', y=['Capitale Efficiente', 'Capitale Attuale'], 
                  color_discrete_sequence=['#2ecc71', '#e74c3c'],
                  labels={'value': 'Valore Capitale (€)', 'variable': 'Scenario'},
                  template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.write("**Checklist di Revisione**")
    if score > 6:
        st.warning("⚠️ **INTERVENTO RICHIESTO**")
        st.write("- Analisi immediata costi di uscita")
        st.write("- Switch su strumenti a replica passiva")
        st.write("- Ottimizzazione fiscale immediata")
    else:
        st.info("✅ **MONITORAGGIO**")
        st.write("- Ribilanciamento periodico")
        st.write("- Verifica correlazione asset < 0.50")
        st.write("- Consolidamento zainetto fiscale")

st.caption("L'analisi si basa su una crescita ipotetica del 5% lordo annuo. La dispersione reale potrebbe variare in base ai mercati.")
