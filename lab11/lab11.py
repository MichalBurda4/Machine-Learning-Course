# -*- coding: utf-8 -*-
"""Untitled15.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ZJ0Z9LhrV9Npe8KzLXF8km5nA7g07ITU

**Laboratorium: Analiza obrazów przy pomocy sieci konwolucyjnych**

**1 Zakres ćwiczeń**

• Wykorzystanie konwolucyjnych sieci neuronowych (CNN) do analizy obrazu.

• Pobieranie gotowego modelu przy pomocy biblioteki Tensorflow Datasets.

• Przetwarzanie i udostępnianie danych przy
pomocy Dataset API.

• Wykorzystanie gotowych modeli do uczenia transferowego.

**2 Ćwiczenia**
"""

import pandas as pd
import tensorflow as tf
import tensorflow_datasets as tfds
import matplotlib.pyplot as plt
import pickle

"""2.1 Ładowanie danych

Do załadowania danych skorzystamy z pakietu Tensorflow Datasets, który udostępnia wiele zbiorów
przydatnych do uczenia maszynowego. Aby utrzymać względnie krótkie czasy uczenia, do ćwiczeń
będziemy używać zbioru tf_flowers:
"""

import tensorflow_datasets as tfds
[test_set_raw, valid_set_raw, train_set_raw], info = tfds.load(
"tf_flowers",
split=['train[:10%]', "train[10%:25%]", "train[25%:]"],
as_supervised=True,
with_info=True)

"""Kilka słów o argumentach metody load:

• split zapewnia odpowiedni podział zbioru (dlatego pierwszy element zwracanej krotki jest
3-elementowym słownikiem),

• as_supervised sprawia, że zwracane obiekty tf.data.Dataset mają postać krotek zawierających zarówno cechy, jak i etykiety,

• with_info dodaje drugi element zwracanej krotki.

Możemy łatwo wyekstrahować istotne parametry zbioru:
"""

class_names = info.features["label"].names
n_classes = info.features["label"].num_classes
dataset_size = info.splits["train"].num_examples

plt.figure(figsize=(12, 8))
index = 0
sample_images = train_set_raw.take(9)
for image, label in sample_images:
  index += 1
  plt.subplot(3, 3, index)
  plt.imshow(image)
  plt.title("Class: {}".format(class_names[label]))
  plt.axis("off")
  plt.show(block=False)

"""**2.2 Budujemy prostą sieć CNN**

2.2.1 Przygotowanie danych

Sieć będzie przetwarzała obrazy o rozmiarze 224 × 224 pikseli, a więc pierwszym krokiem będzie
przetworzenie. Obiekty Dataset pozwalają na wykorzystanie metody map, która przy uczeniu
nadzorowanym będzie otrzymywała dwa argumenty (cechy, etykieta) i powinna zwracać je w postaci
krotki po przetworzeniu.

Najprostsza funkcja będzie po prostu skalowała obraz do pożądanego rozmiaru:
"""

def preprocess(image, label):
  resized_image = tf.image.resize(image, [224, 224])
  return resized_image, label

"""Aplikujemy ją do pobranych zbiorów:"""

batch_size = 32
train_set = train_set_raw.map(preprocess).shuffle(dataset_size).batch(batch_size).prefetch(1)
valid_set = valid_set_raw.map(preprocess).batch(batch_size).prefetch(1)
test_set = test_set_raw.map(preprocess).batch(batch_size).prefetch(1)

plt.figure(figsize=(8, 8))
sample_batch = train_set.take(1)
print(sample_batch)
for X_batch, y_batch in sample_batch:
  for index in range(12):
    plt.subplot(3, 4, index + 1)
    plt.imshow(X_batch[index]/255.0)
    plt.title("Class: {}".format(class_names[y_batch[index]]))
    plt.axis("off")

plt.show()

"""**2.2.2 Budowa sieci**"""

model = tf.keras.models.Sequential([
    tf.keras.layers.Rescaling(1./255),
    tf.keras.layers.Conv2D(filters=96, kernel_size=7, padding="same", activation="relu"),
    tf.keras.layers.MaxPool2D(pool_size=2),
    tf.keras.layers.Conv2D(filters=256, kernel_size=5, padding="same", activation="relu"),
    tf.keras.layers.MaxPool2D(pool_size=2),

    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(256, activation="relu"),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(n_classes, activation="softmax")
])

model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
model.fit(train_set, epochs=10, validation_data=valid_set)

eval_tuple = (model.evaluate(train_set), model.evaluate(valid_set), model.evaluate(test_set))
print(model.summary())

import pickle

with open('simple_cnn_acc.pkl', 'wb') as f:
    pickle.dump(eval_tuple, f)

model.save("simple_cnn_flowers.keras")

