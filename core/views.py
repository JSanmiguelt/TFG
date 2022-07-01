import os

import pandas as pd
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponse
from django.shortcuts import render
from TFG import settings
import static.tsp as tsp
import static.haversine as haversine
import folium
from folium.features import DivIcon
from ortools.constraint_solver import pywrapcp
import numpy as np
import random

# Create your views here.

def home(request):
    return render(request, 'home.html', {})

def about(request):
    return render(request, 'about.html', {})

def places(request):
    if request.method == 'POST':
        main(request)
        return render(request, 'mostrarRuta.html')
    
    
    dingqi = pd.read_csv('static/final.csv')
    POI = ['Other Great Outdoors','Music Venue', 'Park', 'Stadium', 'Church',
            'Performing Arts Venue', 'Art Gallery', 'Plaza', 'Cemetery', 
            'Museum','Concert Hall',  'Theater', 'Movie Theater', 'Scenic Lookout',
            'Synagogue','Arts & Entertainment', 'Garden','Harbor / Marina',
            'College Theater',  'Outdoors & Recreation', 'River','Beach', 'Temple',
            'Historic Site', 'History Museum','Sculpture Garden', 'Science Museum',
            'Art Museum', 'Zoo', 'Shrine', 'Aquarium', 'Mosque','Fair',
            'Planetarium', 'Public Art', 'Garden Center', 'Castle']
    rslt_df = dingqi.loc[dingqi['Venue category name'].str.contains('|'.join(POI))]
    places = rslt_df['Venue ID'].tolist()

    stringlist = ['Food Truck', 'Gastropub','Restaurant', 'American Restaurant',
        'Mexican Restaurant','Burger Joint','Pizza Place','Sandwich Place', 'Soup Place',
        'Diner','Cuban Restaurant', 'BBQ Joint','Italian Restaurant',
        'Bar', 'Spanish Restaurant', 'Asian Restaurant','Burrito Place',
        'Fast Food Restaurant', 'Dumpling Restaurant', 'Wings Joint', 
        'Caribbean Restaurant', 'French Restaurant',
        'Salad Place', 'Vegetarian / Vegan Restaurant','Sushi Restaurant',
        'Chinese Restaurant', 'Latin American Restaurant','Southern / Soul Food Restaurant',
        'Fried Chicken Joint',
        'Middle Eastern Restaurant', 'Seafood Restaurant',
        'Japanese Restaurant','German Restaurant'
        'Indian Restaurant', 'Hot Dog Joint', 'Steakhouse', 
        'Thai Restaurant', 'Food', 'Ramen /  Noodle House', 
        'Mediterranean Restaurant', 'Beer Garden', 'African Restaurant',
        'Malaysian Restaurant',
        'Taco Place', 'South American Restaurant',
        'Brazilian Restaurant', 'Greek Restaurant', 'Falafel Restaurant', 'Tapas Restaurant',
        'Eastern European Restaurant', 'Korean Restaurant',
        'Portuguese Restaurant', 'Cajun / Creole Restaurant', 'Mac & Cheese Joint',
        'Vietnamese Restaurant', 'Dim Sum Restaurant', 'Swiss Restaurant',
        'Australian Restaurant', 'Peruvian Restaurant','Filipino Restaurant',
        'Arepa Restaurant', 'Turkish Restaurant', 'Scandinavian Restaurant',
        'Fish & Chips Shop', 'Afghan Restaurant','Ethiopian Restaurant',
        'Gluten-free Restaurant', 'Argentinian Restaurant', 'Moroccan Restaurant',
        'Molecular Gastronomy Restaurant']
    rslt_df = dingqi[dingqi['Venue category name'].str.contains('|'.join(stringlist))]
    restaurants = rslt_df['Venue category name'].unique().tolist()

    return render(request, 'places.html', {
            'places': places,
            'restaurants': restaurants,
    })

