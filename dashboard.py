import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import glob
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Spotify Charts Dashboard",
    page_icon="🎵",
    layout="wide"
)

# Título y descripción
st.title("🎵 Spotify Charts Dashboard")
st.markdown("""
Este dashboard muestra el análisis de las canciones más populares en Latinoamérica y España según Spotify Charts.

**Nota**: Los datos se actualizan manualmente. Última actualización: {}.
""".format(datetime.now().strftime('%d/%m/%Y')))

# Verificar existencia de carpeta de datos
if not os.path.exists("spotify_downloads"):
    st.error("""
    ⚠️ No se encontraron datos. 
    
    Este dashboard requiere datos descargados de Spotify Charts. Si eres el administrador:
    1. Ejecuta el bot para descargar los datos
    2. Sube la carpeta spotify_downloads al repositorio
    """)
    st.stop()

# Cargar todos los archivos CSV
@st.cache_data
def load_data():
    countries = {
        'ar': 'Argentina',
        'cl': 'Chile',
        'uy': 'Uruguay',
        'mx': 'México',
        'es': 'España'
    }
    
    all_dfs = {}
    all_artists_expanded = {}
    all_labels_expanded = {}
    
    for country_code in countries:
        all_files = glob.glob(f"spotify_downloads/{country_code}/*.csv")
        dfs = []
        
        for file in all_files:
            try:
                # Leer el CSV
                df = pd.read_csv(file)
                
                # Renombrar columnas si es necesario
                column_mapping = {
                    'rank': 'Position',
                    'artist_names': 'Artist',
                    'track_name': 'Track Name',
                    'streams': 'Streams',
                    'source': 'Label'
                }
                df = df.rename(columns=column_mapping)
                
                # Extraer la fecha del nombre del archivo y convertirla correctamente
                date_str = os.path.basename(file).split('daily-')[-1].replace('.csv', '')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    df['date'] = date
                    dfs.append(df)
                except ValueError as e:
                    st.warning(f"Error al procesar la fecha del archivo {file}: {str(e)}")
                
            except Exception as e:
                st.warning(f"Error al cargar {file}: {str(e)}")
        
        if not dfs:
            st.error(f"No se encontraron archivos CSV válidos para {countries[country_code]}")
            continue
        
        # Concatenar todos los DataFrames
        final_df = pd.concat(dfs, ignore_index=True)
        
        # Asegurarse de que las columnas numéricas sean del tipo correcto
        final_df['Position'] = pd.to_numeric(final_df['Position'], errors='coerce')
        final_df['Streams'] = pd.to_numeric(final_df['Streams'], errors='coerce')
        
        # Crear DataFrame expandido con artistas individuales
        artists_expanded = final_df.copy()
        artists_expanded['Artist'] = artists_expanded['Artist'].str.split(', ')
        artists_expanded = artists_expanded.explode('Artist')
        
        # Crear DataFrame expandido con labels individuales
        labels_expanded = final_df.copy()
        labels_expanded['Label'] = labels_expanded['Label'].str.split(' / ')
        labels_expanded = labels_expanded.explode('Label')
        # Limpiar espacios en blanco en las labels
        labels_expanded['Label'] = labels_expanded['Label'].str.strip()
        
        all_dfs[country_code] = final_df
        all_artists_expanded[country_code] = artists_expanded
        all_labels_expanded[country_code] = labels_expanded
    
    return all_dfs, all_artists_expanded, all_labels_expanded

# Cargar los datos
all_dfs, all_artists_expanded, all_labels_expanded = load_data()

