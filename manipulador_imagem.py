from PIL import Image, ImageDraw, ImageFont
import piexif
import os
import pyproj

# Verifica se é um arquivo JPEG válido
def arquivo_jpeg_valido(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'rb') as f:
            f.seek(-2, 2)
            return f.read() == b'\xff\xd9'
    except Exception:
        return False

# Gera um novo nome de arquivo que não conflite com os nomes de arquivos existentes no diretório especificado
def gerar_novo_nome(diretorio, nome_arquivo):
    base, ext = os.path.splitext(nome_arquivo)
    contador = 1
    while os.path.exists(os.path.join(diretorio, nome_arquivo)):
        nome_arquivo = f"{base}_{contador}{ext}"
        contador += 1
    return nome_arquivo

# Função para obter coordenadas formatadas
def obter_coordenadas_formatadas(dados_gps):
    latitude = dados_gps.get(piexif.GPSIFD.GPSLatitude)
    longitude = dados_gps.get(piexif.GPSIFD.GPSLongitude)

    if not (latitude and longitude and latitude[0][1] != 0 and latitude[1][1] != 0 and latitude[2][1] != 0):
        return None, None

    graus_lat = latitude[0][0] / latitude[0][1]
    minutos_lat = latitude[1][0] / latitude[1][1]
    segundos_lat = latitude[2][0] / latitude[2][1]
    direcao_lat = "N" if dados_gps.get(piexif.GPSIFD.GPSLatitudeRef) == b'N' else "S"

    graus_lon = longitude[0][0] / longitude[0][1]
    minutos_lon = longitude[1][0] / longitude[1][1]
    segundos_lon = longitude[2][0] / longitude[2][1]
    direcao_lon = "E" if dados_gps.get(piexif.GPSIFD.GPSLongitudeRef) == b'E' else "W"

    lat_decimal = dms_para_decimal(graus_lat, minutos_lat, segundos_lat)
    lon_decimal = dms_para_decimal(graus_lon, minutos_lon, segundos_lon)

    if direcao_lat == "S":
        lat_decimal = -lat_decimal
    if direcao_lon == "W":
        lon_decimal = -lon_decimal

    coordenadas_utm = converter_para_utm_int(lat_decimal, lon_decimal)
    return coordenadas_utm

# converte a coordenada de dms para decimal
def dms_para_decimal(graus, minutos, segundos):
    return graus + (minutos / 60.0) + (segundos / 3600.0)


# Obtem a zona UTM automaticamente
def obter_zona_utm(longitude):
    """Determina a zona UTM para uma dada longitude."""
    return int((longitude + 180) / 6) + 1

# Converte as coordenadas decimais para UTM - utilizando o pyproj
def converter_para_utm(lat, lon):
    zona = obter_zona_utm(lon)
    transformador = pyproj.Transformer.from_crs(
        {"proj": 'latlong', "datum": 'WGS84'},
        {"proj": 'utm', "zone": zona, "ellps": 'WGS84', "south": True if lat < 0 else False},
        always_xy=True
    )
    leste, norte = transformador.transform(lon, lat)
    return leste, norte

# converte as coordenadas UTM para numeros inteiros
def converter_para_utm_int(lat, lon):
    leste, norte = converter_para_utm(lat, lon)
    return int(leste), int(norte)

# Extrai metadados de uma imagem
def extrair_metadados(caminho_imagem):
    dados_gps = {}
    tempo_exif = ""

    with Image.open(caminho_imagem) as imagem:
        # Verifique se a imagem possui metadados EXIF antes de tentar acessá-los
        if "exif" in imagem.info:
            dados_exif = piexif.load(imagem.info["exif"])
            dados_gps = dados_exif.get('GPS', {})
            tempo_exif = dados_exif.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal, b"").decode("utf-8")

    return dados_gps, tempo_exif


# Obtem a fonte Arial do sistema
def carregar_fonte(tamanho):
    try:
        return ImageFont.truetype("static/fonts/arial.ttf", tamanho)
    except Exception:
        return ImageFont.load_default()

# Imprimi os metadados na imagem nova
def desenhar_metadados_na_imagem(caminho_imagem, metadados, tamanho_fonte, cor_texto, posicao):
    try:
        dados_gps, tempo_exif = metadados
        latitude_formatada, longitude_formatada = obter_coordenadas_formatadas(dados_gps)
        data_hora_formatada = tempo_exif if tempo_exif else "sem metadados"

        imagem = Image.open(caminho_imagem)
        posicao_texto = (10, 10)  # padrão: Topo Esquerdo
        desenho = ImageDraw.Draw(imagem)
        fonte = carregar_fonte(tamanho_fonte)
        texto_metadados = f"Latitude: {latitude_formatada}\n" \
                          f"Longitude: {longitude_formatada}\n" \
                          f"Data e Hora: {data_hora_formatada}"

        desenho.multiline_text(posicao_texto, texto_metadados, fill=cor_texto, font=fonte)
        return imagem
    except Exception as e:
        print(f"Erro ao desenhar metadados em {caminho_imagem}: {e}")
        return None
