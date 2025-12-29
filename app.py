import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sponsor Dedektörü", layout="wide")

st.title("Influencer x Branding")

try:
    df = pd.read_excel('sponsored_videos_scored.xlsx')
    
    validation_col = None
    for col in df.columns:
        if str(col) == 'True':
            validation_col = col
            break
            
    if validation_col:
        df = df[df[validation_col] == '+']
        df = df.drop(columns=[validation_col])

    if 'published_at' in df.columns:
        df['published_at'] = pd.to_datetime(df['published_at'])
        df = df.sort_values(by='published_at', ascending=False)
    
    total_sponsored = len(df)
    unique_sponsors = df['detected_sponsor'].nunique()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tespit Edilen Sponsorlu Video", total_sponsored)
    with col2:
        st.metric("Farklı Marka Sayısı", unique_sponsors)
        
    st.divider()
    
    st.subheader("Tespit Edilen Liste")

    display_df = df.rename(columns={
        'video_title': 'Video Başlığı',
        'channel_name': 'Kanal Adı',
        'published_at': 'Tarih',
        'detected_sponsor': 'Sponsor (Marka)'
    })
    
    st.dataframe(
        display_df, 
        width="stretch",
        column_config={
            "Video Başlığı": st.column_config.TextColumn("Video", width="medium"),
            "Kanal Adı": st.column_config.TextColumn("Kanal", width="small"),
            "Sponsor (Marka)": st.column_config.TextColumn("Sponsor", width="small"),
            "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY")
        }
    )
    
except FileNotFoundError:
    st.error("Sonuç dosyası bulunamadı. Lütfen önce sponsor tespit kodunu çalıştırın.")

st.markdown("---")
st.caption("Barış Serhat Kaplan")