if all_dfs:
    # Selector de país
    country_options = {
        'ar': 'Argentina',
        'cl': 'Chile',
        'uy': 'Uruguay',
        'mx': 'México',
        'es': 'España'
    }
    selected_country = st.sidebar.selectbox(
        "Seleccionar País",
        options=list(country_options.keys()),
        format_func=lambda x: country_options[x]
    )
    
    # Obtener los DataFrames del país seleccionado
    df = all_dfs[selected_country]
    df_artists = all_artists_expanded[selected_country]
    df_labels = all_labels_expanded[selected_country]
    
    # Sidebar para filtros
    st.sidebar.header("Filtros")
    
    # Filtro de fechas
    min_date = df['date'].min()
    max_date = df['date'].max()
    start_date = st.sidebar.date_input(
        "Fecha de inicio",
        min_date,
        min_value=min_date,
        max_value=max_date
    )
    end_date = st.sidebar.date_input(
        "Fecha de fin",
        max_date,
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtro de posición
    min_position = st.sidebar.slider(
        "Posición mínima",
        min_value=1,
        max_value=200,
        value=1
    )
    max_position = st.sidebar.slider(
        "Posición máxima",
        min_value=1,
        max_value=200,
        value=50
    )
    
    # Aplicar filtros a los DataFrames
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    mask &= (df['Position'] >= min_position) & (df['Position'] <= max_position)
    filtered_df = df[mask]
    
    mask_artists = (df_artists['date'].dt.date >= start_date) & (df_artists['date'].dt.date <= end_date)
    mask_artists &= (df_artists['Position'] >= min_position) & (df_artists['Position'] <= max_position)
    filtered_df_artists = df_artists[mask_artists]
    
    mask_labels = (df_labels['date'].dt.date >= start_date) & (df_labels['date'].dt.date <= end_date)
    mask_labels &= (df_labels['Position'] >= min_position) & (df_labels['Position'] <= max_position)
    filtered_df_labels = df_labels[mask_labels]
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total de canciones únicas", filtered_df['Track Name'].nunique())
    with col2:
        st.metric("Total de artistas únicos", filtered_df_artists['Artist'].nunique())
    with col3:
        st.metric("Total de labels", filtered_df_labels['Label'].nunique())
    with col4:
        st.metric("Total de streams", f"{filtered_df['Streams'].sum():,}")
    with col5:
        st.metric("Período analizado", f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    
    # Análisis de números 1
    st.header("🏆 Análisis de Números 1")
    
    # Filtrar solo posición #1
    number_ones = filtered_df[filtered_df['Position'] == 1]
    number_ones_artists = filtered_df_artists[filtered_df_artists['Position'] == 1]
    number_ones_labels = filtered_df_labels[filtered_df_labels['Position'] == 1]
    
    # Artistas con más días en el #1
    st.subheader("Artistas con Más Días en el #1")
    
    # Calcular días totales por artista
    total_days = number_ones_artists['Artist'].value_counts().reset_index()
    total_days.columns = ['Artista', 'Días']
    
    # Crear gráfico de días totales
    fig_days = px.bar(
        total_days.head(10),
        x='Artista',
        y='Días',
        title="Top 10 Artistas por Días Totales en el #1",
        text='Días'
    )
    
    # Personalizar el diseño
    fig_days.update_traces(textposition='auto')
    fig_days.update_layout(height=500)
    
    st.plotly_chart(fig_days, use_container_width=True)
    
    # Artistas con más canciones diferentes en el #1
    st.subheader("Artistas con Más Canciones en el #1")
    
    # Contar canciones únicas por artista
    songs_by_artist = number_ones_artists.groupby('Artist')['Track Name'].nunique().reset_index()
    songs_by_artist.columns = ['Artista', 'Canciones']
    songs_by_artist = songs_by_artist.sort_values('Canciones', ascending=False)
    
    # Crear gráfico de canciones
    fig_songs = px.bar(
        songs_by_artist.head(10),
        x='Artista',
        y='Canciones',
        title="Top 10 Artistas por Cantidad de Canciones Diferentes en el #1",
        text='Canciones'
    )
    
    # Personalizar el diseño
    fig_songs.update_traces(textposition='auto')
    fig_songs.update_layout(height=500)
    
    st.plotly_chart(fig_songs, use_container_width=True)
    
    # Labels con más números 1
    st.subheader("Discográficas con Más Números 1")
    top_labels = number_ones_labels['Label'].value_counts().head(10)
    fig_labels = px.bar(
        x=top_labels.index,
        y=top_labels.values,
        title="Discográficas con más días en el #1",
        labels={'x': 'Discográfica', 'y': 'Días en #1'}
    )
    st.plotly_chart(fig_labels, use_container_width=True)
    
    # Canciones con más días en número 1
    st.subheader("Canciones con Más Días en #1")
    top_songs_n1 = number_ones.groupby(['Track Name', 'Artist'])['date'].count().sort_values(ascending=False).head(10)
    fig_songs_n1 = px.bar(
        x=top_songs_n1.index.get_level_values('Track Name'),
        y=top_songs_n1.values,
        color=top_songs_n1.index.get_level_values('Artist'),
        title="Canciones con más días en el #1",
        labels={'x': 'Canción', 'y': 'Días en #1'}
    )
    st.plotly_chart(fig_songs_n1, use_container_width=True)
    
    # Top Artistas (considerando colaboraciones)
    st.header("📊 Estadísticas Generales")
    
    # Top Labels Overall
    st.subheader("Top 10 Discográficas")
    top_labels_overall = filtered_df_labels['Label'].value_counts().head(10)
    fig_top_labels = px.bar(
        x=top_labels_overall.index,
        y=top_labels_overall.values,
        title="Discográficas con más apariciones en el Top",
        labels={'x': 'Discográfica', 'y': 'Número de apariciones'}
    )
    st.plotly_chart(fig_top_labels, use_container_width=True)
    
    st.subheader("Top 10 Artistas por Apariciones")
    top_artists_overall = filtered_df_artists['Artist'].value_counts().head(10)
    fig_top_artists = px.bar(
        x=top_artists_overall.index,
        y=top_artists_overall.values,
        title="Artistas con más apariciones en el Top",
        labels={'x': 'Artista', 'y': 'Número de apariciones'}
    )
    st.plotly_chart(fig_top_artists, use_container_width=True)
    
    # Gráfico de evolución de artistas en el top
    st.subheader("Evolución de Artistas en el Top")
    
    # Identificar los 10 artistas más frecuentes en el top 10
    # Usamos el DataFrame expandido que ya tiene los artistas separados
    artist_frequencies = filtered_df_artists[filtered_df_artists['Position'] <= 10]['Artist'].value_counts()
    top_10_artists = artist_frequencies.head(10).index.tolist()
    
    # Crear diccionario de artistas por fecha
    top_artists_by_date = {}
    for date in filtered_df_artists['date'].unique():
        # Obtener los artistas para cada fecha
        day_artists = filtered_df_artists[filtered_df_artists['date'] == date].sort_values('Position')
        # Filtrar solo los top 10 artistas más frecuentes
        day_top_artists = day_artists[day_artists['Artist'].isin(top_10_artists)]
        # Agrupar por artista y tomar la mejor posición para cada uno
        day_top_artists = day_top_artists.groupby('Artist')['Position'].min().reset_index()
        top_artists_by_date[date] = dict(zip(day_top_artists['Artist'], day_top_artists['Position']))
    
    # Obtener datos de artistas
    artist_data = []
    for date in filtered_df_artists['date'].unique():
        for artist in top_10_artists:
            position = top_artists_by_date[date].get(artist, None)
            artist_data.append({
                'Fecha': date,
                'Artista': artist,
                'Posición': position
            })
    
    df_artists = pd.DataFrame(artist_data)
    
    # Crear gráfico de líneas
    fig = px.line(df_artists, 
                  x='Fecha', 
                  y='Posición',
                  color='Artista',
                  title='Evolución de Posiciones de los 10 Artistas Más Frecuentes',
                  labels={'Posición': 'Posición en el Top'},
                  line_shape='spline')  # Usar spline para suavizar las líneas
    
    # Invertir el eje Y para que la posición 1 esté arriba
    fig.update_yaxes(autorange="reversed", range=[10.5, 0.5])
    
    # Personalizar el gráfico
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        xaxis=dict(
            tickformat='%d/%m/%Y',
            tickangle=45
        ),
        yaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de canciones más populares
    st.subheader("Canciones Más Populares")
    top_songs = filtered_df.groupby(['Track Name', 'Artist'])['Streams'].sum().reset_index()
    top_songs = top_songs.sort_values('Streams', ascending=False).head(10)
    
    fig_songs = px.bar(
        top_songs,
        x='Track Name',
        y='Streams',
        color='Artist',
        title='Top 10 Canciones por Total de Streams',
        labels={'Streams': 'Total de Streams', 'Track Name': 'Canción'}
    )
    st.plotly_chart(fig_songs, use_container_width=True)
    
    # Tabla de datos
    st.subheader("Datos Detallados")
    st.dataframe(
        filtered_df[['date', 'Position', 'Track Name', 'Artist', 'Label', 'Streams']].sort_values(['date', 'Position']),
        use_container_width=True
    ) 