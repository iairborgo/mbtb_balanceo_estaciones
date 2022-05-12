import numpy as np
import pandas as pd
import math

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import branca.colormap
import colorcet as cc

import folium
import base64
from folium.plugins import HeatMap
from folium import IFrame
import webbrowser
from collections import defaultdict, OrderedDict

# ESTO HACE LOS GRAFICOS LINDOS Y ORDENADOS 
mpl.rcParams["figure.facecolor"] = "w"
plt.rcParams['savefig.facecolor']='w'
plt.rcParams["savefig.dpi"] = 200
mpl.rcParams["savefig.directory"] = r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\plots"
plt.style.use('fivethirtyeight')
paleta = sns.cubehelix_palette(n_colors = 73, reverse = True)

df_estaciones =  pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estaciones2021.csv")

df_estado = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estadocarga_limpio.csv")

df_viajes = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_viajes_limpio.csv") 

df_incidentes = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_fueraserv_limpio.csv")

df_vehiculos = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_vehiculos_limpio.xlsx")

temp = df_incidentes.groupby(["Estación"])["Desde"].count()
sns.barplot(x = temp.index, y = temp.values, palette = paleta)
plt.title('Cantidad de veces fuera de servicio por estación', fontsize = 18)
plt.xticks(rotation = 90, fontsize = 8)
plt.show()

temp = pd.crosstab(df_estado["status"], df_estado["id_station"])
temp = temp.stack().reset_index().rename(columns={0:'Cantidad de Ocurrencias'})
fig = sns.barplot(x = temp.id_station, y = temp["Cantidad de Ocurrencias"], hue = temp.status,  palette = [paleta[10], paleta[36]])
plt.xticks(rotation = 90, fontsize = 8)
plt.title('Cantidad de incidencias por estación', fontsize = 18)
sns.move_legend(fig, bbox_to_anchor=(1, 1.02), loc='upper left')
fig.set_xticklabels(list(df_estaciones["name"]))
plt.show()

df_viajes = df_viajes.loc[df_viajes["destination_station_nam"] != "55"] # me olvide de sacar esa jeje

# Heatmap estacion de origen por estacion destino
plt.figure(figsize = (35,35), dpi = 75)
plt.title('Gráfico de calor: estación de origen (x) por estación destino (y)', fontsize = 18)
sns.set(font_scale=0.8)
plt.xticks(fontsize = 8)
plt.yticks(fontsize = 8)
fig = sns.heatmap(pd.crosstab(df_viajes["destination_station_nam"], df_viajes["origin_station_nam"]),
    robust = True, linewidths = 0.006, linecolor='grey', cbar_kws = {"shrink": .82},)
plt.show()


#Creo 3 tablas, neto positivo, negativo y total

neto_llegada = pd.crosstab(df_viajes["destination_station_id"], df_viajes["hora_llegada_redondeada"])

neto_salida = pd.crosstab(df_viajes["origin_station_id"], df_viajes["hora_salida_redondeada"])

neto_total = (neto_llegada - neto_salida)

# Le agrego condicionales por hora y por estacion
temp = pd.DataFrame([neto_total.sum(axis = 0)], index = ["Suma por Hora"])
neto_total = neto_total.append(temp)

neto_total["Suma por Estacion"] = neto_total.sum(axis = 1)
neto_total

