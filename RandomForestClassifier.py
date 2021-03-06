import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import numpy as np
from sklearn.ensemble import  RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.grid_search import GridSearchCV
import ClassifierHelperFunctions as hf


def run_random_forest_classifier(sports=['Badminton', 'Basketball', 'Foosball', 'Running', 'Skating', 'Walking'],
                                 featuresFile='../Data/featuresFinal.csv',
                                 labelsFile='../Data/labelsFinal.csv',
                                 freqDims=150,
                                 timeDims=13,
                                 channels=6,
                                 num_pca_components=200,
                                 pca_whiten=True,
                                 algoSwitch=0):
    print '\nLoading data...'

    data = hf.load_data(featuresFile, labelsFile)

    train_features = data['train_features'].reshape((-1, freqDims * timeDims, channels))
    train_labels   = data['train_labels']
    test_features  = data['test_features'].reshape((-1, freqDims * timeDims, channels))
    test_labels    = data['test_labels']

    if algoSwitch > 1:
        newPerson_data = hf.load_data('../Data/newPersonFeaturesFinal.csv', '../Data/newPersonLabelsFinal.csv',
                                      newPerson=True)
        newPerson_test_features = newPerson_data['test_features'].reshape((-1, freqDims * timeDims, channels))
        newPerson_test_labels = newPerson_data['test_labels']

    print 'Data loaded!'
    print 'Training set:  ', train_features.shape
    print 'Test set:      ', test_features.shape
    if algoSwitch > 1:
        print 'New person test set:', newPerson_test_features.shape[0]

    random_forest=RandomForestClassifier()
    tuned_parameters = [{'classifier__min_samples_split' : [5,10],
                         'classifier__criterion' : ['gini','entropy'],
                         'classifier__n_estimators' : [15,25]}] #prepared the range of parameters to search over for GridSearchCV


    print '\nReducing dimensionality using PCA...'

    if num_pca_components > freqDims*timeDims:
        num_pca_components = freqDims*timeDims

    reduced_train_features = np.zeros((train_features.shape[0], num_pca_components, channels))
    reduced_test_features = np.zeros((test_features.shape[0], num_pca_components, channels))
    if algoSwitch > 1:
        reduced_newPerson_test_features = np.zeros((newPerson_test_features.shape[0], num_pca_components, channels))

    for c in range(channels):
        pca = PCA(n_components=num_pca_components, whiten=pca_whiten)
        reduced_train_features[:,:,c] = pca.fit_transform(train_features[:,:,c])
        reduced_test_features[:,:,c]  = pca.transform(test_features[:,:,c])
        if algoSwitch > 1:
            reduced_newPerson_test_features[:, :, c] = pca.transform(newPerson_test_features[:, :, c])

    print 'Dimensionality reduced!'
    print 'Old feature dimensions:', train_features.shape[1]*train_features.shape[2]
    print 'New feature dimensions:', reduced_train_features.shape[1]*reduced_train_features.shape[2]

    pipeline = Pipeline([("classifier", random_forest)])
    pipeline_grid = GridSearchCV(pipeline, tuned_parameters, cv = 5, n_jobs=-1)
    train_labels   = np.argmax(train_labels, 1)

    reduced_train_features=reduced_train_features.reshape((reduced_train_features.shape[0],-1))
    reduced_test_features=reduced_test_features.reshape((reduced_test_features.shape[0],-1))
    if algoSwitch > 1:
        reduced_newPerson_test_features = reduced_newPerson_test_features.reshape((reduced_newPerson_test_features.shape[0], -1))

    pipeline_grid.fit(reduced_train_features,train_labels)
    print pipeline_grid.best_params_
    predictions=pipeline_grid.predict(reduced_test_features)
    print predictions.shape

    if algoSwitch > 1:
        newPerson_predictions = pipeline_grid.predict(reduced_newPerson_test_features)
        print newPerson_predictions.shape


    print '\nTEST ERRORS (# of errors / # of test examples)'

    predicted_vs_truth_count_matrix = np.zeros([len(sports), len(sports)], dtype='int')
    for i in range(predictions.shape[0]):
        predicted_vs_truth_count_matrix[np.argmax(test_labels, 1)[i], predictions[i]] += 1

    for i in range(len(sports)):
        num_correctly_predicted = predicted_vs_truth_count_matrix[i,i]
        num_actually_were = np.sum(predicted_vs_truth_count_matrix[i, :])
        num_wrongly_predicted = num_actually_were - num_correctly_predicted
        print sports[i] + ':\t', num_wrongly_predicted, '/', num_actually_were, '\t', predicted_vs_truth_count_matrix[i,:]

    if algoSwitch > 1:
        print '\n\nTEST ERRORS FOR NEW PERSON (# of errors / # of test examples)'

        newPerson_predicted_vs_truth_count_matrix = np.zeros([len(sports), len(sports)], dtype='int')
        for i in range(newPerson_predictions.shape[0]):
            newPerson_predicted_vs_truth_count_matrix[np.argmax(newPerson_test_labels, 1)[i], newPerson_predictions[i]] += 1

        for i in range(len(sports)):
            num_correctly_predicted = newPerson_predicted_vs_truth_count_matrix[i, i]
            num_actually_were = np.sum(newPerson_predicted_vs_truth_count_matrix[i, :])
            num_wrongly_predicted = num_actually_were - num_correctly_predicted
            print sports[i] + ':\t', num_wrongly_predicted, '/', num_actually_were, '\t', newPerson_predicted_vs_truth_count_matrix[i, :]