def main(request):
    """
    Datos a preparar para pasar al solver
    """
    dingqi = pd.read_csv('static/final.csv')
    lugares=[]
    for item in request.POST.getlist('inicio'):
        lugares.append('{}'.format(item))
    for item in request.POST.getlist('places'):
        lugares.append('{}'.format(item))
    df = dingqi[dingqi['Venue ID'].isin(lugares)]
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
    tspm = tsp.TSP()
    # Crear la estructura de datos con matriz de distancias y depot
    tspm.data = tspm.create_data_model(distance_matrix)
    # Crear el manager de rutas
    tspm.manager = pywrapcp.RoutingIndexManager(len(tspm.data['distance_matrix']),
                                       tspm.data['num_vehicles'], tspm.data['depot'])
    # Crear el modelo de rutas
    tspm.routing = pywrapcp.RoutingModel(tspm.manager)
    # Resolver el modelo e imprimir recorrido y distancia objetivo
    solver = tspm.TSP_solver()

    # Imprimir la solucion
    if (tspm.objectiveValue/5000) > 12:
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
    stringlist = ['Food Truck', 'Gastropub','Restaurant', 'American Restaurant',
            'Mexican Restaurant','Burger Joint','Pizza Place','Sandwich Place', 'Soup Place',
            'Diner','Cuban Restaurant', 'BBQ Joint','Italian Restaurant',
            'Bar', 'Spanish Restaurant', 'Asian Restaurant','Burrito Place',
            'Fast Food Restaurant', 'Dumpling Restaurant', 'Wings Joint', 
            'Caribbean Restaurant', 'French Restaurant',
            'Salad Place', 'Vegetarian / Vegan Restaurant','Sushi Restaurant',
            'Chinese Restaurant', 'Latin American Restaurant','Southern / Soul Food Restaurant',
            'Fried Chicken Joint',
            'Middle Eastern Restaurant', 'Seafood Restaurant',
            'Japanese Restaurant','German Restaurant'
            'Indian Restaurant', 'Hot Dog Joint', 'Steakhouse', 
            'Thai Restaurant', 'Food', 'Ramen /  Noodle House', 
            'Mediterranean Restaurant', 'Beer Garden', 'African Restaurant',
            'Malaysian Restaurant',
            'Taco Place', 'South American Restaurant',
            'Brazilian Restaurant', 'Greek Restaurant', 'Falafel Restaurant', 'Tapas Restaurant',
            'Eastern European Restaurant', 'Korean Restaurant',
            'Portuguese Restaurant', 'Cajun / Creole Restaurant', 'Mac & Cheese Joint',
            'Vietnamese Restaurant', 'Dim Sum Restaurant', 'Swiss Restaurant',
            'Australian Restaurant', 'Peruvian Restaurant','Filipino Restaurant',
            'Arepa Restaurant', 'Turkish Restaurant', 'Scandinavian Restaurant',
            'Fish & Chips Shop', 'Afghan Restaurant','Ethiopian Restaurant',
            'Gluten-free Restaurant', 'Argentinian Restaurant', 'Moroccan Restaurant',
            'Molecular Gastronomy Restaurant']
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

    gustos=[]
    for item in request.POST.getlist('restaurants'):
        gustos.append('{}'.format(item))

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
        recomendacionIndex = recomendacionIndex[0]

    """
    añadir el restaurante a la ruta y computar nueva distancia y tiempo
    """
    restauranteFinal = dingqi.iloc[[recomendacionIndex]]
    # añadir el restaurante a la ruta
    solver[0].insert(rutaComida+1, len(solver[0])-1)
    tspm.objectiveValue = tspm.objectiveValue/5000- (distance_matrix[solver[0][rutaComida]][solver[0][rutaComida+2]])/5000

    iniRestaurante = round(haversine.Haversine([df.iloc[solver[0][rutaComida]]["Latitude"],df.iloc[solver[0][rutaComida]]["Longitude"]],[restauranteFinal['Latitude'],restauranteFinal['Longitude']]).meters)
    finRestaurante = round(haversine.Haversine([restauranteFinal["Latitude"],restauranteFinal["Longitude"]],[df.iloc[solver[0][rutaComida+2]]['Latitude'],df.iloc[solver[0][rutaComida+2]]['Longitude']]).meters)
    
    tspm.objectiveValue = tspm.objectiveValue + iniRestaurante/5000 + finRestaurante/5000
    # dataframe con ultima row = restaurante
    df = df.append(restauranteFinal, ignore_index=False)

    # crear lista de tuplas con long,lat
    loc = []
    for i in solver[0]:
        loc.append((df.iloc[i]['Latitude'], df.iloc[i]['Longitude']))

    # dibujar mapa
    m = folium.Map(location=loc[0],
                zoom_start=15)
    folium.PolyLine(loc,
                    color='red',
                    weight=15,
                    opacity=0.8).add_to(m)

    for i, v in enumerate(solver[0][:-1]):
        if v==max(solver[0][:-1]):
            folium.Marker(loc[i], icon = folium.Icon(color='green', prefix='fa', icon='cutlery'), popup="<i>{"+"Restaurante:"+"{}".format(df.iloc[v]['Venue ID'])+". Estilo:"+"{}".format(df.iloc[v]['Venue category name'])+"}</i>", tooltip=None).add_to(m)
        elif v==min(solver[0][:-1]):
            folium.Marker(loc[i], icon = folium.Icon(color='brown', prefix='fa', icon='user'), popup="<i>{"+"Inicio:"+"{}".format(df.iloc[v]['Venue ID'])+"}</i>", tooltip=None).add_to(m)
        else:
            folium.Marker(loc[i], popup="<i>{"+"{}:".format(i+1)+"{}".format(df.iloc[v]['Venue ID'])+"}</i>", tooltip=None).add_to(m)

    text = "Tiempo total: {:.2f}horas".format(tspm.objectiveValue)
    folium.map.Marker(
        loc[0],
        icon=DivIcon(
            icon_size=(200,86),
            icon_anchor=(0,0),
            html='<div style="font-size: 24pt">{}</div>'.format(text),
            )
        ).add_to(m)

    m.save("static/templates/map.html")

    return render(request, 'mostrarRuta.html')
