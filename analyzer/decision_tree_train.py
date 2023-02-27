# Load libraries
import pandas as pd
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.metrics import precision_score

from sklearn.tree import export_graphviz
from six import StringIO
from IPython.display import Image
import pydotplus
from sklearn.datasets import load_breast_cancer
import numpy as np
from features import col_names, reduced_col_names, merged_content
from sklearn import tree
from sklearn.tree import _tree
import sys
import matplotlib.pyplot as plt
from multiprocessing import Pool
from functools import partial
import random

select_consist_only = None

def get_consist(proc):
    cnt = proc[0]
    target  = proc[1]
    index_1 = proc[2]
    row_inconsist = proc[3]

    min_dist = 9999999999
    min_dist_instance = None
    min_index_2 = None

    for index_2, row_consist in select_consist_only.iterrows():
        distance = levenshtein(row_inconsist, row_consist)
        if min_dist > distance:
            min_dist = distance
            min_dist_instance = row_consist
            min_index_2 = index_2

            if distance == 1:
                break

    #print ("Done  distance: %s, cnt: %s, target: %s" % (distance, cnt, target))
    return (min_index_2, min_dist_instance)


def levenshtein(a, b):
    "Calculates the Levenshtein distance between a and b."

    a = a.values.tolist()[:-1]
    b = b.values.tolist()[:-1]

   # n, m = len(a), len(b)
   # if n > m:
   #     # Make sure n <= m, to use O(min(n,m)) space
   #     a,b = b,a
   #     n,m = m,n

   # current = range(n+1)
   # for i in range(1,m+1):
   #     previous, current = current, [i]+[0]*n
   #     for j in range(1,n+1):
   #         add, delete = previous[j]+1, current[j-1]+1
   #         change = previous[j-1]
   #         if a[j-1] != b[i-1]:
   #             change = change + 1
   #         current[j] = min(add, delete, change)

    distance = 0
    for i in range(len(a)):
        if not a[i] == b[i]:
            distance += 1

    return distance



def find_path(clf, X, y, E):

    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    feature = clf.tree_.feature
    threshold = clf.tree_.threshold

    # First let's retrieve the decision path of each sample. The decision_path
    # method allows to retrieve the node indicator functions. A non zero element of
    # indicator matrix at the position (i, j) indicates that the sample i goes
    # through the node j.

    node_indicator = clf.decision_path(X)

    # Similarly, we can also have the leaves ids reached by each sample.

    leave_id = clf.apply(X)

    # Now, it's possible to get the tests that were used to predict a sample or
    # a group of samples. First, let's make it for the sample.
    set_leaf_node = set(leave_id)

    with open(sys.argv[2]) as f:
        log = f.read()

    hihi = log.split("\n\n")

    index_list = list(X.index.values)

    for n in set_leaf_node:
        indices = [i for i, x in enumerate(leave_id) if x == n]
        aa = []
        for i in indices:
            aa.append(index_list[i])
        indices = aa

        inconsist_exist = False
        cnt_inconsist = 0
        cnt_consist = 0
        for i in indices:
            if y[i] == 1:
                cnt_inconsist += 1
                inconsist_exist = True
            else:
                cnt_consist += 1


        if cnt_inconsist > cnt_consist:
            print ("inconsist leaf!")

        a = ""
        if inconsist_exist:
            sample_id = -1
            lowest_id = 9999999999
            lowest_test_case_id = 9999999999
            for j in indices:
                if y[j] == 1:
                    if lowest_test_case_id >= int(hihi[j].split("[*] test case #")[1].split(" ")[0]):
                        lowest_id = j
                        lowest_test_case_id = int(hihi[j].split("[*] test case #")[1].split(" ")[0])
            sample_id = lowest_id


            if sample_id == -1:
                sys.exit()

            a += str(n)
            a += ","
            a += str(lowest_test_case_id)
            a += ","
            a += ","
            a += hihi[sample_id].split("[*] testing CSP: ")[1].split("\n")[0]
            a += "\n"
            a += hihi[sample_id].split("[*] test case ")[1].split("\n")[0]
            print (a)


            test_id = sample_id
            sample_id = index_list.index(sample_id)

            node_index = node_indicator.indices[node_indicator.indptr[sample_id]:
                                                node_indicator.indptr[sample_id + 1]]

            print('Rules used to predict sample %s: ' % test_id)

            nono_id = sample_id
            sample_id = index_list[sample_id]
            for node_id in node_index:

                if leave_id[nono_id] == node_id:  # <-- changed != to ==
                    #continue # <-- comment out
                    print("leaf node {} reached, no decision here".format(leave_id[nono_id])) # <--
                    pass

                else: # < -- added else to iterate through decision nodes
                    if (X.loc[sample_id].values.tolist()[feature[node_id]] <= threshold[node_id]):
                        threshold_sign = "<="
                    else:
                        threshold_sign = ">"

                    print("decision id node %s : (%s (= %s) %s %s)"
                          % (node_id,
                             feature_cols[feature[node_id]],
                             X.loc[sample_id].values.tolist()[feature[node_id]], # <-- changed i to sample_id
                             threshold_sign,
                             threshold[node_id]))
            print ()


