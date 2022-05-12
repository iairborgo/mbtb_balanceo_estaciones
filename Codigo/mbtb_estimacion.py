import pandas as pd
import numpy as np
from datetime import datetime
from joblib import dump, load
import sys


catb_estado = load(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\catb_estado.joblib")
catb_llegada = load(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\catb_llegada.joblib")
catb_salida = load(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\catb_salida.joblib")
df_estaciones = pd.read_csv(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\mbtb_estaciones2021.csv")
dic_estaciones = load(r"C:\Users\iairb\OneDrive\Escritorio\concurso-20220423T013420Z-001\concurso\dic_estaciones.pkl")


def check_fecha(ingresar_fecha):
    try: 
        ingresar_fecha = datetime.strptime(ingresar_fecha, "%d-%m-%Y %H:%M") 
        return ingresar_fecha
    except:
        print('Ingresar fecha valida en formato "dia-mes-año hora:minuto"')

# Esta funcion toma una fecha (formato : dia-mes-año hora:minuto) y nos devuelve una prediccion del estado
# De cada estacion (idealmente, horas del rango 06 - 00 hs.)

def predecir_estado_estacion(ingresar_fecha): 
    
    ingresar_fecha = check_fecha(ingresar_fecha)
    # Creo un dataframe para la prediccion. Con las var exp. en el mismo orden que el modelo
    df_dado = pd.DataFrame([[ingresar_fecha.weekday(), ingresar_fecha.month, ingresar_fecha.hour, ingresar_fecha.minute]],
        columns = ["dia", "mes", "hr", "min"]) # dia 0 = lunes
    
    estaciones =  pd.DataFrame(columns = ['id_station', "dia", "mes", "hr", "min"])
    estaciones['id_station'] = df_estaciones['id']
    estaciones.loc[:, 'dia'] = df_dado['dia'][0]
    estaciones.loc[:, 'mes'] = df_dado['mes'][0]
    estaciones.loc[:, 'hr'] = df_dado['hr'][0]
    estaciones.loc[:, 'min'] = df_dado['min'][0]

    estado_pred = catb_estado.predict(estaciones)
    
    estado_estacion = pd.DataFrame(
        {'id': df_estaciones['id'],
        'estado': pd.Series(estado_pred.tolist())})

    estado_estacion["estado"] = estado_estacion["estado"].astype(str).str.replace('[^a-zA-Z]', '', regex = True)

    return estado_estacion

# Ahora una funcion que prediga demanda

def predecir_demanda(ingresar_fecha): 

    ingresar_fecha = check_fecha(ingresar_fecha)
    df_dado = pd.DataFrame([[ingresar_fecha.weekday(), ingresar_fecha.month, ingresar_fecha.hour, ingresar_fecha.minute]],
        columns = ["dia", "mes", "hr", "min"]) # dia 0 = lunes

    estaciones = pd.DataFrame(columns = ['id_station', "dia", "mes", "hr", "min"])
    estaciones['id_station'] = df_estaciones['id']
    estaciones.loc[:, 'dia'] = df_dado['dia'][0]
    estaciones.loc[:, 'mes'] = df_dado['mes'][0]
    estaciones.loc[:, 'hr'] = df_dado['hr'][0]
    estaciones.loc[:, 'min'] = df_dado['min'][0]

    estaciones.rename(columns = {"id_station" : "destination_station_id", "dia" : "dia_llegada"}, inplace = True)
    llegada_pred = catb_llegada.predict(estaciones)

    estaciones.rename(columns = {"destination_station_id" : "origin_station_id", "dia_llegada" : "dia_salida"}, inplace = True)
    salida_pred = catb_salida.predict(estaciones)

    temp = estaciones[["origin_station_id"]].rename(columns = {"origin_station_id" : "id"})
    df_mov = pd.concat([temp, pd.Series(salida_pred.tolist()), pd.Series(llegada_pred.tolist())], axis = 1)
    
    
    return df_mov

#Estima :P
def estimar(ingresar_fecha):
    demanda = predecir_demanda(ingresar_fecha)
    estado_estacion = predecir_estado_estacion(ingresar_fecha)

    df = pd.merge(demanda, estado_estacion, on = "id")
    #df[0] = df[0].astype(str).str.replace(r'\D+', '', regex = True).astype(str) # elimina []
    #df[1] = df[1].astype(str).str.replace(r'\D+', '', regex = True).astype(int)
    df = df.rename(columns = {0 : "demanda_bici", 1 : "demanda_anclaje"})

    temp = lambda x: 1 if x == ["Baja"] else 2 if x == ["Media"] else 3
    df["demanda_bici"] = df.demanda_bici.apply(temp)
    df["demanda_anclaje"] = df.demanda_anclaje.apply(temp)
    
    df = df.sort_values("demanda_bici", ascending = False) 

    return df

# Genera lista de estaciones a las que ir  
def generar_lista_pares(poner, sacar, original_df, lista):
    # Busca la estacion vacia mas cercana a cada estacion llena
    for i in poner.id:
        estaciones_llenas = list(sacar.id)
        if len(estaciones_llenas) > 0: # Si no hay estaciones llenas esto no corre
            # Busca estacion mas cercana donde sacar bici
            df = pd.DataFrame(dic_estaciones[i], columns = ['estacion', 'distancia']).set_index('estacion')
            df = df.loc[estaciones_llenas].sort_values('distancia')
            estacion_proxima = int(list(df.index.values)[0])
            original_df = original_df.drop(original_df.loc[original_df['id'] == estacion_proxima].index[0])
            original_df = original_df.drop(original_df.loc[original_df['id'] == i].index[0])
            # Saca la estacion ya iterada de la lista
            sacar = sacar[sacar['id'] != estacion_proxima]

            lista.append((i, estacion_proxima))
        else:
            break
    return original_df, lista


def emparejar_estaciones(predicciones):
    df_copia = predicciones.copy()
    pares_estaciones = []

    # Genera 2 dataframes, uno que necesita bicis y otro que necesita anclajes. luego lo pasamos a la funcion anterior
    # Orden de prioridad : primero lleva a las que estas vacía de estaciones llenas.
    poner = df_copia[(df_copia['estado'] == "vacia")].reset_index().drop('index', axis = 1)
    sacar = df_copia[(df_copia["estado"] == "llena")].reset_index().drop('index', axis = 1)
    
    df_copia, pares_estaciones = generar_lista_pares(poner, sacar, df_copia, pares_estaciones)
    
    # Por si todavia quedan estaciones sin redistribuir vacias.
    poner = df_copia[(df_copia['estado'] == "vacia")].reset_index().drop('index', axis = 1)
    sacar = df_copia[(df_copia['estado'] != "vacia") & (df_copia['demanda_bici'] < df_copia['demanda_anclaje'])].reset_index().drop('index', axis = 1)
   
    df_copia, pares_estaciones = generar_lista_pares(poner, sacar, df_copia, pares_estaciones)
    
    # Ahora reordena las que tienen estado "normal" pero su demanda es asimétrica 
    poner = df_copia[(df_copia['estado'] != "llena") & (df_copia['demanda_bici'] > df_copia['demanda_anclaje'])].reset_index().drop('index', axis = 1)
    sacar = df_copia[(df_copia['estado'] != "vacia") & (df_copia['demanda_bici'] < df_copia['demanda_anclaje'])].reset_index().drop('index', axis = 1)

    df_copia, pares_estaciones = generar_lista_pares(poner, sacar, df_copia, pares_estaciones)

    
    # Por ultimo las que tienen demanda alta y anclaje menor (casi siempre) se van a vaciar por la forma que fueron
    # construidas estas mediciones en el modelo
    poner = df_copia[(df_copia["demanda_bici"] == 3) & (df_copia["demanda_anclaje"] < 3)].sort_values("demanda_anclaje")
    sacar = df_copia[(df_copia["demanda_anclaje"] == 3) & (df_copia["demanda_bici"] < 3)].sort_values("demanda_bici")
    
    df_copia, pares_estaciones = generar_lista_pares(poner, sacar, df_copia, pares_estaciones)

    return(pd.DataFrame(pares_estaciones, columns = ["Hasta estación nro", "Desde estación nro"]), df_copia)

def main():
    fecha = input("Ingresar fecha (formato: d-m-a hr:min)\n")
    df = estimar(fecha)
    lista_emparejada, temp = emparejar_estaciones(df)
    print(lista_emparejada)
    input("\n Presionar tecla para cerrar el programa ")

##################################### 

main()