
from dis import dis
import enum
from turtle import title
from unittest.mock import CallableMixin
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import tsp
import numpy as np
import pandas as pd
import haversine
import random

import folium
from folium.features import DivIcon
if __name__ == '__main__':

    """
    Datos a preparar para pasar al solver
    """

    dingqi = pd.read_csv('./rslt_df.csv')
    df = dingqi.sample(6)
    # Aplicar Haversine a cada uno para sacar la matriz de distancias en metros
    # asumo 1er elemento es depot
    distance_matrix = []
    for iIndex, iRow in df.iterrows():
        linea = []
        for jIndex, JRow in df.iterrows():
            linea.append(round(haversine.Haversine([iRow['Latitude'],iRow['Longitude']],[JRow['Latitude'],JRow['Longitude']]).meters))
        distance_matrix.append(linea)
    
    """
    Modelo y resolucion
    """
    
    # Crear la clase
    tsp = tsp.TSP()
    # Crear la estructura de datos con matriz de distancias y depot
    tsp.data = tsp.create_data_model(distance_matrix)
    # Crear el manager de rutas
    tsp.manager = pywrapcp.RoutingIndexManager(len(tsp.data['distance_matrix']),
                                       tsp.data['num_vehicles'], tsp.data['depot'])
    # Crear el modelo de rutas
    tsp.routing = pywrapcp.RoutingModel(tsp.manager)
    # Resolver el modelo e imprimir recorrido y distancia objetivo
    solver = tsp.TSP_solver()

    # Imprimir la solucion
    if (tsp.objectiveValue/5000) > 12:
        print("Tendrias que reducir el plan")

    npa = np.asarray(distance_matrix, dtype=np.float32)


    # 5km/h velocidad media humano andando
    # bucle tiempo cada recorrido
    recorrido = [] # lista con tiempos de cada movimiento en minutos
    for i in solver[0][:-1]:
        recorridoSingle = distance_matrix[solver[0][i]][solver[0][i+1]]
        recorridoTiempo = round((recorridoSingle/(5000))*60)
        recorrido.append(recorridoTiempo)

    # devuelve lugar de la ruta que estariamos para la hora de la comida
    horaComida = 14*60
    horaInicio = 10*60
    horaRecorrido = 0+horaInicio
    rutaComida=0
    for i, v in enumerate(recorrido):
        horaRecorrido+=v
        if(horaRecorrido >= 13*60 and horaComida <=15*60):
            rutaComida = i
            break

    # obtener i para sacar la fila del lugar donde estaremos a la hora de la comida
    i=0
    for iIndex, iRow in df.iterrows():
        if i==solver[0][rutaComida]:
            i=iIndex
            break
        i+=1
    
    # fila del dataset del lugar que estaremos a la hora de la comida
    latitudRastreo = dingqi["Latitude"].iloc[iIndex]
    longitudRastreo = dingqi["Longitude"].iloc[iIndex]

    # dataframe con los restaurantes
    stringlist = ["Bar", "Food", "Restaurant", "Joint", "Place"]
    restaurantes = dingqi[dingqi['Venue category name'].str.contains('|'.join(stringlist))]

    """
    encontrar restaurantes cercanos (1km)
    """
    rastreo = {}
    for i, row in restaurantes.iterrows():
        rastreo[i] = round(haversine.Haversine([row["Latitude"],row["Longitude"]],[latitudRastreo,longitudRastreo]).meters)

    # obtener dataframe_index/distancia de aquellos que esten a <= 1km del origen
    restaurantes1km =[]    
    for k, v in rastreo.items():
        if v <= 1000:
            restaurantes1km.append((k,v))

    # lista con los gustos de la entidad
    gustos = ['Sushi', 'Asian', 'Burger']

    """
    iterar sobre los gustos y elegir el primer restaurante en orden de preferencia, si no hubiera recomendar uno random
    """
    recomendacionIndex = None
    for gusto in gustos:    
        for restaurante in restaurantes1km:
            if restaurante[0] in restaurantes.index:
                if restaurantes.at[restaurante[0],'Venue category name'] == (gusto):
                    recomendacionIndex = restaurante[0]
                    break
    if recomendacionIndex is None:
        recomendacionIndex = random.choice(restaurantes1km)

    """
    añadir el restaurante a la ruta y computar nueva distancia y tiempo
    """
    restauranteFinal = dingqi.iloc[[recomendacionIndex[0]]]
    # añadir el restaurante a la ruta
    solver[0].insert(rutaComida+1, len(solver[0])-1)
    tsp.objectiveValue = tsp.objectiveValue/5000- (distance_matrix[solver[0][rutaComida]][solver[0][rutaComida+2]])/5000

    iniRestaurante = round(haversine.Haversine([df.iloc[solver[0][rutaComida]]["Latitude"],df.iloc[solver[0][rutaComida]]["Longitude"]],[restauranteFinal['Latitude'],restauranteFinal['Longitude']]).meters)
    finRestaurante = round(haversine.Haversine([restauranteFinal["Latitude"],restauranteFinal["Longitude"]],[df.iloc[solver[0][rutaComida+2]]['Latitude'],df.iloc[solver[0][rutaComida+2]]['Longitude']]).meters)
    
    tsp.objectiveValue = tsp.objectiveValue + iniRestaurante/5000 + finRestaurante/5000
    # dataframe con ultima row = restaurante
    df = df.append(restauranteFinal, ignore_index=False)
    print(df)
    # ruta modificada con el restaurante
    print(solver[0])
    # tiempo modificado con el restaurante (en horas)
    print(tsp.objectiveValue)


    # crear lista de tuplas con long,lat
    loc = []
    for i in solver[0]:
        loc.append((df.iloc[i]['Latitude'], df.iloc[i]['Longitude']))
    print(loc)

    # dibujar mapa
    m = folium.Map(location=loc[0],
                zoom_start=15)
    folium.PolyLine(loc,
                    color='red',
                    weight=15,
                    opacity=0.8).add_to(m)

    for i, v in enumerate(solver[0][:-1]):
        folium.Marker(loc[i], popup="<i>{"+"{}".format(df.iloc[v]['Venue ID'])+"}</i>", tooltip=None).add_to(m)

    text = "Tiempo total: {}h".format(tsp.objectiveValue)
    folium.map.Marker(
        loc[0],
        icon=DivIcon(
            icon_size=(200,86),
            icon_anchor=(0,0),
            html='<div style="font-size: 24pt">{}</div>'.format(text),
            )
        ).add_to(m)

    m.save("map.html")
