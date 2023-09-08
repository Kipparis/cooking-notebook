# cooking-notebook
Calculations and suggestions on recipes

# Откуда достаются нутриенты

The FoodData Central API provides REST access to FoodData Central (FDC). It is intended primarily to assist application developers wishing to incorporate nutrient data into their applications or websites.\n  To take full advantage of the API, developers should familiarize themselves with the database by reading the database documentation available via links on [Data Type Documentation](https://fdc.nal.usda.gov/data-documentation.html). This documentation provides the detailed definitions and descriptions needed to understand the data elements referenced in the API documentation.\n  \n  Additional details about the API including rate limits, access, and licensing are available on the [FDC website](https://fdc.nal.usda.gov/api-guide.html)

# Добавляя рецепты
Чтобы не возникало разногласий при попытке сборки ингридиентов, соблюдай правила написания названий продуктов:  
Более общее прилагательное &rarr; частное прилагательное &rarr; существительное.  

**_Не используй дробные числа (1/3) когда указываешь количетсво._**  
**_Наименования продуктов указывай в единственном числе_**  

Список сокращейний (опускаем окончания):  

+ штуки - шт  
+ ломтик - лом.  
+ зубчик - зуб.  
+ чайная ложка - ч. л.  
+ столовая ложка - ст. л.  
+ стакан - ст.  
+ грамм - г.  
+ листр - л  
+ миллилитр - мл  
+ лист _(для лаваша например)_ - лист  
+ пучок _(кинзы)_ - пуч  
+ головка _(лука)_ - гол  

## Перевод в граммы\мг\мкг

Используется только для того, чтобы подсчитывать нужно кол-во нутриентов (в базе не должно хранится записи о кол-ве в стаканах и о кол-ве в г.)

# Планы

+ json по продуктам в каждом поле указанно:  
    - pH  
    - эн. ценность  
    - микро\макроэлементы  
    - категория (фрукты, крахмалы, углеводы, жиры, белки, овощи)  
+ проходимся по элементам в рецепте и предупреждаем, если есть
  несопоставимые (в зависимости от категории)  
