from keras.optimizers import SGD
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.utils.np_utils import to_categorical
from keras import metrics
import numpy as np
from tqdm import tqdm
from glob import glob

import string as base_string

input_width = 10  # longest name to use
num_classes = 3
letters = base_string.ascii_lowercase

# load the data

boys_names_set = set()
girls_names_set = set()

files = glob('./data/bignames/*.data')
print('Loading Data into Memory')
for filename in tqdm(files):
    with open(filename, 'r') as f:
        rows = [x.strip().split(',') for x in f.readlines() if x.strip().split(',')]
        for row in rows:
            gender, name = row[1], row[3].lower()
            if len(name) > input_width or any(c not in letters for c in name):
                continue
            if gender == 'F':
                girls_names_set.add(name)
            if gender == 'M':
                boys_names_set.add(name)
print('Imported Data')

with open('./data/boys_names_large.txt', 'w+') as f:
    for name in boys_names_set:
        print(name, file=f)

with open('./data/girls_names_large.txt', 'w+') as f:
    for name in girls_names_set:
        print(name, file=f)

all_names_set = boys_names_set | girls_names_set

# encode the strings as pictures


def encode_string_as_array(string):
    arr = np.zeros(shape=(input_width * len(letters)))

    for pos, char in enumerate(string):
        arr[pos * input_width + letters.index(char)] = 1.

    return arr


# classify the names as an int, we need to use cargorical transformations to one hot encode these
def classify_name(name):
    boy, girl, both = 0, 1, 2
    # O(1) inclusion tests FTW
    if name in boys_names_set and name in girls_names_set:
        return both
    if name in boys_names_set:
        return boy
    if name in girls_names_set:
        return girl


total_data = np.array([encode_string_as_array(name) for name in sorted(all_names_set)])
data_labels_ints = np.array([classify_name(name) for name in sorted(all_names_set)])
data_labels = to_categorical(data_labels_ints, num_classes)

regular_names = np.array([name for name in sorted(all_names_set)])

# randomize the data

perm = np.random.permutation(len(total_data))

total_data = total_data[perm]
data_labels = data_labels[perm]
regular_names = regular_names[perm]

# partition the data into training, and testing
partition = int(len(total_data) * .9)  # 90% training, 10% testing

X, testing_data = total_data[:partition], total_data[partition:]
Y, testing_labels = data_labels[:partition], data_labels[partition:]
reg_names_training, reg_names_testing = regular_names[:partition], regular_names[partition:]

# Build a model

input_data_total_width = input_width * len(letters)

model = Sequential()
# Input Layer
model.add(Dense(input_data_total_width, input_dim=input_data_total_width, kernel_initializer='normal', activation='relu'))
# Hidden Layers
model.add(Dense(512, activation='relu', kernel_initializer='normal',))
model.add(Dropout(.3))
model.add(Dense(1024, activation='relu', kernel_initializer='normal'))
model.add(Dropout(.3))
model.add(Dense(512, activation='relu', kernel_initializer='normal'))
# Ouput layer
model.add(Dense(num_classes, kernel_initializer='normal', activation='softmax'))

model.summary()

sgd = SGD(lr=0.01)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=[metrics.categorical_accuracy])

model.fit(X, Y, epochs=150, batch_size=128, verbose=True, validation_data=(testing_data, testing_labels))

scores = model.evaluate(X, Y)
print("Accuracy on Testing Data: \n\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))

# see how we did
predictions = np.argmax(model.predict(testing_data), 1)

# visualize


class colors:
    ok = '\033[92m'
    fail = '\033[91m'
    close = '\033[0m'

num_correct = 0
correct_per_class = [0] * num_classes
totals = [0] * num_classes
proto = '|' + '{:^12}|' * 4
for i in range(len(testing_data)):
    if i % 10 == 0:
        print(proto.format('Name', 'Guess', 'Correct', 'Match?'))
    name = reg_names_testing[i]
    guess = ['boy', 'girl', 'both'][predictions[i]]
    answer = ['boy', 'girl', 'both'][classify_name(name)]
    match = guess == answer
    col = colors.ok if match else colors.fail
    string = col + proto.format(name, guess, answer, match) + colors.close
    print(string)

    num_correct += match
    correct_per_class[classify_name(name)] += match
    totals[classify_name(name)] += 1

print()
per_correct = round(num_correct / len(testing_data), 2) * 100
print("Correct on {} of {} ({}%)".format(num_correct, len(testing_data), per_correct))

print('correct both:', round(correct_per_class[0]/totals[0], 2))
print('correct girls:', round(correct_per_class[1]/totals[1], 2))
print('correct boy:', round(correct_per_class[2]/totals[2], 2))
