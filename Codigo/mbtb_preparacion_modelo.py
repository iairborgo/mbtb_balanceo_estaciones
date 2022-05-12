import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd
import geopy.distance
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from joblib import dump, load
from sklearn.svm import SVC
from catboost import CatBoostClassifier
from sklearn.neighbors import KNeighborsClassifier
import pickle
import seaborn as sns

df_viajes = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_viajes_limpio.csv")
df_estaciones = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estaciones2021.csv")
df_carga = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estadocarga_con_normales.csv")

df_carga.status.value_counts()
#Aca comienzo a manipular el DF viajes para luego emplear algun algo

df_viajes['origin_date'] = pd.to_datetime(df_viajes["origin_date"], format = "%Y-%m-%d")
df_viajes["destination_date"] = pd.to_datetime(df_viajes["destination_date"], format = "%Y-%m-%d")
df_viajes["dia_salida"] = df_viajes['origin_date'].dt.day_name()
df_viajes["dia_llegada"] = df_viajes['destination_date'].dt.day_name()
 
df_viajes = df_viajes.drop(['Unnamed: 0','origin_anchor_index','origin_date_name', 'origin_month',
    'destination_anchor_index', 'transhipment', 'time_minutes',
    'origin_station_num', 'origin_station_nam', 'destination_station_num','destination_station_nam',
    ], axis = 1)

# Como el servicio de reposicion solo funciona de 6 a 22, todos los viajes entre esas horas seran tirado hacia un lado
temp = ["22:30", "23:00", "23:30"]
for i in temp:
    df_viajes["hora_salida_redondeada"].loc[df_viajes["hora_salida_redondeada"] == i] = "22:00"
    df_viajes["hora_llegada_redondeada"].loc[df_viajes["hora_llegada_redondeada"] == i] = "22:00"

temp = ["00:00", "00:30","01:00", "01:30","02:00", "02:30","03:00", "03:30","04:00", "04:30","05:00", "05:30"]
for i in temp:
    df_viajes["hora_salida_redondeada"].loc[df_viajes["hora_salida_redondeada"] == i] = "06:00"
    df_viajes["hora_llegada_redondeada"].loc[df_viajes["hora_llegada_redondeada"] == i] = "06:00"

df_viajes_salida = df_viajes.groupby(['origin_station_id',"origin_date",'dia_salida','hora_salida_redondeada']).\
    count()[['origin_time']].reset_index().rename(columns = {'origin_time':'demanda_bici'})

df_viajes_llegada = df_viajes.groupby(['destination_station_id',"destination_date",'dia_llegada','hora_llegada_redondeada']).\
    count()[['destination_time']].reset_index().rename(columns = {'destination_time':'demanda_anclaje'})

############################################## curioso ##################################################
temp = sns.cubehelix_palette(n_colors = 20, reverse = True)
df_viajes_salida.demanda_bici.value_counts().plot(kind = "bar", color = temp)
plt.title("Distribución de bicicletas salidas de una estación en media hora", fontsize = 18)
plt.ylabel("Cantidad de ocurrencias")
plt.xlabel("Bicicleta saliendo / 30min")
plt.show()
########################################################################################################

temp = lambda x: "Baja" if x <= 1 else "Media" if x <= 4 else "Alta"
df_viajes_salida["demanda_bici"] = df_viajes_salida.demanda_bici.apply(temp) 
df_viajes_salida["demanda_bici"].value_counts()
df_viajes_llegada["demanda_anclaje"] = df_viajes_llegada.demanda_anclaje.apply(temp)

# Limpio un poco el dataset y dejo las cosas con las que me interesa implemetar la regresion
x = df_viajes_salida
x["origin_date"] = pd.to_datetime(x["origin_date"], format = "%Y-%m-%d")
x["mes"] = pd.DatetimeIndex(x['origin_date']).month
temp = x.hora_salida_redondeada.str.split(":", expand = True)
temp.columns = ['hr','min']
temp['hr'] = temp['hr'].astype('int32')
temp['min'] = temp['min'].astype('int32')
x = pd.merge(x, temp, left_index = True, right_index = True)
x = x.drop(columns = ["origin_date","hora_salida_redondeada"]) 

x["dia_salida"] = pd.Categorical(x["dia_salida"], ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Monday"])
x = x.sort_values("dia_salida")

x["dia_salida"] = pd.factorize(x["dia_salida"])[0] # Convierto el dia en variable categórica
y = x["demanda_bici"]
x = x.drop(columns = ["demanda_bici"])




#Separo el dataset para entreno y testeo
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.15, random_state = 0)

# Probe con RandomForest, me da una eficacia (levemente) menor

# clf = RandomForestClassifier(random_state = 0, verbose = True, n_jobs = -1)
# clf.fit(x_train, y_train)
# clf.score(x_test, y_test)

parametros = {    'depth'         : [2,4,6,8,10],
                  'learning_rate' : [0.01, 0.025, 0.05, 0.1, 0.125],
                  'iterations'    : [30, 50, 100, 300, 500, 750]
                 }
catB = CatBoostClassifier()
from sklearn.model_selection import GridSearchCV
gs = GridSearchCV(catB, param_grid = parametros, cv = 2, n_jobs = -1)
gs.fit(x_train, y_train, eval_set = (x_test, y_test))

gs.best_score_
gs.best_params_