# Guardo en un excel la tabla neta
neto_total.to_excel(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\tabla_viajes_neto.xlsx")
neto_total["Suma por Estacion"].describe()
neto_total.loc["Suma por Hora"].describe()


# Esto me lleva a preguntar si hay cierto grupo de estaciones / horas en donde, ya sea por distintas razones, no 
# sea utilizado el servicio. Por lo tanto en vez de restar, voy a contar las salidas como un movimiento positivo
# (Por lo tanto, un viaje en vez de ser  neto 0 (+1 -1), pasara a ser +2). Divivido por los 92 dias que estoy teniendo en cuenta

movimiento_diario = (neto_llegada + neto_salida) 
movimiento_diario["Movimientos por dia por Estacion"] = movimiento_diario.sum(axis = 1)
movimiento_diario["Movimientos por dia por Estacion"].describe()

### TODO ESTE LABURO PARA UN GRAFICO LINDO AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

min = movimiento_diario["Movimientos por dia por Estacion"].min()
max = movimiento_diario["Movimientos por dia por Estacion"].max()
ancho = max - min
n = 10
ancho_columna = ancho/n

sns.histplot(movimiento_diario["Movimientos por dia por Estacion"], bins = n, binrange = (min, max), color = paleta[14])
plt.yticks([0,2,4,6,8,10,12,14,16,18])
plt.xticks(np.arange(min - ancho_columna, max + ancho_columna, ancho_columna))
plt.xlim(1000, 26180)
plt.title('Distribución de cantidad estaciones según movimientos por día', fontsize=18)
plt.xlabel('Movimientos (retiro o entrega de bicicleta)')
plt.ylabel('Cantidad de estaciones')
plt.show()

########### POR FIN FUNCIONA (casi) ###########################

plt.style.use('fivethirtyeight') #volver a tocar esto

movimiento_promedio = (neto_llegada + neto_salida) / 92
temp = pd.DataFrame([movimiento_promedio.sum(axis = 0)], index = ["Movimientos por dia por Hora"])
movimiento_promedio = movimiento_promedio.append(temp)

sns.lineplot(x = movimiento_promedio.columns, y = movimiento_promedio.iloc[-1], color = paleta[12])
plt.title('Cantidad de movimientos promedio Por hora', fontsize=18)
plt.xlabel('Hora')
plt.xticks(rotation = 45)
plt.ylabel('Movimientos (retiro o entrega de bicicleta)')
plt.show() 


# Creo subgrupo dependiendo de movimientos totales

neto_llegada_inv = pd.crosstab(df_viajes["hora_llegada_redondeada"], df_viajes["destination_station_id"])
neto_salida_inv = pd.crosstab(df_viajes["hora_salida_redondeada"], df_viajes["origin_station_id"])
movimiento_diario_inv = (neto_llegada_inv + neto_salida_inv)
temp = pd.DataFrame([movimiento_diario_inv.sum(axis = 0)], index = ["Movimientos por dia por Hora"])
movimiento_diario_inv = movimiento_diario_inv.append(temp)


fig = sns.barplot(x = movimiento_diario_inv.columns,y = movimiento_diario_inv[:-1].sum(axis = 0) / 92,
    palette = sns.cubehelix_palette(n_colors = 73, reverse = True))
plt.title('Cantidad de movimientos diarios promedio por estación', fontsize = 18)
plt.xlabel('Hora')
sns.set(font_scale=0.7)
fig.set_xticklabels(list(df_estaciones["name"]))
plt.xticks(rotation = 90)
plt.ylabel('Movimientos (retiro o entrega de bicicleta)')
plt.show() 

movimiento_diario_inv[:-1].sum(axis = 0).describe()

movimiento_diario_g1 = movimiento_diario_inv.loc[:, movimiento_diario_inv.iloc[-1] < 4090] # Q1 Q2 Q3
movimiento_diario_g2 = movimiento_diario_inv.loc[:, movimiento_diario_inv.iloc[-1] > 4090]
movimiento_diario_g2 = movimiento_diario_g2.loc[:, movimiento_diario_g2.iloc[-1] < 7919]
movimiento_diario_g3 = movimiento_diario_inv.loc[:, movimiento_diario_inv.iloc[-1] > 7919]
movimiento_diario_g3 = movimiento_diario_g3.loc[:, movimiento_diario_g3.iloc[-1] < 15075]
movimiento_diario_g4 = movimiento_diario_inv.loc[:, movimiento_diario_inv.iloc[-1] > 15075]

#preparo para plotear
movimiento_diario_g1 = movimiento_diario_g1[:-1] / 92
movimiento_diario_g2 = movimiento_diario_g2[:-1] / 92
movimiento_diario_g3 = movimiento_diario_g3[:-1] / 92
movimiento_diario_g4 = movimiento_diario_g4[:-1] / 92

fig = movimiento_diario_g1.plot(color = paleta)
paleta = sns.color_palette(n_colors = len(movimiento_diario_g1.columns), palette = cc.glasbey_dark)
for i in range(len(movimiento_diario_g1.columns)):
    fig.lines[i].set_color(paleta[i])
plt.title('Cantidad de movimientos diarios promedio por hora en estaciones de menos de 4090 viajes diarios (subgrupo 1)', fontsize = 18)
plt.xlabel('Hora')
plt.ylabel('Movimientos por hora (retiro o entrega de bicicleta)')
plt.legend(loc = 1, fontsize = 'small', title='ID estacion')
plt.show() 

fig = movimiento_diario_g2.plot()
paleta = sns.color_palette(n_colors = len(movimiento_diario_g2.columns), palette = cc.glasbey_dark)
for i in range(len(movimiento_diario_g2.columns)):
    fig.lines[i].set_color(paleta[i])
plt.title('Cantidad de movimientos diarios promedio por hora en estaciones entre 4090 y 7919 viajes diarios (subgrupo 2)', fontsize = 18)
plt.xlabel('Hora')
plt.ylabel('Movimientos por hora (retiro o entrega de bicicleta)')
plt.legend(loc = 1, fontsize = 'small', title='ID estacion')
plt.show() 

fig = movimiento_diario_g3.plot()
paleta = sns.color_palette(n_colors = len(movimiento_diario_g3.columns), palette = cc.glasbey_dark)
for i in range(len(movimiento_diario_g3.columns)):
    fig.lines[i].set_color(paleta[i])
plt.title('Cantidad de movimientos diarios promedio por hora en estaciones entre 7919 y 15075 viajes diarios (subgrupo 3)', fontsize = 18)
plt.xlabel('Hora')
plt.ylabel('Movimientos por hora (retiro o entrega de bicicleta)')
plt.legend(loc = 1, fontsize = 'small', title ='ID estacion')
plt.show() 

fig = movimiento_diario_g4.plot()
paleta = sns.color_palette(n_colors = len(movimiento_diario_g4.columns), palette = cc.glasbey_dark)
for i in range(len(movimiento_diario_g4.columns)):
    fig.lines[i].set_color(paleta[i])
plt.title('Cantidad de movimientos diarios promedio por hora en estaciones con más de 15075 viajes diarios (subgrupo 4)', fontsize = 18)
plt.xlabel('Hora')
plt.ylabel('Movimientos por hora (retiro o entrega de bicicleta)')
plt.legend(loc = 1, fontsize = 'small', title ='ID estacion')
plt.show()

#Grafico de viajes por dia
df_viajes["origin_date_name"] = df_viajes["origin_date_name"].astype("category")
df_viajes_sumadias = df_viajes.groupby("origin_date_name").count().iloc[:,1]
df_viajes_sumadias = df_viajes_sumadias.reindex(index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

fig = sns.barplot(x = df_viajes_sumadias.index,y = df_viajes_sumadias,
    palette = sns.cubehelix_palette(n_colors = 7, reverse = True))
plt.title('Suma de salidas totales según el día', fontsize = 18)
plt.xlabel('Dia')
sns.set(font_scale=0.7)
plt.ylabel('Retiro de bicicletas')
plt.show() 

#Loop para hacer graficos de cada estacion
paleta = sns.cubehelix_palette(n_colors = 3, reverse = True)
temp = 0
for columna in neto_salida_inv:
    fig = (neto_salida_inv[columna] / 92).plot(color = paleta[1])
    fig2 = (neto_llegada_inv[columna] / 92).plot(color = paleta[0])
    nombre = df_estaciones.loc[df_estaciones["id"] == neto_salida_inv[columna].name]
    nombre = nombre.iloc[0,2]
    plt.legend(["Salidas", "Llegadas"])
    plt.xlabel("Hora")
    plt.ylabel("Cantidad (en nro de bicis) promedio")
    plt.title(f'Movimiento promedio para estación {nombre}', fontsize = 18)
    plt.savefig(rf"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\plots\Salida por estacion por estacion\{neto_salida_inv[columna].name}.png", bbox_inches = "tight", dpi = 100)
    plt.close()



#Mapa con cada uno de los graficos anteriores dentro
centro_estaciones = [df_estaciones["lat"].mean(), df_estaciones["lon"].mean()]

mapa_grafico = folium.Map(location = centro_estaciones, tiles = 'Openstreetmap', zoom_start = 12, control_scale = True)
resolution, width, height = 30, 23, 16

for index, loc in df_estaciones.iterrows():
    temp = df_estaciones.iloc[index, 0]
    png = rf"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\plots\Salida por estacion por estacion\{temp}.png"
    html = '<img src="data:image/png;base64,{}">'.format
    encoded = base64.b64encode(open(png, 'rb').read()).decode()
    iframe = IFrame(html(encoded), width=(width*resolution)+20, height=(height*resolution)+20)
    popup = folium.Popup(iframe, max_width=2650)
    folium.CircleMarker([loc['lat'], loc['lon']], radius = 2, weight = 5, popup = popup).add_to(mapa_grafico)

folium.LayerControl().add_to(mapa_grafico)

mapa_grafico.save("mapa2.html")
webbrowser.open("mapa2.html") 

# Mapa  con circulo de radio 300M para fijarme si hay problemas en la distribucion de las estaciones.
# pd: si hay

mapa_300m = folium.Map(location = centro_estaciones, tiles = 'Openstreetmap', zoom_start = 12, control_scale = True)

for index, loc in df_estaciones.iterrows():
       
    folium.CircleMarker([loc['lat'], loc['lon']], radius = 2, weight = 5, popup = loc["name"]).add_to(mapa_300m)
    folium.Circle([loc['lat'], loc['lon']], radius = 300, weight = 5).add_to(mapa_300m)

mapa_300m.save("mapa.html")
webbrowser.open("mapa.html") 

########### Heatmap de viajes por dia
mapa_calor = folium.Map(location = centro_estaciones, tiles = 'Openstreetmap', zoom_start = 12, control_scale = True)
movimiento_diario_promedio = movimiento_diario_inv.iloc[-1] / 92
movimiento_diario_promedio = movimiento_diario_promedio.drop(index = (55))

df_calor = pd.DataFrame({"Lat" : df_estaciones.lat, "Lon" : df_estaciones.lon, 
    "Movimientos por Dia" : movimiento_diario_promedio.values })
df_calor.to_csv("df_calor.csv")
df_calor = df_calor.values.tolist()

temp = 20
colormap = branca.colormap.linear.YlOrRd_09.scale(0, 1).to_step(temp)
gradient_map = defaultdict(dict)
for i in range(temp):
    gradient_map[1/temp * i] = colormap.rgb_hex_str(1/temp * i)
colormap.add_to(mapa_calor) # barrita de color

heatmap = HeatMap(df_calor,gradient = gradient_map, min_opacity = 0.05, max_opacity = 0.9, radius = 30, 
use_local_extrema = False).add_to(mapa_calor)
mapa_calor.add_child(heatmap)

mapa_calor.save("mapacalor.html")
webbrowser.open("mapacalor.html") 

##########
df_viajes_diasemana = df_viajes.loc[(df_viajes["origin_date_name"] != "Saturday") & (df_viajes["origin_date_name"] != "Sunday")]
neto_llegada_diasemana = pd.crosstab(df_viajes_diasemana["hora_llegada_redondeada"], df_viajes_diasemana["destination_station_id"])
neto_salida_diasemana = pd.crosstab(df_viajes_diasemana["hora_salida_redondeada"], df_viajes_diasemana["origin_station_id"])
neto_diario_diasemana = (neto_llegada_diasemana - neto_salida_diasemana) / 66
neto_diario_diasemana = neto_diario_diasemana.drop(55, axis = 1)

#Gráfico lee el titulo jaja
paleta = sns.cubehelix_palette(n_colors = 73, reverse = True)
fig = sns.barplot(x = neto_diario_diasemana.columns, y = neto_diario_diasemana.sum(), palette = paleta)
fig.set_xticklabels(list(df_estaciones["name"]))
plt.title("Movimiento de bicicleta neto por estación (solo lunes a viernes)", fontsize = 18)
plt.xlabel("Estacion")
plt.ylabel("Cantidad")
plt.xticks(rotation = 90)
plt.show()

# No se gana nada de info por este gráfico xd ignorar 
df_vehiculos.groupby("Identificador vehículo")['Descripción tipo de zona'].count().plot(kind = "bar", 
    color = [paleta[0], paleta[20], paleta[40], paleta[60]])
plt.title("Zonas visitadas por vehículo")
plt.xticks(rotation = 0)
plt.show()

#WOLOLOOO esta en el titulo ya no quiero anotar
temp = df_vehiculos.groupby('Descripción de zona')["Identificador vehículo"].count()
plt.title("Cantidad de visitas (vehículo) por zona", fontsize = 18)
fig = temp.plot(kind = "bar", color = paleta[:69])
plt.ylabel("Visitas")
plt.show()

temp2 = df_estado.groupby("station_num")["status"].count()
a = []
for i in list(temp.index):
    a.append(int(''.join(c for c in i if c.isdigit())))
a[14] = 15
b = df_estaciones.sort_values(by = "station_code")
b[33] # filas 33, 49, 64 (-1 para ID) no estan en a
temp2 = temp2.drop([32, 48, 63]) # porque no tengo datos de viajes de estas
temp2 = temp2.sort_index(axis = 0)

# Grafico de dispersion de cantidad de visitas por cantidad de incidentes
modelo = np.poly1d(np.polyfit(temp2.values, temp.values, 2))
ax = np.linspace(0, 1200)
plt.plot(ax, modelo(ax), color = paleta[57])


sns.scatterplot(x = temp2.values, y  = temp.values, color = paleta[28])
plt.title("Cantidad de veces visitadas por cantidad de incidentes", fontsize = 18)
plt.xlabel("Incidentes")
plt.ylabel("Visitas")
plt.show()

#Movimientos pero separado en salidas y llegadas
fig, ax = plt.subplots()
sns.lineplot(y = (neto_llegada_inv.sum(axis = 1) / 92), x = neto_llegada_inv.index, ax = ax, color = paleta[14])
sns.lineplot(y = (neto_salida_inv.sum(axis = 1) / 92), x = neto_llegada_inv.index, ax = ax, color = paleta[56])
plt.title("Cantidad de movimientos promedio por hora", fontsize = 18)
plt.legend(["Llegadas", "Salidas"])
plt.xticks(rotation = 45)
plt.show()

#Este gráfico ve la cantidad de viajes en los que se volvio a la misma estacion. todavia no se si usarlo
df_viajes2 = df_viajes.loc[df_viajes["origin_station_id"] != df_viajes["destination_station_id"]]
temp = df_viajes.loc[df_viajes["origin_station_id"] == df_viajes["destination_station_id"]]
temp = temp.groupby("origin_station_id")["origin_station_id"].count()
fig = temp.plot(kind = "bar", color = paleta)
plt.show()

#Grafico de minutos totales de incidentes por estacion
temp = df_incidentes.groupby("Estación")["Duración"].sum()
paleta_temp = ["grey" if (x < 10000) else paleta[20] for x in temp.values]
temp.plot(kind = "bar", color = paleta_temp)
plt.title(r"$\bf{Minutos\ totales}$" + " fuera de servicio por estación", fontsize = 18)
plt.ylabel("Minutos")
plt.show()