def get_page(test_page_id):
    if test_page_id >= 100000000:
        test_page_id = test_page_id % 100000000
        with open("status_100.html", 'r') as f:
            for number, line in enumerate(f):
                if number+1 == test_page_id:
                    return line.strip()
        return 0

    else:
        with open("full_test_list.html", 'r') as f:
            for number, line in enumerate(f):
                if number == test_page_id:
                    return line.strip()
        return 0

def perf_measure(y_actual, y_hat):
    TP = 0
    FP = 0
    TN = 0
    FN = 0

    index_list = list(y_actual.index.values)

    for i in range(len(y_hat)):
        j = index_list[i]
        if y_actual[j]==y_hat[i]==1:
           TP += 1
        if y_hat[i]==1 and y_actual[j]!=y_hat[i]:
           FP += 1
        if y_actual[j]==y_hat[i]==0:
           TN += 1
        if y_hat[i]==0 and y_actual[j]!=y_hat[i]:
           FN += 1

    return(TP, FP, TN, FN)

def get_fn(y_actual, y_hat, X):
    TP = 0
    FP = 0
    TN = 0
    FN = 0

    for i in range(len(y_hat)):
        if y_actual[i]==y_hat[i]==1:
           TP += 1
        if y_hat[i]==1 and y_actual[i]!=y_hat[i]:
           FP += 1
        if y_actual[i]==y_hat[i]==0:
           TN += 1
        if y_hat[i]==0 and y_actual[i]!=y_hat[i]:
           FN += 1

    return(TP, FP, TN, FN)
def htmlspecialchars(text):
    return (
        text.replace("&", "&amp;").
        replace('"', "&quot;").
        replace("<", "&lt;").
        replace(">", "&gt;")
    )

def feature_reduction(X):
    data = {}
    reduced_X = pd.DataFrame(data)
    for feature in reduced_col_names:
        if "[" == feature[0]:
            print (feature)
            original_col_names = [htmlspecialchars(w) for w in merged_content[feature]]
            reduced_X[feature] = [0] * len(X)
            for original_feature in original_col_names:
                reduced_X[feature] = reduced_X[feature] | X[original_feature]
        elif feature == "JS_EXECUTION_METHOD":
            reduced_X[feature] = [0] * len(X)
            for i in (range(len(X))):
                if X["url-allowed"][i] == 1:
                    reduced_X[feature][i] = 1
                elif X["url-self"][i] == 1:
                    reduced_X[feature][i] = 2
                elif X["url-blocked"][i] == 1:
                    reduced_X[feature][i] = 3
                elif X["inline-script"][i] == 1:
                    reduced_X[feature][i] = 4
        elif feature == "Chrome":
            continue
        elif feature == "Firefox":
            continue
        elif feature == "Safari":
            continue
        else:
            reduced_X[feature] = X[feature]


    return reduced_X

col_names = [htmlspecialchars(w) for w in col_names]

#col_names = [w.replace('[', '{') for w in col_names]
#col_names = [w.replace(']', '}') for w in col_names]

# load dataset
pima = pd.read_csv(sys.argv[1], header=None, names=col_names)
print (pima['label'].value_counts())
print (pima.head())