"""**2.3 Uczenie transferowe**

**2.3.1 Przygotowanie danych**
"""

import tensorflow as tf

def preprocess(image, label):
  # Zmiana rozmiaru obrazu do 224x224 pikseli
  resized_image = tf.image.resize(image, [224, 224])

  # Przetwarzanie obrazu przy użyciu funkcji preprocess_input z modelu Xception
  # Funkcja ta przekształca obraz tak, aby był zgodny z wymaganiami modelu Xception
  final_image = tf.keras.applications.xception.preprocess_input(resized_image)

  # Zwrócenie przetworzonego obrazu oraz etykiety
  return final_image, label

batch_size = 32

train_set = train_set_raw.map(preprocess).shuffle(dataset_size).batch(batch_size).prefetch(1)
valid_set = valid_set_raw.map(preprocess).batch(batch_size).prefetch(1)
test_set = test_set_raw.map(preprocess).batch(batch_size).prefetch(1)

import matplotlib.pyplot as plt

# Ustawienie wielkości figury (okna) wykresu na 8x8 cali
plt.figure(figsize=(8, 8))

# Pobranie jednej partii danych z zestawu treningowego
sample_batch = train_set.take(1).repeat()

# Iteracja przez partie danych (w tym przypadku tylko jedna partia)
for X_batch, y_batch in sample_batch:
  # Wyświetlenie 12 obrazów z partii
  for index in range(12):
    # Dodanie subplotu do figury, z 3 wierszami i 4 kolumnami
    plt.subplot(3, 4, index + 1)

    # Wyświetlenie obrazu (zde-normalizacja, zakładając że obrazy zostały przeskalowane do zakresu [-1, 1])
    plt.imshow(X_batch[index] / 2 + 0.5)

    # Ustawienie tytułu subplotu na nazwę klasy dla bieżącego obrazu
    plt.title("Class: {}".format(class_names[y_batch[index]]))

    # Wyłączenie osi, aby nie były wyświetlane wokół obrazów
    plt.axis("off")

# Wyświetlenie całej figury z subplotami
plt.show()

"""**2.3.2 Budowa sieci**

Utwórz model bazowy przy pomocy odpowiedniej metody:
"""

base_model = tf.keras.applications.xception.Xception(weights="imagenet",include_top=False)

avg = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
output = tf.keras.layers.Dense(n_classes, activation="softmax")(avg)
model = tf.keras.Model(inputs=base_model.input, outputs=output)

import tensorflow as tf

# Zamrożenie wszystkich warstw w bazowym modelu
for layer in base_model.layers:
    layer.trainable = False

# Kompilacja modelu z określoną funkcją straty, optymalizatorem i metryką
model.compile(
    loss="sparse_categorical_crossentropy",  # Funkcja straty do klasyfikacji wieloklasowej z etykietami w postaci liczb całkowitych
    optimizer=tf.keras.optimizers.SGD(lr=0.2),  # Optymalizator Stochastic Gradient Descent z określoną szybkością uczenia (learning rate)
    metrics=["accuracy"]  # Metryka do oceny modelu podczas treningu i ewaluacji
)

# Trenowanie modelu na zbiorze treningowym przez 5 epok, z walidacją na zbiorze walidacyjnym
model.fit(
    train_set,  # Zbiór danych treningowych
    epochs=5,  # Liczba epok treningu
    validation_data=valid_set  # Zbiór danych walidacyjnych
)

# Ustawienie flagi trainable na True, aby wszystkie warstwy bazowego modelu były trenowalne
base_model.trainable = True

# Kompilacja modelu z nowymi ustawieniami optymalizatora i funkcji straty
model.compile(
    loss="sparse_categorical_crossentropy",  # Funkcja straty do klasyfikacji wieloklasowej z etykietami w postaci liczb całkowitych
    optimizer=tf.keras.optimizers.SGD(lr=0.01, momentum=0.9),  # Optymalizator Stochastic Gradient Descent z niższą szybkością uczenia i momentem
    metrics=["accuracy"]  # Metryka do oceny modelu podczas treningu i ewaluacji
)

# Trenowanie modelu na zbiorze treningowym przez 10 epok, z walidacją na zbiorze walidacyjnym
model.fit(
    train_set,  # Zbiór danych treningowych
    epochs=10,  # Liczba epok treningu
    validation_data=valid_set  # Zbiór danych walidacyjnych
)

# Zapisz model do pliku xception_flowers.keras.
eval_tuple = (model.evaluate(train_set), model.evaluate(valid_set), model.evaluate(test_set))
print(model.summary())

with open('xception_acc.pkl', 'wb') as f:
    pickle.dump(eval_tuple, f)

model.save("xception_flowers.keras")