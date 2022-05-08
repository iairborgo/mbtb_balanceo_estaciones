# Mi Bici Tu Bici: Balanceo de Estaciones.

Trabajo realizado con datos aportados por la Municipalidad de Rosario, con el objetivo de ser presentado en el Premio Dra. Elsa Servy, llevado a cabo por la Escuela de Estadística de la Facultad de Ciencias Económicas y Estadística de la Universidad Nacional de Rosario conjuntamente con el Consejo Profesional de Ciencias Económicas de la Provincia de Santa Fe - Cámara II y el Colegio de Graduados de Ciencias Económicas de Rosario (CPCE-CGCE).

## Objetivo:

El objetivo principal del proyecto era optimizar el procedimiento de balanceo mediante la descripción de la oferta y demanda de cada estación y proveer una solución al problema de abastecimiento de ellas.

Todo este proyecto fue llevado a cabo en lapso de un mes, para poder realizar esto utilice varias librerias de python (Pandas, Numpy, Seaborn, etc) que aprendí a usar durante el transcurso. Note una gran mejora en fluidez y entendimiento del código en el camino, sirviendo como experiencia de cara a futuro.

## Limpieza de datos:

Fueron proporcionados 5 dataframes (viajes, estaciones, fuera de servicio, estado de carga y entradas/salidas de vehiculos) junto a un diccionario correspondiente. Los datos son de todo el año 2021 pero por recomendación solo mantuve las observaciones correspondientes al periodo Oct.-Nov.

El primer paso a realizar fue la limpieza de estos (mbtb_limpieza.py), donde se encontraba muchas columnas que no eran utiles con respecto al problema en cuestión.
Tambien se eliminaron muchas observaciones de estaciones que no están disponibles para el uso público. 
Todo lo que tenía que ver respecto a horarios fue llevado a UTC-3 ( originalmente en UTC+0 ) y agrupado en intervalos de 30 minutos para facilitar el análisis y trabajo computacional.

## Analisis Exploratorio:

Muchos gráficos útiles ya habían sido dados en la presentación del concurso, por lo que me limité solo a los que daban una orientacion en como enmarcar el problema (mbt_exploracion.py). Tambien realicé 3 mapas donde en uno se veía una distribución de calor de movimientos promedios, y en otro podias elegir cada estación y ver sus movimientos por hora.

Estos y más pueden ser vistos en la presentación.
![Salidas segun dia](https://user-images.githubusercontent.com/105130558/167307979-ed5c6bd4-2728-47a2-961d-14726ac18e34.png)
![Movimientos netos por estacion](https://user-images.githubusercontent.com/105130558/167308001-41c7f7bf-6c3f-44ed-af0a-aeb8211256ac.png)
![movimientos por hora desagregado](https://user-images.githubusercontent.com/105130558/167308002-38e9feee-2ae3-40d8-a328-6883bc2af053.png)
![Mapa](https://user-images.githubusercontent.com/105130558/167308314-cfe55d84-60cc-40ad-abf7-ba2a1d1d1dbe.png)

## Modelo:

Ya habiendo recolectado información, la estrategia que encaré para la reposición de bicicleta giró en torno a  predecir (mbtb_preparacion_modelo.py) 3 medidas:
- Estado de estación.
- Cantidad de bicicletas que salen (por media hora).
- Cantidad de bicicletas que entran (por media hora).

Intente crear una nueva columna en donde se vea el porcentaje de ocupación de una estacion x, pero ocurrian inconsistencias debido a la forma que la base de datos tomaba los anclajes bloqueados. Mientras hacia esto, me di cuenta que en la base de datos de estado, las que eran consideradas "normales" podían tener solo 1 bici disponible y, generalmente, el problema más común era la *falta* de bicicletas en una estación.

Aplicando diversos  modelos (entre ellos: RandomForest, KNeighbors, Support Vector Machine) llegue a que [CatBoost](https://en.wikipedia.org/wiki/Catboost) (una libreria que se basa en [Gradient Boosting](https://en.wikipedia.org/wiki/Gradient_boosting)) era la que mejor funcionaba con las variables que estaba utilizando.
Hecho las modificaciones en el DataFrame necesarias para que el algoritmo pueda correr (codificando variable categórica), y separandolo para entreno y testeo, procedí a usar GridSearchCV para hallar los mejores hiperparámetros (en el tiempo que tuve, puede ser que haya una configuración mejor)

## Resultados

Para poder dar una respuesta al problema, cree un diccionario con cada estación, que contiene listas a la distancia hacia otra estaciones.
Entonces dado una fecha,  el programa devuelve una lista de recomedación de cual estacion *sacar* y a cual *llevar* bicicletas (toma la mas cercana, dependiendo de distintas condiciones). Esta lista está dada en un orden de prioridad (este se puede ver en mbtb_estimacion.py).

![Lista](https://user-images.githubusercontent.com/105130558/167309198-c3a920be-4929-4fbb-9ca1-e2d87d926b33.png)


### Conclusión

Lejos de lo ideal, esto nos ayuda a a reacomodar las bicicletas no solo teniendo la información actual, sino también el movimiento *estimado* de cada estación. Creo que esto puede ser mejorado sumando variables como "estado de clima", y dandole al regresór mas data (algunas estaciones hasta consideré no usarlas debido a la baja cantidad de observaciones).

También pensando otra idea fue que, si tuviese el acceso a data en tiempo real, se podria recolectar por hora la cantidad de salidas y entradas para aplicar algun algoritmo involucrando series de tiempo que intente predecir el movimiento del siguiente día para tener una mejor estrategia al momento de optimizar. Pero esto llevaría un trabajo más extenso y herramientas que, francamente, no estoy familiarizado todavía.



#### ***Este trabajo utilizó partes de otros compartido bajo código abierto***
#### ***Contacto***: iairborgo@gmail.com

