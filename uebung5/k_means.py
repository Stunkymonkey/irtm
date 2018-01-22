#!/usr/bin/env python3
from copy import deepcopy
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def dist(a, b, ax=1):
    """
    Euclidean Distance
    """
    return np.linalg.norm(a - b, axis=ax)


def k_means(file, k=3):
    plt.rcParams['figure.figsize'] = (120, 40)
    plt.style.use('ggplot')

    # Importing the dataset
    data = pd.read_csv(file)
    data.head()

    # Getting the values and plotting it
    f1 = data['V1'].values
    f2 = data['V2'].values
    X = np.array(list(zip(f1, f2)))
    plt.scatter(f1, f2, c='black', s=7)

    # X coordinates of random centroids
    C_x = np.random.rand(k, 1)[:, 0]
    # Y coordinates of random centroids
    C_y = np.random.rand(k, 1)[:, 0]
    C = np.array(list(zip(C_x, C_y)), dtype=np.float32)

    # Plotting along with the Centroids
    plt.scatter(f1, f2, c='#050505', s=7)
    plt.scatter(C_x, C_y, marker='*', s=200, c='g')

    # To store the value of centroids when it updates
    C_old = np.zeros(C.shape)
    # Cluster Lables(0, 1, 2)
    clusters = np.zeros(len(X))
    # Error func. - Distance between new centroids and old centroids
    error = dist(C, C_old, None)
    # Loop will run till the error becomes zero
    while error != 0:
        # Assigning each value to its closest cluster
        for i in range(len(X)):
            distances = dist(X[i], C)
            cluster = np.argmin(distances)
            clusters[i] = cluster
        # Storing the old centroid values
        C_old = deepcopy(C)
        # Finding the new centroids by taking the average value
        for i in range(k):
            points = [X[j] for j in range(len(X)) if clusters[j] == i]
            if len(points) == 0:
                continue
            C[i] = np.mean(points, axis=0)
        error = dist(C, C_old, None)

    colors = ['r', 'g', 'b', 'y', 'c', 'm']
    fig, ax = plt.subplots()
    for i in range(k):
        points = np.array([X[j] for j in range(len(X)) if clusters[j] == i])
        if len(points) == 0:
            print("no points found for centroid")
            continue
        ax.scatter(points[:, 0], points[:, 1], s=7, c=colors[i % 6])
        ax.scatter(C[i, 0], C[i, 1], marker='*', s=200, c='#050505')
    plt.savefig(str('result-' + str(k) + '.png'))


if __name__ == '__main__':
    k_means('data.csv', 2)
    k_means('data.csv', 20)