parametros = {    'depth'         : [3,4,5],
                  'learning_rate' : [0.115, 0.12, 0.125],
                  'iterations'    : [500, 750, 1000]
                 }

gs = GridSearchCV(catB, param_grid = parametros, cv = 2, n_jobs = -1)
gs.fit(x_train, y_train, eval_set = (x_test, y_test))

gs.best_score_
gs.best_params_ # {'depth': 4, 'iterations': 750, 'learning_rate': 0.12}

catB = CatBoostClassifier(depth = 4, learning_rate = 0.12, iterations = 750) 
catB.fit(x_train, y_train, eval_set = (x_test, y_test))
catB.score(x_test, y_test) # 0.6
print(catB.feature_importances_) # aca se ve que tanto peso tiene cada varialbe

# Aunque el mes no aporte mucho, decidi dejarlo por si quiero agregar datos de enero a septiembre en el futuro

x2 = df_viajes_llegada
x2["destination_date"] = pd.to_datetime(x2["destination_date"], format = "%Y-%m-%d")
x2["mes"] = pd.DatetimeIndex(x2['destination_date']).month
temp = x2.hora_llegada_redondeada.str.split(":", expand = True)
temp.columns = ['hr','min']
temp['hr'] = temp['hr'].astype('int32')
temp['min'] = temp['min'].astype('int32')
x2 = pd.merge(x2, temp, left_index = True, right_index = True)
x2 = x2.drop(columns = ["destination_date", "hora_llegada_redondeada"])

x2["dia_llegada"] = pd.Categorical(x2["dia_llegada"], ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Monday"])
x2 = x2.sort_values("dia_llegada")
x2["dia_llegada"] = pd.factorize(x2["dia_llegada"])[0]

y2 = x2["demanda_anclaje"]
x2 = x2.drop(columns = "demanda_anclaje")

x2_train, x2_test, y2_train, y2_test = train_test_split(x2, y2, test_size = 0.15, random_state = 0)

# De nuevo, el algoritmo que mejor se adecua a la base de datos es CatBoost

# clf2 = RandomForestClassifier(random_state = 0, verbose=True, n_jobs = -1)
# clf2.fit(x2_train, y2_train)
# clf2.score(x_test, y_test)

# x2_std = StandardScaler().fit_transform(x2)
# knc2 = KNeighborsClassifier(n_neighbors = np.sqrt(x2_std.shape[0]), n_jobs = -1) 
# knc2.fit(x2_train, y2_train)
# knc2.score(x2_test, y2_test)

catB2 = CatBoostClassifier(depth = 4, learning_rate = 0.12, iterations = 750)
catB2.fit(x2_train, y2_train, eval_set = (x2_test, y2_test))
catB2.score(x2_test, y2_test) 

# Ahora hay que hacer lo mismo con el df de estado de carga

x3 = df_carga.drop(columns = ['Unnamed: 0','reported_anchors', 'hora_fin', 'fin'])
x3["inicio"] = pd.to_datetime(x3["inicio"], format = "%Y-%m-%d")
x3["mes"] = pd.DatetimeIndex(x3['inicio']).month
x3 = x3.drop(columns = "inicio")

temp = x3.hora_inicio.str.split(":", expand = True)
temp.columns = ['hr','min']
temp['hr'] = temp['hr'].astype('int32')
temp['min'] = temp['min'].astype('int32')
x3 = pd.merge(x3, temp, left_index = True, right_index = True)
x3 = x3.drop(columns = ["hora_inicio", "occupied_anchors", "free_anchors", "blocked_anchors"])

temp = [22, 23] # me olvide de reordenarla antes
for i in temp:
    x3["hr"].loc[x3["hr"] == i] = 21
temp = [1, 2, 3, 4, 5]
for i in temp:
    x3["hr"].loc[x3["hr"] == i] = 6

x3["dia"] = pd.Categorical(x3["dia"], ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Monday"])
x3 = x3.sort_values("dia")
x3["dia"] = pd.factorize(x3["dia"])[0]

y3 = x3["status"]
x3 = x3.drop(columns = "status")

x3_train, x3_test, y3_train, y3_test = train_test_split(x3, y3, test_size = 0.2, random_state = 0)

catB3 = CatBoostClassifier(depth = 2)
catB3.fit(x3_train, y3_train, eval_set = (x3_test, y3_test))
catB3.score(x3_test, y3_test)
dump(catB3, 'catb_estado.joblib')

#Crea un diccionario (con [] buscas una estacion) para la distancia a otras estaciones (en km).
dic_estaciones = {}
for estacion in df_estaciones.id.unique().tolist():
    loc1 = (df_estaciones[df_estaciones.id == estacion].lat.values, df_estaciones[df_estaciones.id == estacion].lon.values)
    otras = [x for x in df_estaciones.id.unique().tolist() if x != estacion]
    dist = {}
    for otra in otras:
        loc2 = (df_estaciones[df_estaciones.id == otra].lat.values, df_estaciones[df_estaciones.id == otra].lon.values)
        distancia = geopy.distance.distance(loc1, loc2).km
        dist[otra] = distancia
    dist = sorted(dist.items(), key = lambda kv:(kv[1], kv[0])) # lo ordena en menor a mayor
    dic_estaciones[estacion] = dist

temp = open('dic_estaciones.pkl', 'wb')
pickle.dump(dic_estaciones, temp, -1)
temp.close()
