import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import math

## Carga de datos de viajes

df = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_viajes2021.csv")
df

df = df.drop(columns = ["user_id", "id", "age", "gender", "nationality", "user_type", "country_id", 
        "origin_month_name", "user_type_id", "bike_id", "close_type"])

# agarro datos SOLO del ultimo trimestre, como fue recomendado
df["origin_month"]
df = df.loc[(df["origin_month"] == 12) | (df["origin_month"] == 11) | (df["origin_month"] == 10)]

df = df.loc[(df["destination_station_id"] != "55") & (df["origin_station_id"] != "55")] #No existe
df = df.loc[(df["destination_station_id"] != "86") & (df["origin_station_id"] != "86")] #Tampoco existe en la base de estaciones
df = df.loc[(df["destination_station_id"] != "56") & (df["origin_station_id"] != "56")]

df = df.loc[df["destination_station_id"] != 86]

# Nuevas columnas con la hora redondeada para despues hacer tabla
df["hora_salida_redondeada"] = pd.to_datetime(df["origin_time"], format = "%H:%M:%S")
df["hora_salida_redondeada"] = df["hora_salida_redondeada"].dt.tz_localize('utc').dt.tz_convert('America/Sao_Paulo')
df["hora_salida_redondeada"] = df["hora_salida_redondeada"].dt.round("30min")
df["hora_salida_redondeada"] = df["hora_salida_redondeada"].dt.strftime('%H:%M')

df["hora_llegada_redondeada"] = pd.to_datetime(df["destination_time"], format = "%H:%M:%S")
df["hora_llegada_redondeada"] = df["hora_llegada_redondeada"].dt.tz_localize('utc').dt.tz_convert('America/Sao_Paulo')
df["hora_llegada_redondeada"] = df["hora_llegada_redondeada"].dt.round("30min")
df["hora_llegada_redondeada"] = df["hora_llegada_redondeada"].dt.strftime('%H:%M')


## Carga de datos de vehiculos

df2  = pd.read_excel(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_vehiculos2021.xlsx")
df2

df2 = df2[df2["Desestimar"] != "sí"] # Elimino datos desestimados
df2 = df2[df2["Descripción de zona"] != "BASE OPERATIVA"] # Elimino cuando entran a la base
df2["Fecha hora salida de zona normalizada"] = pd.to_datetime(df2["Fecha hora salida de zona"], format='%d-%m-%Y %H:%M:%S').dt.normalize() 
df2 = df2[~(df2["Fecha hora salida de zona normalizada"] <=  "2021-10-1")] # Elimino todos los datos anteriores a octubre 2021

pd.crosstab(df2["Identificador vehículo"], df2["Descripción de zona"])

sns.heatmap(pd.crosstab(df2["Identificador vehículo"], df2["Descripción de zona"]),
 annot=True, cbar=False, robust=True)
plt.show() # Hay zonas donde pasan mas veces, otras donde solo hubo 1 viaje, estuvieron ellas alguna vez fuera de
# servicio?

## Carga de datos fuera de servicio

df3 = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_fueraserv2021.csv")
df3

df3["Duración"].describe() # noto un outlier, 132556 minutos ?
df3 = df3[df3["Número"] != 503] # quito estaciones de prueba nro 503

df3.sort_values("Duración") # sigue habiendo nros altos entonces ordeno
df3 = df3[df3["Número"] != 502] # quito estaciones moviles 
df3 = df3[df3["Número"] != 501]
df3 = df3[df3["Número"] != 55]
df3 = df3[df3["Número"] != 56]
df3 = df3[df3["Número"] != 86]


# incluso despues de sacar estas estaciones, sigue habiendo problemas con tiempo de incidencia MUY largos
# por lo tanto voy a asumir que si pasa de los 5 días (7200 minutos) el problema no es por errores en la 
# distribucion, si no otra falla ajena al problema 

# df3 = df3[df3["Duración"] < 7200] # me di cuenta que esta es la base de datos de las estaciones fuera de servicio :P

df3 = df3["Desde Normalizado"] = pd.to_datetime(df3["Desde"], format='%d-%m-%Y %H:%M:%S').dt.normalize()
df3 = df3[~(df3["Desde Normalizado"] <=  "2021-10-1")] # Elimino todos los datos anteriores a octubre 2021

## Carga de datos de estado de parada

df4 = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estadocarga2021.csv")

df4 = df4[df4["id_station"] != 55] # ya que la 55 NO SE ENCUENTRA en la base de estaciones
df4 = df4[df4["id_station"] != 56] # eso eso
df4 = df4[df4["id_station"] != 86] # ya que la 86 blablabla

df4 = df4.drop(["id", "station_num", "is_deleted", "incidence_time", "id_status_for_station"], axis = 1)

df4["inicio"] = pd.to_datetime(df4["created_at"], format='%Y-%m-%d %H:%M:%S').dt.normalize()
df4 = df4[~(df4["inicio"] <=  "2021-10-1")] # Elimino todos los datos anteriores a octubre 2021

df4["fin"] = pd.to_datetime(df4["incidence_end_date"], format='%Y-%m-%d %H:%M:%S').dt.normalize()

# Agrego variable que me diga el dia (queda en ingles por mi compu creo u.u)
df4["dia"] = df4['inicio'].dt.day_name()

df4["hora_inicio"] = pd.to_datetime(df4["created_at"], format = "%Y-%m-%d %H:%M:%S")
df4["hora_inicio"] = df4["hora_inicio"].dt.tz_localize('utc').dt.tz_convert('America/Sao_Paulo')
df4["hora_inicio"] = df4["hora_inicio"].dt.round("30min")
df4["hora_inicio"] = df4["hora_inicio"].dt.strftime('%H:%M')

df4["hora_fin"] = pd.to_datetime(df4["incidence_end_date"], format = "%Y-%m-%d %H:%M:%S")
df4["hora_fin"] = df4["hora_fin"].dt.tz_localize('utc').dt.tz_convert('America/Sao_Paulo')
df4["hora_fin"] = df4["hora_fin"].dt.round("30min")
df4["hora_fin"] = df4["hora_fin"].dt.strftime('%H:%M')

# Al final era inconsistente. Deje la columna "status", confiando que esta bien calculada
# df4["porcentaje_ocupado"] = df4["occupied_anchors"] df4['blocked_anchors'] / df4["reported_anchors"]

# temp = [
#     (df4["porcentaje_ocupado"] < 0.33),
#     (df4["porcentaje_ocupado"] > 0.33) & (df4["porcentaje_ocupado"] < 0.66),
#     (df4["porcentaje_ocupado"] > 0.66)
# ]

# temp2 = ["Riesgo Vacío", "Sin Riesgo", "Riesgo Lleno"]
# df4["riesgo"] = np.select(temp, temp2)

df4 = df4.drop(columns = ['incidence_end_date', 'created_at', 'updated_at'])
## GUARDADO DE DATOS

df.to_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_viajes_limpio.csv")
df2.to_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_vehiculos_limpio.xlsx")
df3.to_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_fueraserv_limpio.csv")
df4.to_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estadocarga_con_normales.csv")