#split dataset in features and target variable
feature_cols = col_names[:-1]
X = pima[feature_cols] # Features

print (X)
X = feature_reduction(X)
y = pima.label # Target variable


X = X.replace(0, np.nan)
X  = X.dropna(how='all', axis=1)
X = X.replace(np.nan, 0)

feature_cols = list(X.columns)

#==========================sampling => edit distance================

print(X.shape)
print(y.shape)
Z = pd.concat([X, y], axis=1)
E = pd.concat([X, y], axis=1)


if Z['label'].value_counts()[1] < Z['label'].value_counts()[0]:

    select_inconsist_only  = Z.loc[Z['label'] == 1]
    select_consist_only  = Z.loc[Z['label'] == 0]

    sampled_data = Z.loc[Z['label'] == 1]

    print(Z.shape)
    print(select_inconsist_only.shape)
    print(select_consist_only.shape)

    target_size = select_inconsist_only.shape[0]
    consist_size = select_consist_only.shape[0]

    r_size = consist_size - target_size

    r_mask = [True] * Z.shape[0]

    for i in random.sample(range(consist_size), r_size):
        r_index = select_consist_only.index[i]
        r_mask[r_index] = False

    Zp = Z[r_mask]

    assert(Zp.shape[0] == 2 * target_size)

    s1  = Zp.loc[Zp['label'] == 1]
    s2  = Zp.loc[Zp['label'] == 0]
    assert(s1.shape == s2.shape)
    Z = Zp

#Z.to_pickle(sys.argv[4])
#==========================-====================================

print(X)
print(y)
print("="*30)

X = Z.drop(labels='label', axis=1)
y = Z.take([-1], 1).iloc[:,0]

print(X)
print(y)
# Split dataset into training set and test set

feature_cols = X.columns.values


for ii in [10]:
    print ("[*] result! with depth %s" % ii)
    score_accuracy = []
    score_precision = []
    score_recall = []

    #for depth in range(1,35):
    #    model = DecisionTreeClassifier(criterion='gini', max_depth=depth)
    #    model.fit(X, y)
    #
    #    y_pred = model.predict(X)
    #
    #    accuracy = metrics.accuracy_score(y, y_pred)
    #    precision = metrics.precision_score(y, y_pred)
    #    recall = metrics.recall_score(y, y_pred)
    #    print ("accuracy:", accuracy)
    #    print ("precision:", precision)
    #    print ("recall:", recall)
    #
    #    score_accuracy.append(accuracy)
    #    score_precision.append(precision)
    #    score_recall.append(recall)
    #
    #
    #print ("accuracy:", score_accuracy)
    #print ("precision:", score_precision)
    #print ("recall:", score_recall)
    #
    #plt.plot(range(1,35), score_accuracy, 'ro--')
    #plt.plot(range(1,35), score_precision, 'bv--')
    #plt.plot(range(1,35), score_recall, 'y^--')
    #
    #plt.legend(['accuracy', "precision", "recall"])
    #plt.xlabel('max_depth')
    #
    #plt.savefig('/var/www/html/recall.png',
    #            facecolor='#eeeeee',
    #            edgecolor='black',
    #            format='png', dpi=140)
    #sys.exit()

    # Create Decision Tree classifer object
    clf = DecisionTreeClassifier(criterion='entropy', max_depth=ii)

    # Train Decision Tree Classifer
    clf = clf.fit(X,y)



    #Predict the response for test dataset
    y_pred = clf.predict(X)

    #find_path(clf, X, y, E)


    accuracy = metrics.accuracy_score(y, y_pred)
    precision = metrics.precision_score(y, y_pred)
    recall = metrics.recall_score(y, y_pred)


    print ("accuracy:", accuracy)
    print ("precision:", precision)
    print ("recall:", recall)

    print (perf_measure(y, y_pred))

    #print (get_fn(y, y_pred, X))
    #
    #
#    dot_data = StringIO()
#    export_graphviz(clf, out_file=dot_data,
#                    filled=True, rounded=True,
#                    special_characters=True,feature_names = feature_cols,class_names=['0','1'])
#    graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
#    graph.write_pdf("tree_pdf_%s.pdf" % ii)
